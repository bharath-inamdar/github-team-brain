from fastapi import FastAPI

# Create the FastAPI application.
# Every incoming request starts here.
app = FastAPI(
    title="GitHub Team Brain API",
    description="Backend API for GitHub Team Brain",
    version="1.0.0",
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