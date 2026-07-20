from fastapi import FastAPI
from app.routers.health import router as health_router

# Create the FastAPI application.
# Every incoming request starts here.
app = FastAPI(
    title="GitHub Team Brain API",
    description="Backend API for GitHub Team Brain",
    version="1.0.0",
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