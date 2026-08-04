import logging

import chromadb
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.database import engine

# APIRouter groups related endpoints together.
router = APIRouter()

logger = logging.getLogger(__name__)


def _check_postgres() -> str:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "healthy"
    except Exception:
        logger.exception("PostgreSQL health check failed")
        return "unhealthy"


def _check_chromadb() -> str:
    try:
        client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
        client.list_collections()
        return "healthy"
    except Exception:
        logger.exception("ChromaDB health check failed")
        return "unhealthy"


def _check_gemini() -> str:
    return "healthy" if settings.gemini_api_key else "unhealthy"


@router.get("/health")
def health_check():
    """
    Simple readiness endpoint.

    Used to verify that the API and its external dependencies are available.
    """
    postgres_status = _check_postgres()
    chromadb_status = _check_chromadb()
    gemini_status = _check_gemini()

    return {
        "status": (
            "healthy"
            if all(
                status == "healthy"
                for status in (
                    postgres_status,
                    chromadb_status,
                    gemini_status,
                )
            )
            else "unhealthy"
        ),
        "postgres": postgres_status,
        "chromadb": chromadb_status,
        "gemini": gemini_status,
    }