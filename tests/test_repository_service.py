import pytest
from fastapi import HTTPException

from app.schemas import RepositoryCreate, RepositoryUpdate
from app.services import repository_service


def _repository_create(owner: str = "openai", name: str = "teambrain"):
    return RepositoryCreate(
        owner=owner,
        name=name,
        description="AI-powered GitHub knowledge assistant",
        language="Python",
        stars=10,
        forks=2,
        open_issues=1,
        default_branch="main",
    )


def test_repository_crud(db_session, make_user):
    user = make_user()

    created = repository_service.create_repository(
        _repository_create(),
        db_session,
        user_id=user.id,
    )

    assert created.id is not None
    assert created.owner == "openai"
    assert created.user_id == user.id

    fetched = repository_service.get_repository_or_404(
        created.id,
        db_session,
    )
    assert fetched.name == "teambrain"

    updated = repository_service.update_repository(
        created.id,
        RepositoryUpdate(
            owner="openai",
            name="teambrain",
            description="Updated description",
            language="TypeScript",
            stars=20,
            forks=3,
            open_issues=0,
            default_branch="main",
        ),
        db_session,
        user_id=user.id,
    )

    assert updated.description == "Updated description"
    assert updated.language == "TypeScript"

    result = repository_service.delete_repository(
        created.id,
        db_session,
        user_id=user.id,
    )
    assert result == {"message": "Repository deleted successfully"}

    with pytest.raises(HTTPException) as exc_info:
        repository_service.get_repository_or_404(created.id, db_session)

    assert exc_info.value.status_code == 404


def test_repositories_scoped_by_user(db_session, make_user):
    user_a = make_user(email="a@example.com")
    user_b = make_user(email="b@example.com")

    repository_service.create_repository(
        _repository_create(owner="a-org", name="a-repo"),
        db_session,
        user_id=user_a.id,
    )
    repository_service.create_repository(
        _repository_create(owner="b-org", name="b-repo"),
        db_session,
        user_id=user_b.id,
    )

    user_a_repositories = repository_service.get_repositories(
        db_session,
        user_id=user_a.id,
    )
    user_b_repositories = repository_service.get_repositories(
        db_session,
        user_id=user_b.id,
    )

    assert [r.owner for r in user_a_repositories] == ["a-org"]
    assert [r.owner for r in user_b_repositories] == ["b-org"]


def test_cross_user_access_denied(db_session, make_user):
    user_a = make_user(email="a@example.com")
    user_b = make_user(email="b@example.com")

    created = repository_service.create_repository(
        _repository_create(owner="a-org", name="a-repo"),
        db_session,
        user_id=user_a.id,
    )

    with pytest.raises(HTTPException) as exc_info:
        repository_service.get_owned_repository_or_404(
            created.id,
            user_b.id,
            db_session,
        )

    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        repository_service.delete_repository(
            created.id,
            db_session,
            user_id=user_b.id,
        )

    assert exc_info.value.status_code == 403


def test_import_repository_from_github_updates_existing(
    db_session,
    monkeypatch,
    make_user,
):
    user = make_user()

    repository_service.create_repository(
        _repository_create(owner="octo-org", name="octo-repo"),
        db_session,
        user_id=user.id,
    )

    monkeypatch.setattr(
        repository_service.github_service,
        "get_repository_details",
        lambda owner, repo: {
            "owner": owner,
            "name": repo,
            "description": "Synced from GitHub",
            "language": "Python",
            "stars": 42,
            "forks": 7,
            "open_issues": 5,
            "default_branch": "main",
        },
    )

    imported = repository_service.import_repository_from_github(
        "octo-org",
        "octo-repo",
        db_session,
        user_id=user.id,
    )

    assert imported.description == "Synced from GitHub"
    assert imported.stars == 42
    assert len(repository_service.get_repositories(db_session, user_id=user.id)) == 1


def test_import_repository_from_github_scoped_per_user(
    db_session,
    monkeypatch,
    make_user,
):
    user_a = make_user(email="a@example.com")
    user_b = make_user(email="b@example.com")

    monkeypatch.setattr(
        repository_service.github_service,
        "get_repository_details",
        lambda owner, repo: {
            "owner": owner,
            "name": repo,
            "description": "Synced from GitHub",
            "language": "Python",
            "stars": 1,
            "forks": 1,
            "open_issues": 1,
            "default_branch": "main",
        },
    )

    imported = repository_service.import_repository_from_github(
        "octo-org",
        "octo-repo",
        db_session,
        user_id=user_a.id,
    )

    assert imported.user_id == user_a.id

    # A second user importing the same GitHub repository must get their own row.
    imported_b = repository_service.import_repository_from_github(
        "octo-org",
        "octo-repo",
        db_session,
        user_id=user_b.id,
    )

    assert imported_b.user_id == user_b.id
    assert imported_b.id != imported.id
    assert len(repository_service.get_repositories(db_session, user_id=user_a.id)) == 1
    assert len(repository_service.get_repositories(db_session, user_id=user_b.id)) == 1
