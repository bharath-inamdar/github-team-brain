import logging

from sqlalchemy.orm import Session

from app.models import PullRequest, PullRequestReview, PullRequestReviewComment
from app.services.ai_service import AIService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

MAX_SUMMARY_CONTEXT_CHARS = 40000
MAX_ASK_CONTEXT_CHARS = 12000


class IngestionService:
    """
    Handles indexing GitHub data into ChromaDB.
    """

    def __init__(self):
        self.ai_service = AIService()
        self.vector_service = VectorService()

    def _is_useful_review(self, review_text: str) -> bool:
        """
        Returns True if the review contains meaningful engineering feedback.
        """

        if not review_text:
            return False

        review_text = review_text.strip()

        # Ignore very short reviews
        if len(review_text) < 20:
            return False

        lower = review_text.lower()

        ignored_phrases = [
            "codex review",
            "about codex",
            "your team has set up codex",
            "comment \"@codex review\"",
            "comment '@codex review'",
            "triggered when",
            "dependabot",
            "github actions",
            "reviewed commit",
            "<details>",
            "</details>",
            "lgtm",
            "looks good",
            "approved",
        ]

        return not any(
            phrase in lower
            for phrase in ignored_phrases
        )

    def _review_document_id(self, review: PullRequestReview) -> str:
        return f"review:{review.github_review_id}"

    def _review_comment_document_id(
        self,
        comment: PullRequestReviewComment,
    ) -> str:
        return f"review-comment:{comment.github_comment_id}"

    def _clean_metadata(self, metadata: dict) -> dict:
        """
        Chroma metadata values cannot be null, so store empty strings instead.
        """

        return {
            key: "" if value is None else value
            for key, value in metadata.items()
        }

    def _format_comment_text(
        self,
        comment: PullRequestReviewComment,
    ) -> str:
        location_parts = []

        if comment.path:
            location_parts.append(comment.path)

        if comment.line is not None:
            location_parts.append(f"line {comment.line}")

        location = " at ".join(location_parts)
        prefix = f"{location}\n" if location else ""

        return f"{prefix}{comment.body.strip()}"

    def _source_citations(self, search_results: dict) -> list[dict]:
        documents = search_results.get("documents", [[]])[0] or []
        metadatas = search_results.get("metadatas", [[]])[0] or []

        citations = []

        for index, document in enumerate(documents, start=1):
            metadata = metadatas[index - 1] if index - 1 < len(metadatas) else {}

            citations.append(
                {
                    "citation_id": index,
                    "text": document,
                    "source_type": metadata.get("source_type", "review"),
                    "reviewer": metadata.get("reviewer") or None,
                    "state": metadata.get("state") or None,
                    "path": metadata.get("path") or None,
                    "line": metadata.get("line") or None,
                    "pull_request_id": metadata.get("pull_request_id") or None,
                    "repository_id": metadata.get("repository_id") or None,
                }
            )

        return citations

    def _context_from_sources(self, sources: list[dict]) -> str:
        context_blocks = []
        context_characters = 0

        for source in sources:
            block = f"[{source['citation_id']}] {source['text']}"

            if context_characters + len(block) > MAX_ASK_CONTEXT_CHARS:
                break

            context_blocks.append(block)
            context_characters += len(block)

        return "\n\n".join(context_blocks)

    def index_first_review(self, db: Session):
        """
        Indexes the first review from PostgreSQL into ChromaDB.
        """

        review = (
            db.query(PullRequestReview)
            .filter(PullRequestReview.body.isnot(None))
            .filter(PullRequestReview.body != "")
            .first()
        )

        if review is None:
            return "No reviews with text found."

        embedding = self.ai_service.generate_embedding(
            review.body
        )

        self.vector_service.add_document(
            document_id=self._review_document_id(review),
            document_text=review.body,
            embedding=embedding,
            metadata=self._clean_metadata({
                "repository_id": review.pull_request.repository_id,
                "reviewer": review.reviewer or "",
                "state": review.state or "",
                "source_type": "review",
                "review_id": review.github_review_id,
                "pull_request_id": review.pull_request_id,
            }),
        )

        return f"Indexed review {review.github_review_id}"

    def index_all_reviews(self, db: Session):
        """
        Index every useful pull request review and inline review comment into ChromaDB.
        """

        reviews = db.query(PullRequestReview).all()
        review_comments = db.query(PullRequestReviewComment).all()

        indexed = 0
        indexed_reviews = 0
        indexed_review_comments = 0
        skipped_empty = 0
        skipped_existing = 0
        skipped_bot = 0
        skipped_short = 0

        for review in reviews:

            if not review.body or review.body.strip() == "":
                skipped_empty += 1
                continue

            review_text = review.body.strip()

            if len(review_text) < 20:
                skipped_short += 1
                continue

            if not self._is_useful_review(review_text):
                skipped_bot += 1
                continue

            document_id = self._review_document_id(review)

            if self.vector_service.document_exists(document_id):
                skipped_existing += 1
                continue

            embedding = self.ai_service.generate_embedding(
                review_text
            )

            self.vector_service.add_document(
                document_id=document_id,
                document_text=review_text,
                embedding=embedding,
                metadata=self._clean_metadata({
                    "repository_id": review.pull_request.repository_id,
                    "reviewer": review.reviewer,
                    "state": review.state,
                    "source_type": "review",
                    "review_id": review.github_review_id,
                    "pull_request_id": review.pull_request_id,
                }),
            )

            indexed += 1
            indexed_reviews += 1

        for comment in review_comments:

            if not comment.body or comment.body.strip() == "":
                skipped_empty += 1
                continue

            comment_text = comment.body.strip()

            if len(comment_text) < 20:
                skipped_short += 1
                continue

            if not self._is_useful_review(comment_text):
                skipped_bot += 1
                continue

            document_id = self._review_comment_document_id(comment)

            if self.vector_service.document_exists(document_id):
                skipped_existing += 1
                continue

            document_text = self._format_comment_text(comment)
            embedding = self.ai_service.generate_embedding(document_text)

            self.vector_service.add_document(
                document_id=document_id,
                document_text=document_text,
                embedding=embedding,
                metadata=self._clean_metadata({
                    "repository_id": comment.pull_request.repository_id,
                    "reviewer": comment.reviewer,
                    "source_type": "review_comment",
                    "comment_id": comment.github_comment_id,
                    "pull_request_id": comment.pull_request_id,
                    "path": comment.path,
                    "line": comment.line,
                }),
            )

            indexed += 1
            indexed_review_comments += 1

        return {
            "total_reviews": len(reviews),
            "total_review_comments": len(review_comments),
            "indexed": indexed,
            "indexed_reviews": indexed_reviews,
            "indexed_review_comments": indexed_review_comments,
            "skipped_empty": skipped_empty,
            "skipped_short": skipped_short,
            "skipped_bot": skipped_bot,
            "skipped_existing": skipped_existing,
        }

    def search_reviews(
        self,
        question: str,
        repository_id: int | None = None,
    ):
        """
        Searches indexed reviews using semantic similarity.
        """

        embedding = self.ai_service.generate_embedding(
            question
        )

        return self.vector_service.search_reviews(
            embedding,
            repository_id=repository_id,
        )

    def ask_repository(
        self,
        question: str,
        repository_id: int | None = None,
        db: Session | None = None,
    ):
        """
        Answers a question about the repository
        using semantic search.
        """

        search_results = self.search_reviews(
            question,
            repository_id=repository_id,
        )

        sources = self._source_citations(search_results)

        if not sources and db is not None:
            logger.info(
                "No vector search results found; indexing database review material",
                extra={"repository_id": repository_id},
            )
            self.index_all_reviews(db)
            search_results = self.search_reviews(
                question,
                repository_id=repository_id,
            )
            sources = self._source_citations(search_results)

        context = self._context_from_sources(sources)

        answer = self.ai_service.answer_question(
            question=question,
            context=context,
        )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    def summarize_repository(
        self,
        db: Session,
        repository_id: int | None = None,
    ):
        """
        Generates a repository engineering summary using only useful review comments.
        """

        comments_query = (
            db.query(PullRequestReviewComment)
            .join(PullRequestReviewComment.pull_request)
            .filter(PullRequestReviewComment.body.isnot(None))
            .filter(PullRequestReviewComment.body != "")
        )

        if repository_id is not None:
            comments_query = comments_query.filter(
                PullRequest.repository_id == repository_id
            )

        comments = comments_query.all()

        comment_texts = []
        included_comments = 0
        skipped_comments = 0
        context_characters = 0

        for comment in comments:

            if not comment.body:
                continue

            comment_text = comment.body.strip()

            if not self._is_useful_review(comment_text):
                skipped_comments += 1
                continue

            comment_length = len(comment_text)

            if comment_texts:
                comment_length += 2

            if context_characters + comment_length > MAX_SUMMARY_CONTEXT_CHARS:
                skipped_comments += 1
                break

            comment_texts.append(comment_text)
            included_comments += 1
            context_characters += comment_length

        context = "\n\n".join(comment_texts)

        logger.info(
            "Prepared repository summary context",
            extra={
                "total_comments_considered": len(comments),
                "included_comments": included_comments,
                "skipped_comments": skipped_comments,
                "context_characters": context_characters,
            },
        )

        if not context.strip():
            return {
                "total_reviews": 0,
                "summary": "No meaningful review comments were found.",
            }

        summary = self.ai_service.summarize_repository(
            context=context,
        )

        return {
            "total_reviews": len(comment_texts),
            "summary": summary,
        }
