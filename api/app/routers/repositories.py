from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Repository
from app.schemas import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
)

router = APIRouter()


def get_repository_or_404(
    repository_id: int,
    db: Session
):
    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found"
        )

    return repository


@router.post(
    "/repositories",
    response_model=RepositoryResponse
)
def create_repository(
    repository: RepositoryCreate,
    db: Session = Depends(get_db)
):
    new_repository = Repository(
        name=repository.name,
        owner=repository.owner,
    )

    db.add(new_repository)
    db.commit()
    db.refresh(new_repository)

    return new_repository


@router.get(
    "/repositories",
    response_model=list[RepositoryResponse]
)
def get_repositories(
    db: Session = Depends(get_db)
):
    repositories = db.query(Repository).all()
    return repositories


@router.get(
    "/repositories/{repository_id}",
    response_model=RepositoryResponse
)
def get_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    repository = get_repository_or_404(
        repository_id,
        db
    )

    return repository


@router.put(
    "/repositories/{repository_id}",
    response_model=RepositoryResponse
)
def update_repository(
    repository_id: int,
    repository_update: RepositoryUpdate,
    db: Session = Depends(get_db)
):
    repository = get_repository_or_404(
        repository_id,
        db
    )

    repository.name = repository_update.name
    repository.owner = repository_update.owner

    db.commit()
    db.refresh(repository)

    return repository


@router.delete("/repositories/{repository_id}")
def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    repository = get_repository_or_404(
        repository_id,
        db
    )

    db.delete(repository)
    db.commit()

    return {
        "message": "Repository deleted successfully"
    }