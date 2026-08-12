from app import models
from app.services.ingestion_service import IngestionService


def test_is_useful_review_filters_empty_short_and_bot_text():
    service = IngestionService.__new__(IngestionService)

    assert service._is_useful_review("") is False
    assert service._is_useful_review("LGTM") is False
    assert service._is_useful_review("Dependabot updated a dependency") is False
    assert service._is_useful_review("Approved, looks good to me overall") is False


def test_is_useful_review_allows_meaningful_feedback():
    service = IngestionService.__new__(IngestionService)

    review = (
        "This query should be indexed by repository_id because otherwise "
        "search results can mix unrelated repositories."
    )

    assert service._is_useful_review(review) is True


def test_summarize_repository_uses_review_comments(db_session):
    repository = models.Repository(
        owner="octo-org",
        name="octo-repo",
        default_branch="main",
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)

    pull_request = models.PullRequest(
        repository_id=repository.id,
        github_pr_number=12,
        title="Improve repository summary",
        body="",
        state="open",
        author="octocat",
    )
    db_session.add(pull_request)
    db_session.commit()
    db_session.refresh(pull_request)

    db_session.add(
        models.PullRequestReview(
            pull_request_id=pull_request.id,
            github_review_id=2001,
            reviewer="reviewer",
            state="COMMENTED",
            body=(
                "This useful review body should not be used by repository "
                "summary generation anymore."
            ),
        )
    )
    db_session.add(
        models.PullRequestReviewComment(
            pull_request_id=pull_request.id,
            github_comment_id=3001,
            reviewer="reviewer",
            body=(
                "The repository summary should use this inline engineering "
                "comment about the implementation details."
            ),
        )
    )
    db_session.commit()

    class FakeAIService:
        context = None

        def summarize_repository(self, context):
            self.context = context
            return "summary"

    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()

    result = service.summarize_repository(db_session)

    assert result == {
        "total_reviews": 1,
        "summary": "summary",
    }
    assert service.ai_service.context == (
        "The repository summary should use this inline engineering "
        "comment about the implementation details."
    )


def test_index_all_reviews_indexes_inline_review_comments(db_session):
    repository = models.Repository(
        owner="octo-org",
        name="octo-repo",
        default_branch="main",
    )
    db_session.add(repository)
    db_session.commit()
    db_session.refresh(repository)

    pull_request = models.PullRequest(
        repository_id=repository.id,
        github_pr_number=12,
        title="Improve retrieval",
        body="",
        state="open",
        author="octocat",
    )
    db_session.add(pull_request)
    db_session.commit()
    db_session.refresh(pull_request)

    db_session.add(
        models.PullRequestReviewComment(
            pull_request_id=pull_request.id,
            github_comment_id=3001,
            reviewer="reviewer",
            body=(
                "This inline review comment should be embedded because it "
                "contains the useful implementation feedback."
            ),
            path="api/app/services/ingestion_service.py",
            line=42,
        )
    )
    db_session.commit()

    class FakeAIService:
        def generate_embedding(self, text):
            return [0.1, 0.2, 0.3]

    class FakeVectorService:
        documents = []

        def document_exists(self, document_id):
            return False

        def add_document(self, document_id, document_text, embedding, metadata):
            self.documents.append(
                {
                    "document_id": document_id,
                    "document_text": document_text,
                    "embedding": embedding,
                    "metadata": metadata,
                }
            )

    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()
    service.vector_service = FakeVectorService()

    result = service.index_all_reviews(db_session)

    assert result["indexed_review_comments"] == 1
    assert service.vector_service.documents == [
        {
            "document_id": "review-comment:3001",
            "document_text": (
                "api/app/services/ingestion_service.py at line 42\n"
                "This inline review comment should be embedded because it "
                "contains the useful implementation feedback."
            ),
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {
                "repository_id": repository.id,
                "reviewer": "reviewer",
                "source_type": "review_comment",
                "comment_id": 3001,
                "pull_request_id": pull_request.id,
                "path": "api/app/services/ingestion_service.py",
                "line": 42,
            },
        }
    ]
