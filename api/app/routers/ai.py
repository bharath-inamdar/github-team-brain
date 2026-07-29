from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_service import AIService
from app.services.vector_service import VectorService
from app.services.ingestion_service import IngestionService

router = APIRouter()

ai_service = AIService()
vector_service = VectorService()


@router.get("/ai/embedding-test")
def test_embedding():
    """
    Generate an embedding using Gemini and verify it works.
    """
    embedding = ai_service.generate_embedding(
        "FastAPI is a modern Python web framework."
    )

    return {
        "dimensions": len(embedding),
        "first_10_values": embedding[:10],
    }


@router.get("/ai/chroma-test")
def test_chromadb():
    """
    Verify ChromaDB connection.
    """
    return {
        "collection_name": vector_service.collection.name,
        "document_count": vector_service.collection.count(),
        "status": "Connected to ChromaDB successfully!",
    }


@router.post("/ai/index-review")
def index_review(
    db: Session = Depends(get_db),
):
    """
    Index the first pull request review from PostgreSQL into ChromaDB.
    """
    ingestion_service = IngestionService()

    result = ingestion_service.index_first_review(db)

    return {
        "message": result,
    }


@router.get("/ai/search")
def search_reviews(
    question: str,
):
    """
    Search similar pull request reviews.
    """

    ingestion_service = IngestionService()

    results = ingestion_service.search_reviews(
        question
    )

    return results


@router.post("/ai/index-all-reviews")
def index_all_reviews(
    db: Session = Depends(get_db),
):
    """
    Index all pull request reviews into ChromaDB.
    """

    ingestion_service = IngestionService()

    result = ingestion_service.index_all_reviews(db)

    return result

@router.get("/ai/ask")
def ask_repository(
    question: str,
):
    """
    Ask TeamBrain a question about the repository.
    """

    ingestion_service = IngestionService()

    result = ingestion_service.ask_repository(
        question
    )

    return result

@router.get("/ai/repository-summary")
def repository_summary(
    db: Session = Depends(get_db),
):
    ingestion_service = IngestionService()

    return ingestion_service.summarize_repository(
        db=db,
    )