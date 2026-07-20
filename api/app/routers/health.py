from fastapi import APIRouter

# APIRouter groups related endpoints together.
router = APIRouter()


@router.get("/health")
def health_check():
    """
    Simple health endpoint.

    Used to verify that the API is running correctly.
    """
    return {
        "status": "healthy"
    }