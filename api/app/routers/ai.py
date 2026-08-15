from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    AIChromaTestResponse,
    AIAskRepositoryResponse,
    AIEmbeddingTestResponse,
    AIIndexAllReviewsResponse,
    AIMessageResponse,
    AIRepositorySummaryResponse,
    AISearchReviewsResponse,
)
from app.services import repository_service
from app.services.ai_service import AIService
from app.services.vector_service import VectorService
from app.services.ingestion_service import (
    IngestionService,
    NOT_INDEXED_MESSAGE,
    RepositoryNotIndexedError,
)

router = APIRouter()


def get_ai_service() -> AIService:
    return AIService()


def get_vector_service() -> VectorService:
    return VectorService()


def get_ingestion_service() -> IngestionService:
    return IngestionService()


def _require_debug_mode() -> None:
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )


def _resolve_repository_ids(
    repository_id: int | None,
    user_id: int,
    db: Session,
) -> list[int] | None:
    """
    Resolve the repository ids a user is allowed to query.

    If a repository_id is supplied, ownership is verified first. Otherwise
    the ids resolve to every repository owned by the authenticated user,
    guaranteeing RAG queries never cross user boundaries.
    """
    if repository_id is not None:
        repository_service.get_owned_repository_or_404(
            repository_id,
            user_id,
            db,
        )

        return [repository_id]

    repository_ids = repository_service.get_user_repository_ids(
        db,
        user_id,
    )

    return repository_ids or None


def get_owned_repository_ids(
    repository_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[int] | None:
    """
    FastAPI dependency that verifies repository ownership before any
    external service (ChromaDB, Gemini) is contacted.
    """
    return _resolve_repository_ids(
        repository_id,
        current_user.id,
        db,
    )


@router.get(
    "/ai/embedding-test",
    include_in_schema=False,
    response_model=AIEmbeddingTestResponse,
)
def test_embedding(
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """
    Generate an embedding using Gemini and verify it works.
    """
    _require_debug_mode()

    embedding = ai_service.generate_embedding(
        "FastAPI is a modern Python web framework."
    )

    return {
        "dimensions": len(embedding),
        "first_10_values": embedding[:10],
    }


@router.get(
    "/ai/chroma-test",
    include_in_schema=False,
    response_model=AIChromaTestResponse,
)
def test_chromadb(
    current_user: User = Depends(get_current_user),
    vector_service: VectorService = Depends(get_vector_service),
):
    """
    Verify ChromaDB connection.
    """
    _require_debug_mode()

    return {
        "collection_name": vector_service.collection.name,
        "document_count": vector_service.collection.count(),
        "status": "Connected to ChromaDB successfully!",
    }


@router.post("/ai/index-review", response_model=AIMessageResponse)
def index_review(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Index the first pull request review owned by the authenticated
    user from PostgreSQL into ChromaDB.
    """
    result = ingestion_service.index_first_review(
        db,
        user_id=current_user.id,
    )

    return {
        "message": result,
    }


@router.get("/ai/search", response_model=AISearchReviewsResponse)
def search_reviews(
    question: str,
    repository_ids: list[int] | None = Depends(get_owned_repository_ids),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Search similar pull request reviews within the repositories
    owned by the authenticated user.
    """
    results = ingestion_service.search_reviews(
        question,
        repository_ids=repository_ids,
    )

    return results


@router.post("/ai/index-all-reviews", response_model=AIIndexAllReviewsResponse)
def index_all_reviews(
    repository_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Index pull request reviews into ChromaDB.

    When a repository_id is supplied only that repository is indexed
    (after verifying ownership). Otherwise every repository owned by the
    authenticated user is indexed. Reviews from other users' repositories
    are never indexed.
    """
    if repository_id is not None:
        repository_service.get_owned_repository_or_404(
            repository_id,
            current_user.id,
            db,
        )

    result = ingestion_service.index_all_reviews(
        db,
        user_id=current_user.id,
        repository_id=repository_id,
    )

    return result


@router.get("/ai/ask", response_model=AIAskRepositoryResponse)
def ask_repository(
    question: str,
    repository_ids: list[int] | None = Depends(get_owned_repository_ids),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Ask TeamBrain a question about a repository owned by the
    authenticated user.

    Read-only: answering never triggers indexing. Repositories that have
    not been indexed yet return a 409 instructing the user to index first.
    """
    try:
        result = ingestion_service.ask_repository(
            question,
            repository_ids=repository_ids,
        )
    except RepositoryNotIndexedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=NOT_INDEXED_MESSAGE,
        )

    return result


@router.get("/ai/repository-summary", response_model=AIRepositorySummaryResponse)
def repository_summary(
    repository_ids: list[int] | None = Depends(get_owned_repository_ids),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Generate a repository summary from evidence owned by the
    authenticated user.
    """
    return ingestion_service.summarize_repository(
        db=db,
        user_id=current_user.id,
        repository_id=(
            repository_ids[0]
            if repository_ids
            else None
        ),
    )
