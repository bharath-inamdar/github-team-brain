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


def test_repository_crud(db_session):
    created = repository_service.create_repository(
        _repository_create(),
        db_session,
    )

    assert created.id is not None
    assert created.owner == "openai"

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
    )

    assert updated.description == "Updated description"
    assert updated.language == "TypeScript"

    result = repository_service.delete_repository(created.id, db_session)
    assert result == {"message": "Repository deleted successfully"}

    with pytest.raises(HTTPException) as exc_info:
        repository_service.get_repository_or_404(created.id, db_session)

    assert exc_info.value.status_code == 404


def test_import_repository_from_github_updates_existing(
    db_session,
    monkeypatch,
):
    repository_service.create_repository(
        _repository_create(owner="octo-org", name="octo-repo"),
        db_session,
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
    )

    assert imported.description == "Synced from GitHub"
    assert imported.stars == 42
    assert len(repository_service.get_repositories(db_session)) == 1
