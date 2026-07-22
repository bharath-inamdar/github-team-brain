from fastapi import FastAPI
from app.routers.health import router as health_router
from app.core.config import settings
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)
# Create the FastAPI application.
# Every incoming request starts here.
app = FastAPI(
    title=settings.app_name,
    description="Backend API for GitHub Team Brain",
    version=settings.app_version,
)

app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"]
)
@app.get("/")
def root():
    """
    Health-check endpoint.

    We use this to verify that the API server is running.
    """
    return {
        "message": "Fuck you Niggaums"
    }