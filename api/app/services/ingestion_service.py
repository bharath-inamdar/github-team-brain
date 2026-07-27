from sqlalchemy.orm import Session

from app.models import PullRequestReview
from app.services.ai_service import AIService
from app.services.vector_service import VectorService


class IngestionService:
    """
    Handles indexing GitHub data into ChromaDB.
    """

    def __init__(self):
        self.ai_service = AIService()
        self.vector_service = VectorService()

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
        )

        return f"Indexed review {review.github_review_id}"

    def index_all_reviews(self, db: Session):
        """
        Index every pull request review into ChromaDB.
        """

        reviews = db.query(PullRequestReview).all()

        indexed = 0
        skipped_empty = 0
        skipped_existing = 0

        for review in reviews:

            # Skip reviews with no text
            if not review.body or review.body.strip() == "":
                skipped_empty += 1
                continue

            # Skip already indexed reviews
            if self.vector_service.review_exists(
                review.github_review_id
            ):
                skipped_existing += 1
                continue

            # Generate Gemini embedding
            embedding = self.ai_service.generate_embedding(
                review.body
            )

            # Store in ChromaDB
            self.vector_service.add_review(
                review_id=review.github_review_id,
                review_text=review.body,
                embedding=embedding,
                metadata={
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
            "skipped_existing": skipped_existing,
        }

    def search_reviews(
        self,
        question: str,
    ):
        """
        Searches indexed reviews using semantic similarity.
        """

        embedding = self.ai_service.generate_embedding(
            question
        )

        return self.vector_service.search_reviews(
            embedding
        )

    def ask_repository(
        self,
        question: str,
    ):
        """
        Answers a question about the repository
        using semantic search.
        """

        search_results = self.search_reviews(question)

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