import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router

from app.core.config import settings

from app.routers.health import router as health_router
from app.routers.repositories import router as repositories_router
from app.routers.ai import router as ai_router

from app.services.ai_service import RateLimitError
from app.services.auth_service import ensure_bootstrap_admin

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the application starts.
    """
    ensure_bootstrap_admin()
    yield


# Create the FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for GitHub Team Brain",
    version=settings.app_version,
    lifespan=lifespan,
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


@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(
    request: Request,
    exc: RateLimitError,
):
    """
    Translates AI provider rate limits into a clean 429 response with a
    Retry-After header instead of a raw 500.
    """
    headers = {}

    if exc.retry_after_seconds is not None:
        headers["Retry-After"] = str(
            max(1, round(exc.retry_after_seconds))
        )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": (
                "AI provider rate limit exceeded. "
                "Please retry shortly."
            ),
        },
        headers=headers,
    )

# Register Health routes
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["Health"],
)

# Register Auth routes
app.include_router(
    auth_router,
    prefix="/api/v1",
    tags=["Auth"],
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