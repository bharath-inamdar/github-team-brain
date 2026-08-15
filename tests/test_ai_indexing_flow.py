import pytest

from app import models
from app.core.security import hash_password
from app.services.ai_service import RateLimitError
from app.services.ingestion_service import (
    IngestionService,
    RepositoryNotIndexedError,
)


class FakeAIService:
    """
    Records embedding and answer calls so tests can prove that ask only
    embeds the question and never the repository material.
    """

    def __init__(self):
        self.embedding_calls = []
        self.answer_calls = []

    def generate_embedding(self, text):
        self.embedding_calls.append(text)
        return [0.1, 0.2, 0.3]

    def answer_question(self, question, context):
        self.answer_calls.append((question, context))
        return "answer"


class FakeVectorService:
    """
    In-memory stand-in for ChromaDB that behaves like the real vector
    service: upserts by id, checks existence, and scopes counts and
    searches to repository ids.
    """

    def __init__(self):
        self.docs = {}

    def document_exists(self, document_id):
        return document_id in self.docs

    def add_document(self, document_id, document_text, embedding, metadata):
        self.docs[document_id] = {
            "text": document_text,
            "embedding": embedding,
            "metadata": metadata,
        }

    def count_documents(self, repository_ids=None):
        if not repository_ids:
            return len(self.docs)
        return sum(
            1
            for document in self.docs.values()
            if document["metadata"].get("repository_id")
            in repository_ids
        )

    def search_reviews(
        self,
        query_embedding,
        repository_id=None,
        repository_ids=None,
        top_k=5,
    ):
        if repository_ids is None:
            repository_ids = (
                [repository_id]
                if repository_id is not None
                else []
            )

        matched = [
            document_id
            for document_id, document in self.docs.items()
            if document["metadata"].get("repository_id")
            in repository_ids
        ][:top_k]

        return {
            "ids": [matched],
            "documents": [
                [self.docs[document_id]["text"] for document_id in matched]
            ],
            "metadatas": [
                [self.docs[document_id]["metadata"] for document_id in matched]
            ],
            "distances": [[1.0] * len(matched)],
        }


def _service_with_one_indexed_review():
    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()

    vector_service = FakeVectorService()
    vector_service.add_document(
        document_id="review:7:1001",
        document_text="Indexed engineering feedback.",
        embedding=[0.1, 0.2, 0.3],
        metadata={
            "repository_id": 7,
            "source_type": "review",
        },
    )

    service.vector_service = vector_service
    return service


def test_ask_repository_never_triggers_indexing():
    service = _service_with_one_indexed_review()

    def _fail(*args, **kwargs):
        raise AssertionError("ask_repository must never re-index")

    service.index_all_reviews = _fail

    result = service.ask_repository(
        "what did reviewers mention?",
        repository_ids=[7],
    )

    assert result["answer"] == "answer"
    assert result["sources"][0]["text"] == "Indexed engineering feedback."

    # Only the question was embedded, never the indexed material.
    assert service.ai_service.embedding_calls == [
        "what did reviewers mention?"
    ]


def test_ask_repository_queries_existing_vectors_only():
    service = _service_with_one_indexed_review()

    result = service.ask_repository(
        "what did reviewers mention?",
        repository_ids=[7],
    )

    question, context = service.ai_service.answer_calls[0]
    assert question == "what did reviewers mention?"
    assert "Indexed engineering feedback." in context
    assert result["sources"][0]["text"] == "Indexed engineering feedback."


def test_ask_repository_raises_when_repository_not_indexed():
    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()
    service.vector_service = FakeVectorService()

    with pytest.raises(RepositoryNotIndexedError):
        service.ask_repository(
            "what changed?",
            repository_ids=[7],
        )

    # No embedding was wasted on an unindexed repository.
    assert service.ai_service.embedding_calls == []


def test_ask_repository_without_repositories_is_graceful():
    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()
    service.vector_service = FakeVectorService()

    result = service.ask_repository(
        "what changed?",
        repository_ids=None,
    )

    assert result["answer"] == (
        "The repository does not contain enough information."
    )
    assert result["sources"] == []
    assert service.ai_service.embedding_calls == []


def test_index_all_reviews_uses_stable_repository_scoped_ids(
    db_session,
    make_user,
):
    owner_a = make_user(email="a@example.com", username="a")
    owner_b = make_user(email="b@example.com", username="b")

    repo_a = models.Repository(
        user_id=owner_a.id,
        owner="octo-org",
        name="repo-a",
        default_branch="main",
    )
    repo_b = models.Repository(
        user_id=owner_b.id,
        owner="octo-org",
        name="repo-b",
        default_branch="main",
    )
    db_session.add(repo_a)
    db_session.add(repo_b)
    db_session.commit()
    db_session.refresh(repo_a)
    db_session.refresh(repo_b)

    for repository, comment_id in (
        (repo_a, 3001),
        (repo_b, 3002),
    ):
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
                github_comment_id=comment_id,
                reviewer="reviewer",
                body=(
                    "Useful inline comment that must be indexed under a "
                    "stable, repository-scoped document id."
                ),
                path="api/app/services/ingestion_service.py",
                line=42,
            )
        )

    db_session.commit()

    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()
    service.vector_service = FakeVectorService()

    # Both users index into the same shared collection.
    service.index_all_reviews(
        db_session,
        user_id=owner_a.id,
    )
    service.index_all_reviews(
        db_session,
        user_id=owner_b.id,
    )

    # Document ids embed the repository id, so distinct repositories stay
    # isolated even inside one shared collection.
    assert set(service.vector_service.docs) == {
        f"review-comment:{repo_a.id}:3001",
        f"review-comment:{repo_b.id}:3002",
    }
    assert (
        service.vector_service.count_documents(
            repository_ids=[repo_a.id]
        )
        == 1
    )
    assert (
        service.vector_service.count_documents(
            repository_ids=[repo_b.id]
        )
        == 1
    )


def test_index_all_reviews_is_idempotent(db_session, make_user):
    user = make_user()
    repository = models.Repository(
        user_id=user.id,
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
                "This inline review comment should be embedded exactly "
                "once even when indexing runs repeatedly."
            ),
            path="api/app/services/ingestion_service.py",
            line=42,
        )
    )
    db_session.commit()

    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()
    service.vector_service = FakeVectorService()

    first = service.index_all_reviews(
        db_session,
        user_id=user.id,
        repository_id=repository.id,
    )
    second = service.index_all_reviews(
        db_session,
        user_id=user.id,
        repository_id=repository.id,
    )

    assert first["indexed_review_comments"] == 1
    assert second["indexed_review_comments"] == 0
    assert second["skipped_existing"] == 1
    assert len(service.vector_service.docs) == 1
    assert service.ai_service.embedding_calls == [
        "api/app/services/ingestion_service.py at line 42\n"
        "This inline review comment should be embedded exactly "
        "once even when indexing runs repeatedly."
    ]


def test_index_all_reviews_can_target_a_single_repository(
    db_session,
    make_user,
):
    user = make_user()

    repositories = []
    for name in ("target-repo", "other-repo"):
        repository = models.Repository(
            user_id=user.id,
            owner="octo-org",
            name=name,
            default_branch="main",
        )
        db_session.add(repository)
        db_session.commit()
        db_session.refresh(repository)
        repositories.append(repository)

    for index, repository in enumerate(repositories, start=1):
        pull_request = models.PullRequest(
            repository_id=repository.id,
            github_pr_number=index,
            title=f"PR {index}",
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
                github_comment_id=index,
                reviewer="reviewer",
                body=(
                    f"Useful inline comment in {repository.name} that "
                    "should be embedded during indexing."
                ),
                path="api/app/services/ingestion_service.py",
                line=index,
            )
        )

    db_session.commit()

    target = repositories[0]

    service = IngestionService.__new__(IngestionService)
    service.ai_service = FakeAIService()
    service.vector_service = FakeVectorService()

    result = service.index_all_reviews(
        db_session,
        user_id=user.id,
        repository_id=target.id,
    )

    assert result["indexed_review_comments"] == 1
    assert set(service.vector_service.docs) == {
        f"review-comment:{target.id}:1"
    }


def test_ask_embedding_rate_limit_surfaces_as_429_not_500(client, monkeypatch):
    from app.routers.ai import get_ingestion_service

    test_client, session_factory = client
    db = session_factory()

    try:
        user = models.User(
            email="owner@example.com",
            username="owner",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        repository = models.Repository(
            user_id=user.id,
            owner="octo-org",
            name="octo-repo",
            default_branch="main",
        )
        db.add(repository)
        db.commit()
        db.refresh(repository)
        repository_id = repository.id
    finally:
        db.close()

    login = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@example.com",
            "password": "password123",
        },
    )
    assert login.status_code == 200
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    class _RateLimitedIngestion:
        def ask_repository(self, question, repository_ids):
            raise RateLimitError(retry_after_seconds=60)

    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: _RateLimitedIngestion(),
    )

    response = test_client.get(
        "/api/v1/ai/ask",
        params={
            "question": "what changed?",
            "repository_id": repository_id,
        },
        headers=headers,
    )

    assert response.status_code == 429
    assert response.headers.get("retry-after") == "60"


def test_ask_unindexed_repository_returns_409(client, monkeypatch):
    from app.routers.ai import get_ingestion_service
    from app.services.ingestion_service import NOT_INDEXED_MESSAGE

    test_client, session_factory = client
    db = session_factory()

    try:
        user = models.User(
            email="owner@example.com",
            username="owner",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        repository = models.Repository(
            user_id=user.id,
            owner="octo-org",
            name="octo-repo",
            default_branch="main",
        )
        db.add(repository)
        db.commit()
        db.refresh(repository)
        repository_id = repository.id
    finally:
        db.close()

    login = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@example.com",
            "password": "password123",
        },
    )
    assert login.status_code == 200
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    class _UnindexedIngestion:
        def ask_repository(self, question, repository_ids):
            raise RepositoryNotIndexedError()

    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: _UnindexedIngestion(),
    )

    response = test_client.get(
        "/api/v1/ai/ask",
        params={
            "question": "what changed?",
            "repository_id": repository_id,
        },
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == NOT_INDEXED_MESSAGE


def test_import_review_comments_triggers_repository_indexing(
    client,
    monkeypatch,
):
    from app.routers.ai import get_ingestion_service
    from app.routers.repositories import review_service

    test_client, session_factory = client
    db = session_factory()

    try:
        user = models.User(
            email="owner@example.com",
            username="owner",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        repository = models.Repository(
            user_id=user.id,
            owner="octo-org",
            name="octo-repo",
            default_branch="main",
        )
        db.add(repository)
        db.commit()
        db.refresh(repository)
        user_id = user.id
        repository_id = repository.id
    finally:
        db.close()

    monkeypatch.setattr(
        review_service,
        "import_pull_request_review_comments",
        lambda owner, repo, db: 0,
    )

    class _RecordingIngestion:
        def __init__(self):
            self.calls = []

        def index_all_reviews(self, db, user_id, repository_id=None):
            self.calls.append((user_id, repository_id))
            return {
                "total_reviews": 0,
                "total_review_comments": 0,
                "indexed": 0,
                "indexed_reviews": 0,
                "indexed_review_comments": 0,
                "skipped_empty": 0,
                "skipped_short": 0,
                "skipped_bot": 0,
                "skipped_existing": 0,
            }

    fake = _RecordingIngestion()
    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: fake,
    )

    login = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@example.com",
            "password": "password123",
        },
    )
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = test_client.post(
        "/api/v1/repositories/import/octo-org/octo-repo/review-comments",
        headers=headers,
    )

    assert response.status_code == 200
    assert fake.calls == [(user_id, repository_id)]


def test_import_indexing_failure_does_not_fail_import(
    client,
    monkeypatch,
):
    from app.routers.ai import get_ingestion_service
    from app.routers.repositories import review_service

    test_client, session_factory = client
    db = session_factory()

    try:
        user = models.User(
            email="owner@example.com",
            username="owner",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        repository = models.Repository(
            user_id=user.id,
            owner="octo-org",
            name="octo-repo",
            default_branch="main",
        )
        db.add(repository)
        db.commit()
        db.refresh(repository)
    finally:
        db.close()

    monkeypatch.setattr(
        review_service,
        "import_pull_request_review_comments",
        lambda owner, repo, db: 0,
    )

    class _FailingIngestion:
        def index_all_reviews(self, db, user_id, repository_id=None):
            raise RateLimitError(retry_after_seconds=60)

    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: _FailingIngestion(),
    )

    login = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@example.com",
            "password": "password123",
        },
    )
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    response = test_client.post(
        "/api/v1/repositories/import/octo-org/octo-repo/review-comments",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Review comments imported successfully."
    )


def test_index_all_reviews_repository_id_requires_ownership(
    client,
    monkeypatch,
):
    from app.routers.ai import get_ingestion_service

    test_client, session_factory = client
    db = session_factory()

    try:
        owner = models.User(
            email="owner@example.com",
            username="owner",
            hashed_password=hash_password("password123"),
        )
        other = models.User(
            email="other@example.com",
            username="other",
            hashed_password=hash_password("password123"),
        )
        db.add(owner)
        db.add(other)
        db.commit()
        db.refresh(owner)
        db.refresh(other)
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
        db.add(owner_repo)
        db.add(other_repo)
        db.commit()
        db.refresh(owner_repo)
        db.refresh(other_repo)
        owner_id = owner.id
        owner_repo_id = owner_repo.id
        other_repo_id = other_repo.id
    finally:
        db.close()

    class _RecordingIngestion:
        def __init__(self):
            self.calls = []

        def index_all_reviews(self, db, user_id, repository_id=None):
            self.calls.append((user_id, repository_id))
            return {
                "total_reviews": 0,
                "total_review_comments": 0,
                "indexed": 0,
                "indexed_reviews": 0,
                "indexed_review_comments": 0,
                "skipped_empty": 0,
                "skipped_short": 0,
                "skipped_bot": 0,
                "skipped_existing": 0,
            }

    fake = _RecordingIngestion()
    monkeypatch.setitem(
        test_client.app.dependency_overrides,
        get_ingestion_service,
        lambda: fake,
    )

    login = test_client.post(
        "/api/v1/auth/login",
        data={
            "username": "owner@example.com",
            "password": "password123",
        },
    )
    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    forbidden = test_client.post(
        "/api/v1/ai/index-all-reviews",
        params={"repository_id": other_repo_id},
        headers=headers,
    )
    assert forbidden.status_code == 403
    assert fake.calls == []

    allowed = test_client.post(
        "/api/v1/ai/index-all-reviews",
        params={"repository_id": owner_repo_id},
        headers=headers,
    )
    assert allowed.status_code == 200
    assert fake.calls == [(owner_id, owner_repo_id)]
