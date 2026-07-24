from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Repository
from app.schemas import RepositoryCreate, RepositoryResponse

router = APIRouter()


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


@router.get("/repositories")
def get_repositories(db: Session = Depends(get_db)):
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

@router.get(
    "/repositories/{repository_id}",
    response_model=RepositoryResponse
)
def get_repository(
    repository_id: int,
    db: Session = Depends(get_db)
):
    repository = db.query(Repository).filter(
        Repository.id == repository_id
    ).first()

    return repository