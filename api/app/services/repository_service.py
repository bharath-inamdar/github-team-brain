from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Repository
from app.schemas import (
    RepositoryCreate,
    RepositoryUpdate,
)
from app.services import github_service


def create_repository(
    repository: RepositoryCreate,
    db: Session,
):
    new_repository = Repository(
        owner=repository.owner,
        name=repository.name,
        description=repository.description,
        language=repository.language,
        stars=repository.stars,
        forks=repository.forks,
        open_issues=repository.open_issues,
        default_branch=repository.default_branch,
    )

    db.add(new_repository)
    db.commit()
    db.refresh(new_repository)

    return new_repository


def get_repositories(
    db: Session,
):
    return db.query(Repository).all()


def get_repository_or_404(
    repository_id: int,
    db: Session,
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return repository


def update_repository(
    repository_id: int,
    repository_update: RepositoryUpdate,
    db: Session,
):
    repository = get_repository_or_404(
        repository_id,
        db,
    )

    repository.owner = repository_update.owner
    repository.name = repository_update.name
    repository.description = repository_update.description
    repository.language = repository_update.language
    repository.stars = repository_update.stars
    repository.forks = repository_update.forks
    repository.open_issues = repository_update.open_issues
    repository.default_branch = repository_update.default_branch

    db.commit()
    db.refresh(repository)

    return repository


def delete_repository(
    repository_id: int,
    db: Session,
):
    repository = get_repository_or_404(
        repository_id,
        db,
    )

    db.delete(repository)
    db.commit()

    return {
        "message": "Repository deleted successfully",
    }


def import_repository_from_github(
    owner: str,
    repo: str,
    db: Session,
):
    """
    Fetch repository details from GitHub and
    synchronize them with our database.
    """

    github_repository = github_service.get_repository_details(
        owner,
        repo,
    )

    repository = (
        db.query(Repository)
        .filter(
            Repository.owner == github_repository["owner"],
            Repository.name == github_repository["name"],
        )
        .first()
    )

    if repository is None:
        repository = Repository(
            owner=github_repository["owner"],
            name=github_repository["name"],
            description=github_repository["description"],
            language=github_repository["language"],
            stars=github_repository["stars"],
            forks=github_repository["forks"],
            open_issues=github_repository["open_issues"],
            default_branch=github_repository["default_branch"],
        )

        db.add(repository)

    else:
        repository.description = github_repository["description"]
        repository.language = github_repository["language"]
        repository.stars = github_repository["stars"]
        repository.forks = github_repository["forks"]
        repository.open_issues = github_repository["open_issues"]
        repository.default_branch = github_repository["default_branch"]

    db.commit()
    db.refresh(repository)

    return repository