from fastapi import FastAPI
from app.routers.health import router as health_router
from app.core.config import settings
from app.database import engine
from app.models import Base,Repository
from fastapi import Depends
from sqlalchemy.orm import Session
from app.schemas import RepositoryCreate

from app.database import get_db

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
def root(db: Session = Depends(get_db)):
    return {
        "message": "GitHub Team Brain API",
        "database": "Connected"
    }


@app.post("/repositories")
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
@app.get("/repositories")
def get_repositories(db: Session = Depends(get_db)):
    repositories = db.query(Repository).all()

    return repositories