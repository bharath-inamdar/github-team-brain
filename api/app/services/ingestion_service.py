import logging

from sqlalchemy.orm import Session

from app.models import PullRequestReview, PullRequestReviewComment
from app.services.ai_service import AIService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)

MAX_SUMMARY_CONTEXT_CHARS = 40000


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

        self.vector_service.add_review(
            review_id=review.github_review_id,
            review_text=review.body,
            embedding=embedding,
            metadata={
                "repository_id": review.pull_request.repository_id,
                "reviewer": review.reviewer or "",
                "state": review.state or "",
                "review_id": review.github_review_id,
                "pull_request_id": review.pull_request_id,
            },
        )

        return f"Indexed review {review.github_review_id}"

    def index_all_reviews(self, db: Session):
        """
        Index every useful pull request review into ChromaDB.
        """

        reviews = db.query(PullRequestReview).all()

        indexed = 0
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

            if self.vector_service.review_exists(
                review.github_review_id
            ):
                skipped_existing += 1
                continue

            embedding = self.ai_service.generate_embedding(
                review_text
            )

            self.vector_service.add_review(
                review_id=review.github_review_id,
                review_text=review_text,
                embedding=embedding,
                metadata={
                    "repository_id": review.pull_request.repository_id,
                    "reviewer": review.reviewer,
                    "state": review.state,
                    "review_id": review.github_review_id,
                    "pull_request_id": review.pull_request_id,
                },
            )

            indexed += 1

        return {
            "total_reviews": len(reviews),
            "indexed": indexed,
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
    ):
        """
        Answers a question about the repository
        using semantic search.
        """

        search_results = self.search_reviews(
            question,
            repository_id=repository_id,
        )

        documents = search_results.get("documents", [[]])[0]

        context = "\n\n".join(documents)

        answer = self.ai_service.answer_question(
            question=question,
            context=context,
        )

        return {
            "question": question,
            "answer": answer,
            "sources": documents,
        }

    def summarize_repository(
        self,
        db: Session,
    ):
        """
        Generates a repository engineering summary using only useful review comments.
        """

        comments = (
            db.query(PullRequestReviewComment)
            .filter(PullRequestReviewComment.body.isnot(None))
            .filter(PullRequestReviewComment.body != "")
            .all()
        )

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
