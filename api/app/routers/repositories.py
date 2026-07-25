from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services import github_service
from app.database import get_db
from app.schemas import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
)
from app.services import repository_service

router = APIRouter()


@router.post(
    "/repositories",
    response_model=RepositoryResponse
)
def create_repository(
    repository: RepositoryCreate,
    db: Session = Depends(get_db)
):
    return repository_service.create_repository(
        repository,
        db
    )


@router.get(
    "/repositories",
    response_model=list[RepositoryResponse]
)
def get_repositories(
    db: Session = Depends(get_db)
):
    return repository_service.get_repositories(db)


@router.get(
    "/repositories/{repository_id}",
    response_model=RepositoryResponse
)
def get_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    return repository_service.get_repository_or_404(
        repository_id,
        db
    )


@router.put(
    "/repositories/{repository_id}",
    response_model=RepositoryResponse
)
def update_repository(
    repository_id: int,
    repository_update: RepositoryUpdate,
    db: Session = Depends(get_db)
):
    return repository_service.update_repository(
        repository_id,
        repository_update,
        db
    )


@router.delete("/repositories/{repository_id}")
def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    return repository_service.delete_repository(
        repository_id,
        db
    )

@router.get("/github/{owner}/{repo}")
def fetch_github_repository(
    owner: str,
    repo: str
):
    return github_service.get_repository_details(
        owner,
        repo
    )

@router.post(
    "/repositories/import/{owner}/{repo}",
    response_model=RepositoryResponse,
)
def import_repository(
    owner: str,
    repo: str,
    db: Session = Depends(get_db),
):
    return repository_service.import_repository_from_github(
        owner,
        repo,
        db,
    )