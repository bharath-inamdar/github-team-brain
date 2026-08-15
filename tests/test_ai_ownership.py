from app import models
from app.core.security import hash_password
from app.routers.ai import get_ingestion_service


class FakeIngestionService:
    """
    Records how the AI router calls the ingestion service so tests
    can assert that ownership scoping happened before any vector
    store interaction.
    """

    def __init__(self):
        self.calls = []

    def index_first_review(self, db, user_id):
        self.calls.append(("index_first_review", user_id))
        return "indexed"

    def index_all_reviews(self, db, user_id, repository_id=None):
        self.calls.append(("index_all_reviews", user_id, repository_id))
        return {
            "total_reviews": 0,
            "indexed": 0,
            "skipped_empty": 0,
            "skipped_short": 0,
            "skipped_bot": 0,
            "skipped_existing": 0,
        }

    def search_reviews(self, question, repository_ids):
        self.calls.append(("search_reviews", question, repository_ids))
        return []

    def ask_repository(self, question, repository_ids):
        self.calls.append(("ask_repository", question, repository_ids))
        return {"question": question, "answer": "ok", "sources": []}

    def summarize_repository(self, db, user_id, repository_id):
        self.calls.append(("summarize_repository", user_id, repository_id))
        return {"total_reviews": 0, "summary": "ok"}


def _create_user(db, email, username=None):
    user = models.User(
        email=email,
        username=username or email.split("@")[0],
        hashed_password=hash_password("password123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_repository(db, user, owner="octo-org", name="octo-repo"):
    repository = models.Repository(
        user_id=user.id,
        owner=owner,
        name=name,
        default_branch="main",
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)
    return repository


def _auth_headers(client, email):
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "password123"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_ai_endpoints_require_authentication(client):
    test_client, _ = client

    assert (
        test_client.get("/api/v1/ai/ask", params={"question": "q"}).status_code
        == 401
    )
    assert (
        test_client.get(
            "/api/v1/ai/search",
            params={"question": "q"},
        ).status_code
        == 401
    )
    assert (
        test_client.get("/api/v1/ai/repository-summary").status_code
        == 401
    )
    assert (
        test_client.post("/api/v1/ai/index-all-reviews").status_code
        == 401
    )


def test_cross_user_ai_access_denied_before_vector_store(
    client,
    monkeypatch,
):
    test_client, session_factory = client
    db = session_factory()

    try:
        owner = _create_user(db, email="owner@example.com")
        other = _create_user(db, email="other@example.com")
        repository = _create_repository(
            db,
            owner,
            owner="octo-org",
            name="octo-repo",
        )
        other_id = other.id
        repository_id = repository.id
    finally:
        db.close()

    fake = FakeIngestionService()
    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: fake,
    )

    headers = _auth_headers(test_client, "other@example.com")

    ask = test_client.get(
        "/api/v1/ai/ask",
        params={"question": "q", "repository_id": repository_id},
        headers=headers,
    )
    assert ask.status_code == 403

    search = test_client.get(
        "/api/v1/ai/search",
        params={"question": "q", "repository_id": repository_id},
        headers=headers,
    )
    assert search.status_code == 403

    summary = test_client.get(
        "/api/v1/ai/repository-summary",
        params={"repository_id": repository_id},
        headers=headers,
    )
    assert summary.status_code == 403

    assert fake.calls == []


def test_owner_can_query_own_repository(client, monkeypatch):
    test_client, session_factory = client
    db = session_factory()

    try:
        owner = _create_user(db, email="owner@example.com")
        repository = _create_repository(
            db,
            owner,
            owner="octo-org",
            name="octo-repo",
        )
        owner_id = owner.id
        repository_id = repository.id
    finally:
        db.close()

    fake = FakeIngestionService()
    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: fake,
    )

    headers = _auth_headers(test_client, "owner@example.com")

    ask = test_client.get(
        "/api/v1/ai/ask",
        params={"question": "what changed?", "repository_id": repository_id},
        headers=headers,
    )
    assert ask.status_code == 200
    assert fake.calls[-1] == (
        "ask_repository",
        "what changed?",
        [repository_id],
    )

    summary = test_client.get(
        "/api/v1/ai/repository-summary",
        params={"repository_id": repository_id},
        headers=headers,
    )
    assert summary.status_code == 200
    assert fake.calls[-1] == (
        "summarize_repository",
        owner_id,
        repository_id,
    )


def test_no_repository_id_resolves_to_owned_repositories(
    client,
    monkeypatch,
):
    test_client, session_factory = client
    db = session_factory()

    try:
        owner = _create_user(db, email="owner@example.com")
        first = _create_repository(
            db,
            owner,
            owner="octo-org",
            name="first-repo",
        )
        second = _create_repository(
            db,
            owner,
            owner="octo-org",
            name="second-repo",
        )
        owner_id = owner.id
        first_id = first.id
        second_id = second.id
    finally:
        db.close()

    fake = FakeIngestionService()
    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: fake,
    )

    headers = _auth_headers(test_client, "owner@example.com")

    ask = test_client.get(
        "/api/v1/ai/ask",
        params={"question": "q"},
        headers=headers,
    )
    assert ask.status_code == 200
    assert fake.calls[-1][0] == "ask_repository"
    assert sorted(fake.calls[-1][2]) == sorted([first_id, second_id])


def test_index_all_reviews_scoped_to_owner(client, monkeypatch):
    test_client, session_factory = client
    db = session_factory()

    try:
        owner = _create_user(db, email="owner@example.com")
        other = _create_user(db, email="other@example.com")
        owner_repo = _create_repository(
            db,
            owner,
            owner="octo-org",
            name="owner-repo",
        )
        other_repo = _create_repository(
            db,
            other,
            owner="other-org",
            name="other-repo",
        )

        owner_pr = models.PullRequest(
            repository_id=owner_repo.id,
            github_pr_number=1,
            title="Owner PR",
            body="",
            state="open",
            author="owner",
        )
        other_pr = models.PullRequest(
            repository_id=other_repo.id,
            github_pr_number=1,
            title="Other PR",
            body="",
            state="open",
            author="other",
        )
        db.add(owner_pr)
        db.add(other_pr)
        db.commit()
        db.refresh(owner_pr)
        db.refresh(other_pr)

        db.add(
            models.PullRequestReview(
                pull_request_id=owner_pr.id,
                github_review_id=1,
                reviewer="owner",
                state="COMMENTED",
                body=(
                    "Owner review feedback that should be indexed "
                    "for the owner only."
                ),
            )
        )
        db.add(
            models.PullRequestReview(
                pull_request_id=other_pr.id,
                github_review_id=2,
                reviewer="other",
                state="COMMENTED",
                body=(
                    "Other user's review feedback that must never be "
                    "indexed for the owner."
                ),
            )
        )
        db.commit()
        owner_id = owner.id
    finally:
        db.close()

    fake = FakeIngestionService()
    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: fake,
    )

    response = test_client.post(
        "/api/v1/ai/index-all-reviews",
        headers=_auth_headers(test_client, "owner@example.com"),
    )
    assert response.status_code == 200
    assert fake.calls == [("index_all_reviews", owner_id, None)]


def test_index_all_reviews_service_only_indexes_owner_reviews(
    db_session,
    make_user,
):
    owner = make_user(email="owner@example.com", username="owner")
    other = make_user(email="other@example.com", username="other")

    owner_repo = models.Repository(
        user_id=owner.id,
        owner="octo-org",
        name="owner-repo",
        default_branch="main",
    )
    other_repo = models.Repository(
        user_id=other.id,
        owner="other-org",
        name="other-repo",
        default_branch="main",
    )
    db_session.add(owner_repo)
    db_session.add(other_repo)
    db_session.commit()
    db_session.refresh(owner_repo)
    db_session.refresh(other_repo)

    owner_pr = models.PullRequest(
        repository_id=owner_repo.id,
        github_pr_number=1,
        title="Owner PR",
        body="",
        state="open",
        author="owner",
    )
    other_pr = models.PullRequest(
        repository_id=other_repo.id,
        github_pr_number=1,
        title="Other PR",
        body="",
        state="open",
        author="other",
    )
    db_session.add(owner_pr)
    db_session.add(other_pr)
    db_session.commit()
    db_session.refresh(owner_pr)
    db_session.refresh(other_pr)

    db_session.add(
        models.PullRequestReviewComment(
            pull_request_id=owner_pr.id,
            github_comment_id=1,
            reviewer="owner",
            body=(
                "Owner inline review comment that should be indexed "
                "for the owner only."
            ),
            path="api/app/services/ingestion_service.py",
            line=10,
        )
    )
    db_session.add(
        models.PullRequestReviewComment(
            pull_request_id=other_pr.id,
            github_comment_id=2,
            reviewer="other",
            body=(
                "Other user's inline comment that must never be "
                "indexed for the owner."
            ),
            path="api/app/services/ingestion_service.py",
            line=11,
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
                    "metadata": metadata,
                }
            )

    from app.services.ingestion_service import IngestionService

    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()
    service.vector_service = FakeVectorService()

    result = service.index_all_reviews(
        db_session,
        user_id=owner.id,
    )

    assert result["indexed_review_comments"] == 1
    assert service.vector_service.documents == [
        {
            "document_id": f"review-comment:{owner_repo.id}:1",
            "metadata": {
                "repository_id": owner_repo.id,
                "reviewer": "owner",
                "source_type": "review_comment",
                "comment_id": 1,
                "pull_request_id": owner_pr.id,
                "path": "api/app/services/ingestion_service.py",
                "line": 10,
            },
        }
    ]
