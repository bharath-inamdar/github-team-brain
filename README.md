# TeamBrain

TeamBrain is an AI-powered GitHub knowledge assistant. It imports repository
metadata, pull requests, and pull request reviews from GitHub, stores structured
data in PostgreSQL, indexes review text in ChromaDB, and uses Google Gemini to
answer engineering questions and generate repository summaries.

## Features

- Import GitHub repository metadata.
- Import pull requests and pull request reviews.
- Persist repository data with FastAPI, SQLAlchemy, and PostgreSQL.
- Generate embeddings for useful review comments with Gemini.
- Store and query review embeddings in ChromaDB.
- Ask natural-language questions over indexed review feedback.
- Generate a Markdown engineering summary for the repository.
- React and TailwindCSS frontend for summary generation.

## Architecture

```mermaid
flowchart LR
    UI[React + TypeScript Frontend] --> API[FastAPI API]
    API --> DB[(PostgreSQL)]
    API --> GH[GitHub REST API]
    API --> AI[Google Gemini API]
    API --> VS[ChromaDB]
    GH --> API
    DB --> API
    API --> AI
    AI --> API
    API --> VS
    VS --> API
    API --> UI
```

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL
- Vector store: ChromaDB
- AI: Google Gemini API
- Frontend: React, TypeScript, Vite, TailwindCSS
- Tests: pytest

## Folder Structure

```text
.
├── api/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── clients/          # External API clients
│   │   ├── core/             # Application configuration
│   │   ├── routers/          # FastAPI routes
│   │   ├── services/         # Business logic
│   │   ├── database.py       # SQLAlchemy engine/session
│   │   ├── models.py         # SQLAlchemy models
│   │   └── schemas.py        # Pydantic schemas
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       └── services/
├── tests/                    # pytest unit tests
├── docker-compose.yml
└── .env.example
```

## Installation

1. Create environment files.

```bash
cp .env.example api/.env
cp .env.example frontend/.env.local
```

2. Start PostgreSQL and ChromaDB.

```bash
docker compose up -d
```

3. Install and run the backend.

```bash
cd api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

4. Install and run the frontend.

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Backend variables are read by `api/app/core/config.py`.

```env
APP_NAME=GitHub Team Brain API
APP_VERSION=1.0.0
DEBUG=True
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/github_team_brain
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REQUEST_TIMEOUT_SECONDS=15
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=models/gemini-3.6-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=teambrain
```

Frontend variables:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## API Endpoints

- `GET /api/v1/health` - service health check
- `POST /api/v1/repositories` - create a repository record
- `GET /api/v1/repositories` - list repositories
- `GET /api/v1/repositories/{repository_id}` - get a repository
- `PUT /api/v1/repositories/{repository_id}` - update a repository
- `DELETE /api/v1/repositories/{repository_id}` - delete a repository
- `GET /api/v1/github/{owner}/{repo}` - preview GitHub repository metadata
- `POST /api/v1/repositories/import/{owner}/{repo}` - import repository metadata
- `POST /api/v1/repositories/import/{owner}/{repo}/pull-requests` - import pull requests
- `POST /api/v1/repositories/import/{owner}/{repo}/reviews` - import pull request reviews
- `GET /api/v1/ai/embedding-test` - verify Gemini embeddings
- `GET /api/v1/ai/chroma-test` - verify ChromaDB connection
- `POST /api/v1/ai/index-review` - index one review
- `POST /api/v1/ai/index-all-reviews` - index all useful reviews
- `GET /api/v1/ai/search?question=...` - search similar review comments
- `GET /api/v1/ai/ask?question=...` - answer a repository question
- `GET /api/v1/ai/repository-summary` - generate a repository summary

`/api/v1/ai/search` and `/api/v1/ai/ask` also accept an optional
`repository_id` query parameter to scope retrieval.

## RAG Workflow

1. Import repository metadata from GitHub.
2. Import pull requests for that repository.
3. Import pull request reviews.
4. Filter out empty, very short, bot-generated, and low-signal review text.
5. Generate Gemini embeddings for useful review comments.
6. Store review text, embeddings, and metadata in ChromaDB.
7. Embed the user's question.
8. Retrieve similar reviews from ChromaDB.
9. Ask Gemini to answer using only the retrieved review context.

## Testing

Run backend unit tests from the repository root:

```bash
pytest
```

Run frontend checks from `frontend/`:

```bash
npm run lint
npm run build
```

## Future Improvements

- Add authentication for mutating and AI-costing endpoints.
- Add rate limiting for GitHub and Gemini calls.
- Add CI/CD checks for tests, linting, and migrations.
- Add deployment configuration for production environments.
- Add background jobs for long-running imports and indexing.
- Add API-level integration tests with disposable PostgreSQL and ChromaDB.
- Add observability dashboards and request tracing.
