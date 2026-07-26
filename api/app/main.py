from fastapi import FastAPI

from app.routers.health import router as health_router
from app.routers.repositories import router as repositories_router

from app.core.config import settings
from app.database import engine, get_db
from app.models import Base

from fastapi import Depends
from sqlalchemy.orm import Session


# Create all database tables
Base.metadata.create_all(bind=engine)

# Create the FastAPI application.
# Every incoming request starts here.
app = FastAPI(
    title=settings.app_name,
    description="Backend API for GitHub Team Brain",
    version=settings.app_version,
)

# Register Health routes
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"]
)

# Register Repository routes
app.include_router(
    repositories_router,
    prefix="/api/v1",
    tags=["Repositories"]
)


@app.get("/")
def root(db: Session = Depends(get_db)):
    return {
        "message": "GitHub Team Brain API",
        "database": "Connected"
    }

print("GitHub Token Loaded:", settings.github_token is not None)