import logging

from sqlalchemy.orm import Session

from app.models import (
    PullRequest,
    PullRequestReview,
    PullRequestReviewComment,
)
from app.services.ai_service import AIService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

MAX_SUMMARY_CONTEXT_CHARS = 60000
MAX_ASK_CONTEXT_CHARS = 12000


class IngestionService:
    """
    Handles indexing GitHub data into ChromaDB and retrieving
    relevant engineering knowledge for TeamBrain.
    """

    def __init__(self):
        self.ai_service = AIService()
        self.vector_service = VectorService()

    def _is_useful_review(
        self,
        review_text: str,
    ) -> bool:
        """
        Returns True if the review contains meaningful
        engineering feedback.
        """

        if not review_text:
            return False

        review_text = review_text.strip()

        if len(review_text) < 20:
            return False

        lower = review_text.lower()

        ignored_phrases = [
            "codex review",
            "about codex",
            "your team has set up codex",
            'comment "@codex review"',
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

    def _review_document_id(
        self,
        review: PullRequestReview,
    ) -> str:
        return f"review:{review.github_review_id}"

    def _review_comment_document_id(
        self,
        comment: PullRequestReviewComment,
    ) -> str:
        return f"review-comment:{comment.github_comment_id}"

    def _clean_metadata(
        self,
        metadata: dict,
    ) -> dict:
        """
        Chroma metadata values cannot be null,
        so store empty strings instead.
        """

        return {
            key: "" if value is None else value
            for key, value in metadata.items()
        }

    def _format_comment_text(
        self,
        comment: PullRequestReviewComment,
    ) -> str:
        """
        Adds file and line information to inline review comments.
        """

        location_parts = []

        if comment.path:
            location_parts.append(comment.path)

        if comment.line is not None:
            location_parts.append(
                f"line {comment.line}"
            )

        location = " at ".join(
            location_parts
        )

        prefix = (
            f"{location}\n"
            if location
            else ""
        )

        return (
            f"{prefix}"
            f"{comment.body.strip()}"
        )

    def _source_citations(
        self,
        search_results: dict,
    ) -> list[dict]:
        """
        Converts Chroma search results into structured
        source citations.
        """

        documents = (
            search_results.get(
                "documents",
                [[]],
            )[0]
            or []
        )

        metadatas = (
            search_results.get(
                "metadatas",
                [[]],
            )[0]
            or []
        )

        citations = []

        for index, document in enumerate(
            documents,
            start=1,
        ):
            metadata = (
                metadatas[index - 1]
                if index - 1 < len(metadatas)
                else {}
            )

            citations.append(
                {
                    "citation_id": index,
                    "text": document,
                    "source_type": metadata.get(
                        "source_type",
                        "review",
                    ),
                    "reviewer": metadata.get(
                        "reviewer"
                    ) or None,
                    "state": metadata.get(
                        "state"
                    ) or None,
                    "path": metadata.get(
                        "path"
                    ) or None,
                    "line": metadata.get(
                        "line"
                    ) or None,
                    "pull_request_id": metadata.get(
                        "pull_request_id"
                    ) or None,
                    "repository_id": metadata.get(
                        "repository_id"
                    ) or None,
                }
            )

        return citations

    def _context_from_sources(
        self,
        sources: list[dict],
    ) -> str:
        """
        Converts retrieved sources into clearly numbered
        evidence for the LLM.
        """

        context_blocks = []
        context_characters = 0

        for source in sources:

            citation_id = source["citation_id"]

            source_type = (
                source.get(
                    "source_type"
                )
                or "review"
            )

            path = source.get("path")
            line = source.get("line")
            reviewer = source.get("reviewer")

            header_parts = [
                f"[{citation_id}]",
                source_type.replace(
                    "_",
                    " ",
                ).title(),
            ]

            if path:
                header_parts.append(
                    f"File: {path}"
                )

            if line is not None:
                header_parts.append(
                    f"Line: {line}"
                )

            if reviewer:
                header_parts.append(
                    f"Reviewer: {reviewer}"
                )

            header = "\n".join(
                header_parts
            )

            block = (
                f"{header}\n"
                f"Review comment:\n"
                f"{source['text']}"
            )

            if (
                context_characters
                + len(block)
                > MAX_ASK_CONTEXT_CHARS
            ):
                break

            context_blocks.append(
                block
            )

            context_characters += len(
                block
            )

        return "\n\n".join(
            context_blocks
        )

    def _summary_evidence_block(
        self,
        source_id: int,
        source_type: str,
        text: str,
        path: str | None = None,
        line: int | None = None,
        reviewer: str | None = None,
    ) -> str:
        """
        Formats one piece of repository evidence for the
        summary LLM.

        Every source receives a stable citation number.
        """

        header_parts = [
            f"[{source_id}]",
            source_type.replace(
                "_",
                " ",
            ).title(),
        ]

        if path:
            header_parts.append(
                f"File: {path}"
            )

        if line is not None:
            header_parts.append(
                f"Line: {line}"
            )

        if reviewer:
            header_parts.append(
                f"Reviewer: {reviewer}"
            )

        header = "\n".join(
            header_parts
        )

        return (
            f"{header}\n"
            f"Review comment:\n"
            f"{text}"
        )

    def index_first_review(
        self,
        db: Session,
    ):
        """
        Indexes the first review from PostgreSQL into ChromaDB.
        """

        review = (
            db.query(PullRequestReview)
            .filter(
                PullRequestReview.body.isnot(None)
            )
            .filter(
                PullRequestReview.body != ""
            )
            .first()
        )

        if review is None:
            return "No reviews with text found."

        embedding = (
            self.ai_service.generate_embedding(
                review.body
            )
        )

        self.vector_service.add_document(
            document_id=self._review_document_id(
                review
            ),
            document_text=review.body,
            embedding=embedding,
            metadata=self._clean_metadata(
                {
                    "repository_id": (
                        review.pull_request.repository_id
                    ),
                    "reviewer": (
                        review.reviewer
                        or ""
                    ),
                    "state": (
                        review.state
                        or ""
                    ),
                    "source_type": "review",
                    "review_id": (
                        review.github_review_id
                    ),
                    "pull_request_id": (
                        review.pull_request_id
                    ),
                }
            ),
        )

        return (
            f"Indexed review "
            f"{review.github_review_id}"
        )

    def index_all_reviews(
        self,
        db: Session,
    ):
        """
        Index every useful pull request review and
        inline review comment into ChromaDB.
        """

        reviews = (
            db.query(
                PullRequestReview
            ).all()
        )

        review_comments = (
            db.query(
                PullRequestReviewComment
            ).all()
        )

        indexed = 0
        indexed_reviews = 0
        indexed_review_comments = 0

        skipped_empty = 0
        skipped_existing = 0
        skipped_bot = 0
        skipped_short = 0

        # ---------------------------------------------------------
        # Index pull request reviews
        # ---------------------------------------------------------

        for review in reviews:

            if (
                not review.body
                or review.body.strip() == ""
            ):
                skipped_empty += 1
                continue

            review_text = (
                review.body.strip()
            )

            if len(review_text) < 20:
                skipped_short += 1
                continue

            if not self._is_useful_review(
                review_text
            ):
                skipped_bot += 1
                continue

            document_id = (
                self._review_document_id(
                    review
                )
            )

            if self.vector_service.document_exists(
                document_id
            ):
                skipped_existing += 1
                continue

            embedding = (
                self.ai_service.generate_embedding(
                    review_text
                )
            )

            self.vector_service.add_document(
                document_id=document_id,
                document_text=review_text,
                embedding=embedding,
                metadata=self._clean_metadata(
                    {
                        "repository_id": (
                            review.pull_request.repository_id
                        ),
                        "reviewer": (
                            review.reviewer
                        ),
                        "state": review.state,
                        "source_type": "review",
                        "review_id": (
                            review.github_review_id
                        ),
                        "pull_request_id": (
                            review.pull_request_id
                        ),
                    }
                ),
            )

            indexed += 1
            indexed_reviews += 1

        # ---------------------------------------------------------
        # Index inline review comments
        # ---------------------------------------------------------

        for comment in review_comments:

            if (
                not comment.body
                or comment.body.strip() == ""
            ):
                skipped_empty += 1
                continue

            comment_text = (
                comment.body.strip()
            )

            if len(comment_text) < 20:
                skipped_short += 1
                continue

            if not self._is_useful_review(
                comment_text
            ):
                skipped_bot += 1
                continue

            document_id = (
                self._review_comment_document_id(
                    comment
                )
            )

            if self.vector_service.document_exists(
                document_id
            ):
                skipped_existing += 1
                continue

            document_text = (
                self._format_comment_text(
                    comment
                )
            )

            embedding = (
                self.ai_service.generate_embedding(
                    document_text
                )
            )

            self.vector_service.add_document(
                document_id=document_id,
                document_text=document_text,
                embedding=embedding,
                metadata=self._clean_metadata(
                    {
                        "repository_id": (
                            comment.pull_request.repository_id
                        ),
                        "reviewer": (
                            comment.reviewer
                        ),
                        "source_type": (
                            "review_comment"
                        ),
                        "comment_id": (
                            comment.github_comment_id
                        ),
                        "pull_request_id": (
                            comment.pull_request_id
                        ),
                        "path": comment.path,
                        "line": comment.line,
                    }
                ),
            )

            indexed += 1
            indexed_review_comments += 1

        return {
            "total_reviews": len(
                reviews
            ),
            "total_review_comments": len(
                review_comments
            ),
            "indexed": indexed,
            "indexed_reviews": (
                indexed_reviews
            ),
            "indexed_review_comments": (
                indexed_review_comments
            ),
            "skipped_empty": (
                skipped_empty
            ),
            "skipped_short": (
                skipped_short
            ),
            "skipped_bot": (
                skipped_bot
            ),
            "skipped_existing": (
                skipped_existing
            ),
        }

    def search_reviews(
        self,
        question: str,
        repository_id: int | None = None,
    ):
        """
        Searches indexed reviews using semantic similarity.
        """

        embedding = (
            self.ai_service.generate_embedding(
                question
            )
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
        Answers a repository question using semantic search.

        Retrieved review evidence is converted into numbered
        sources before being sent to Gemini.
        """

        search_results = (
            self.search_reviews(
                question,
                repository_id=repository_id,
            )
        )

        sources = (
            self._source_citations(
                search_results
            )
        )

        # If Chroma has no results, populate it from PostgreSQL.
        if not sources and db is not None:

            logger.info(
                "No vector search results found; "
                "indexing database review material",
                extra={
                    "repository_id": (
                        repository_id
                    ),
                },
            )

            self.index_all_reviews(db)

            search_results = (
                self.search_reviews(
                    question,
                    repository_id=repository_id,
                )
            )

            sources = (
                self._source_citations(
                    search_results
                )
            )

        # Never ask Gemini to answer from an empty context.
        if not sources:

            return {
                "question": question,
                "answer": (
                    "The repository does not contain "
                    "enough information."
                ),
                "sources": [],
            }

        context = (
            self._context_from_sources(
                sources
            )
        )

        logger.info(
            "Answering repository question",
            extra={
                "repository_id": (
                    repository_id
                ),
                "source_count": len(
                    sources
                ),
                "context_characters": len(
                    context
                ),
            },
        )

        answer = (
            self.ai_service.answer_question(
                question=question,
                context=context,
            )
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
        Generates a detailed repository engineering summary.

        The summary uses both:
        - Pull request review bodies
        - Inline review comments

        Evidence is explicitly numbered so Gemini can cite
        the original review sources.
        """

        # ---------------------------------------------------------
        # Pull request reviews
        # ---------------------------------------------------------

        reviews_query = (
            db.query(
                PullRequestReview
            )
            .join(
                PullRequestReview.pull_request
            )
            .filter(
                PullRequestReview.body.isnot(None)
            )
            .filter(
                PullRequestReview.body != ""
            )
        )

        if repository_id is not None:
            reviews_query = (
                reviews_query.filter(
                    PullRequest.repository_id
                    == repository_id
                )
            )

        reviews = reviews_query.all()

        # ---------------------------------------------------------
        # Inline review comments
        # ---------------------------------------------------------

        comments_query = (
            db.query(
                PullRequestReviewComment
            )
            .join(
                PullRequestReviewComment.pull_request
            )
            .filter(
                PullRequestReviewComment.body.isnot(None)
            )
            .filter(
                PullRequestReviewComment.body != ""
            )
        )

        if repository_id is not None:
            comments_query = (
                comments_query.filter(
                    PullRequest.repository_id
                    == repository_id
                )
            )

        comments = comments_query.all()

        # ---------------------------------------------------------
        # Build numbered evidence
        # ---------------------------------------------------------

        evidence_blocks = []

        source_id = 1
        included_reviews = 0
        included_comments = 0
        skipped_items = 0
        context_characters = 0

        # First add review bodies.
        for review in reviews:

            if not review.body:
                continue

            review_text = (
                review.body.strip()
            )

            if not self._is_useful_review(
                review_text
            ):
                skipped_items += 1
                continue

            block = (
                self._summary_evidence_block(
                    source_id=source_id,
                    source_type="review",
                    text=review_text,
                    reviewer=review.reviewer,
                )
            )

            additional_length = len(block)

            if evidence_blocks:
                additional_length += 2

            if (
                context_characters
                + additional_length
                > MAX_SUMMARY_CONTEXT_CHARS
            ):
                break

            evidence_blocks.append(
                block
            )

            context_characters += (
                additional_length
            )

            included_reviews += 1
            source_id += 1

        # Then add inline comments.
        for comment in comments:

            if not comment.body:
                continue

            comment_text = (
                comment.body.strip()
            )

            if not self._is_useful_review(
                comment_text
            ):
                skipped_items += 1
                continue

            document_text = (
                self._format_comment_text(
                    comment
                )
            )

            block = (
                self._summary_evidence_block(
                    source_id=source_id,
                    source_type="review_comment",
                    text=document_text,
                    path=comment.path,
                    line=comment.line,
                    reviewer=comment.reviewer,
                )
            )

            additional_length = len(block)

            if evidence_blocks:
                additional_length += 2

            if (
                context_characters
                + additional_length
                > MAX_SUMMARY_CONTEXT_CHARS
            ):
                break

            evidence_blocks.append(
                block
            )

            context_characters += (
                additional_length
            )

            included_comments += 1
            source_id += 1

        context = "\n\n".join(
            evidence_blocks
        )

        logger.info(
            "Prepared repository summary context",
            extra={
                "repository_id": (
                    repository_id
                ),
                "total_reviews": len(
                    reviews
                ),
                "total_review_comments": len(
                    comments
                ),
                "included_reviews": (
                    included_reviews
                ),
                "included_comments": (
                    included_comments
                ),
                "skipped_items": (
                    skipped_items
                ),
                "context_characters": (
                    context_characters
                ),
            },
        )

        if not context.strip():

            return {
                "total_reviews": 0,
                "summary": (
                    "No meaningful review comments "
                    "were found."
                ),
            }

        summary = (
            self.ai_service.summarize_repository(
                context=context,
            )
        )

        return {
            "total_reviews": (
                included_reviews
                + included_comments
            ),
            "summary": summary,
        }