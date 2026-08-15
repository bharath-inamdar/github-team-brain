import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Repository
from app.schemas import (
    RepositoryCreate,
    RepositoryUpdate,
)
from app.services import github_service

GITHUB_REPOSITORY_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def parse_github_repository_url(url: str) -> tuple[str, str]:
    """
    Parse browser and clone-style GitHub repository URLs.
    """

    match = GITHUB_REPOSITORY_URL_PATTERN.match(url.strip())

    if match is None:
        raise HTTPException(
            status_code=422,
            detail="Enter a valid GitHub repository URL, for example https://github.com/openai/openai-python.",
        )

    return match.group("owner"), match.group("repo")


def create_repository(
    repository: RepositoryCreate,
    db: Session,
    user_id: int,
):
    new_repository = Repository(
        user_id=user_id,
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
    user_id: int,
    skip: int = 0,
    limit: int = 20,
):
    return (
        db.query(Repository)
        .filter(Repository.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_repository_ids(
    db: Session,
    user_id: int,
) -> list[int]:
    """
    Returns the ids of every repository owned by a user.
    Used to scope ChromaDB RAG queries to the authenticated user.
    """
    rows = (
        db.query(Repository.id)
        .filter(Repository.user_id == user_id)
        .all()
    )

    return [row[0] for row in rows]


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


def get_owned_repository_or_404(
    repository_id: int,
    user_id: int,
    db: Session,
):
    """
    Resolve a repository and verify the authenticated user owns it.
    """
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

    if repository.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this repository",
        )

    return repository


def get_owned_repository_or_404_by_owner_name(
    owner: str,
    repo: str,
    user_id: int,
    db: Session,
):
    """
    Resolve a repository by owner/name and verify the authenticated
    user owns it.
    """
    repository = (
        db.query(Repository)
        .filter(
            Repository.user_id == user_id,
            Repository.owner == owner,
            Repository.name == repo,
        )
        .first()
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found. Import the repository first.",
        )

    return repository


def update_repository(
    repository_id: int,
    repository_update: RepositoryUpdate,
    db: Session,
    user_id: int,
):
    repository = get_owned_repository_or_404(
        repository_id,
        user_id,
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
    user_id: int,
):
    repository = get_owned_repository_or_404(
        repository_id,
        user_id,
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
    user_id: int,
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
            Repository.user_id == user_id,
            Repository.owner == github_repository["owner"],
            Repository.name == github_repository["name"],
        )
        .first()
    )

    if repository is None:
        repository = Repository(
            user_id=user_id,
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
