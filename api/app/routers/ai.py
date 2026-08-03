from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.core.security import verify_api_key
from app.schemas import (
    AIChromaTestResponse,
    AIAskRepositoryResponse,
    AIEmbeddingTestResponse,
    AIIndexAllReviewsResponse,
    AIMessageResponse,
    AIRepositorySummaryResponse,
    AISearchReviewsResponse,
)
from app.services.ai_service import AIService
from app.services.vector_service import VectorService
from app.services.ingestion_service import IngestionService

router = APIRouter(dependencies=[Depends(verify_api_key)])


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


@router.get(
    "/ai/embedding-test",
    include_in_schema=False,
    response_model=AIEmbeddingTestResponse,
)
def test_embedding(
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
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Index the first pull request review from PostgreSQL into ChromaDB.
    """
    result = ingestion_service.index_first_review(db)

    return {
        "message": result,
    }


@router.get("/ai/search", response_model=AISearchReviewsResponse)
def search_reviews(
    question: str,
    repository_id: int | None = None,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Search similar pull request reviews.
    """

    results = ingestion_service.search_reviews(
        question,
        repository_id=repository_id,
    )

    return results


@router.post("/ai/index-all-reviews", response_model=AIIndexAllReviewsResponse)
def index_all_reviews(
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Index all pull request reviews into ChromaDB.
    """

    result = ingestion_service.index_all_reviews(db)

    return result

@router.get("/ai/ask", response_model=AIAskRepositoryResponse)
def ask_repository(
    question: str,
    repository_id: int | None = None,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    """
    Ask TeamBrain a question about the repository.
    """

    result = ingestion_service.ask_repository(
        question,
        repository_id=repository_id,
    )

    return result

@router.get("/ai/repository-summary", response_model=AIRepositorySummaryResponse)
def repository_summary(
    db: Session = Depends(get_db),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    return ingestion_service.summarize_repository(
        db=db,
    )
