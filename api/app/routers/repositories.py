import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas import (
    RepositoryCreate,
    RepositoryImportRequest,
    RepositoryImportResponse,
    RepositoryUpdate,
    RepositoryResponse,
)

from app.services import (
    github_service,
    pull_request_service,
    repository_service,
    review_service,
)

from app.routers.ai import get_ingestion_service
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter()


def _index_imported_repository_best_effort(
    ingestion_service: IngestionService,
    db: Session,
    user_id: int,
    repository_id: int,
) -> None:
    """
    Index a just-imported repository into ChromaDB.

    Best-effort by design: if the AI provider rate-limits or the vector
    store is unavailable, the import still succeeds and the user can
    retry indexing explicitly via /ai/index-all-reviews.
    """
    try:
        ingestion_service.index_all_reviews(
            db,
            user_id=user_id,
            repository_id=repository_id,
        )
    except Exception as exc:
        logger.warning(
            "Best-effort indexing after import failed",
            extra={
                "repository_id": repository_id,
                "error": str(exc),
            },
        )

@router.post(
    "/repositories",
    response_model=RepositoryResponse,
)
def create_repository(
    repository: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.create_repository(
        repository,
        db,
        user_id=current_user.id,
    )


@router.get(
    "/repositories",
    response_model=list[RepositoryResponse],
)
def get_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, gt=0, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.get_repositories(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/repositories/{repository_id}",
    response_model=RepositoryResponse,
)
def get_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.get_owned_repository_or_404(
        repository_id,
        current_user.id,
        db,
    )


@router.put(
    "/repositories/{repository_id}",
    response_model=RepositoryResponse,
)
def update_repository(
    repository_id: int,
    repository_update: RepositoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.update_repository(
        repository_id,
        repository_update,
        db,
        user_id=current_user.id,
    )


@router.delete("/repositories/{repository_id}")
def delete_repository(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.delete_repository(
        repository_id,
        db,
        user_id=current_user.id,
    )


@router.get("/github/{owner}/{repo}")
def fetch_github_repository(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
):
    return github_service.get_repository_details(
        owner,
        repo,
    )


@router.post(
    "/repositories/import/{owner}/{repo}",
    response_model=RepositoryResponse,
)
def import_repository(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return repository_service.import_repository_from_github(
        owner,
        repo,
        db,
        user_id=current_user.id,
    )


@router.post(
    "/repositories/import/{owner}/{repo}/pull-requests",
)
def import_pull_requests(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repository_service.get_owned_repository_or_404_by_owner_name(
        owner,
        repo,
        current_user.id,
        db,
    )

    imported_count = pull_request_service.import_repository_pull_requests(
        owner,
        repo,
        db,
    )

    return {
        "message": "Pull requests imported successfully.",
        "imported_count": imported_count,
    }


@router.post(
    "/repositories/import/{owner}/{repo}/reviews",
)
def import_reviews(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    repository = repository_service.get_owned_repository_or_404_by_owner_name(
        owner,
        repo,
        current_user.id,
        db,
    )

    imported_count = review_service.import_pull_request_reviews(
        owner,
        repo,
        db,
    )

    _index_imported_repository_best_effort(
        ingestion_service,
        db,
        current_user.id,
        repository.id,
    )

    return {
        "message": "Reviews imported successfully.",
        "imported_count": imported_count,
    }


@router.post(
    "/repositories/import/{owner}/{repo}/review-comments",
)
def import_review_comments(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    repository = repository_service.get_owned_repository_or_404_by_owner_name(
        owner,
        repo,
        current_user.id,
        db,
    )

    imported_count = review_service.import_pull_request_review_comments(
        owner,
        repo,
        db,
    )

    _index_imported_repository_best_effort(
        ingestion_service,
        db,
        current_user.id,
        repository.id,
    )

    return {
        "message": "Review comments imported successfully.",
        "imported_count": imported_count,
    }


@router.post(
    "/repositories/import",
    response_model=RepositoryImportResponse,
)
def import_repository_from_url(
    request: RepositoryImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Import a GitHub repository using its URL.

    Example:
    https://github.com/openai/openai-python
    """

    owner, repo = repository_service.parse_github_repository_url(request.url)

    repository = repository_service.import_repository_from_github(
        owner,
        repo,
        db,
        user_id=current_user.id,
    )

    return {
        "success": True,
        "message": "Repository imported successfully.",
        "repository": repository,
    }
