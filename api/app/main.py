import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.dashboard import router as dashboard_router

from app.core.config import settings

from app.routers.health import router as health_router
from app.routers.repositories import router as repositories_router
from app.routers.ai import router as ai_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for GitHub Team Brain",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Health routes
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"],
)

# Register Repository routes
app.include_router(
    repositories_router,
    prefix="/api/v1",
    tags=["Repositories"],
)

# Register AI routes
app.include_router(
    ai_router,
    prefix="/api/v1",
    tags=["AI"],
)


@app.get("/")
def root():
    return {
        "message": "GitHub Team Brain API",
        "database": "Connected",
    }


logger.info(
    "Application configured",
    extra={"github_token_configured": settings.github_token is not None},
)

app.include_router(
    dashboard_router,
    prefix="/api/v1",
    tags=["Dashboard"],
)