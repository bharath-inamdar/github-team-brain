# GitHub TeamBrain

GitHub TeamBrain is an AI-powered repository intelligence dashboard. It imports GitHub repositories, pull requests, reviews, and inline review comments, stores structured data in PostgreSQL, indexes useful review evidence in ChromaDB, and uses Gemini for grounded Q&A and repository summaries.

## Architecture

```mermaid
flowchart LR
    UI[React + TypeScript + Vite] --> API[FastAPI Routers]
    API --> Services[Service Layer]
    Services --> DB[(PostgreSQL)]
    Services --> Chroma[(ChromaDB)]
    Services --> GitHub[GitHub REST API]
    Services --> Gemini[Google Gemini]
    Gemini --> Services
    Chroma --> Services
    DB --> Services
    Services --> API
    API --> UI
```

## What It Does

- Imports repository metadata from a GitHub URL.
- Syncs pull requests, PR reviews, and inline review comments.
- Filters low-signal comments before embedding.
- Indexes review bodies and inline review comments in ChromaDB.
- Answers questions with source citations from retrieved evidence.
- Generates Markdown engineering summaries by repository.
- Provides a SaaS-style React dashboard with overview stats, import progress, chat, evidence cards, and summary regeneration.

## Tech Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, Lucide icons
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic
- Data: PostgreSQL, ChromaDB
- AI: Google Gemini text generation and embeddings
- Tooling: Docker Compose, pytest, npm build

## Setup

Create environment files:

```bash
cp .env.example .env
cp .env.example api/.env
cp .env.example frontend/.env
```

Set these values before running imports or AI endpoints:

```env
JWT_SECRET=your_long_random_jwt_secret
BOOTSTRAP_ADMIN_EMAIL=admin@teambrain.local
BOOTSTRAP_ADMIN_PASSWORD=your_strong_admin_password
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5433/github_team_brain
CHROMA_HOST=localhost
CHROMA_PORT=8001
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Run the full stack:

```bash
docker compose up --build
```

Services:

- Frontend: http://127.0.0.1:5173
- API: http://127.0.0.1:8000
- PostgreSQL: 127.0.0.1:5433
- ChromaDB: http://127.0.0.1:8001

Run locally without Docker:

```bash
docker compose up -d postgres chromadb
cd api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## API Overview

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/health`
- `GET /api/v1/dashboard/overview`
- `GET /api/v1/repositories`
- `POST /api/v1/repositories/import`
- `POST /api/v1/repositories/import/{owner}/{repo}/pull-requests`
- `POST /api/v1/repositories/import/{owner}/{repo}/reviews`
- `POST /api/v1/repositories/import/{owner}/{repo}/review-comments`
- `POST /api/v1/ai/index-all-reviews`
- `GET /api/v1/ai/search?question=...&repository_id=...`
- `GET /api/v1/ai/ask?question=...&repository_id=...`
- `GET /api/v1/ai/repository-summary?repository_id=...`

## Authentication

All endpoints except `/health` and `/auth/register` and `/auth/login` require a JWT Bearer token:

1. Register or log in:
   ```http
   POST /api/v1/auth/register
   Content-Type: application/json

   {"email": "you@example.com", "password": "your_password"}
   ```
   ```http
   POST /api/v1/auth/login
   Content-Type: application/x-www-form-urlencoded

   username=you@example.com&password=your_password
   ```
2. Use the returned `access_token` on every protected request:
   ```http
   Authorization: Bearer <access_token>
   ```

Repositories are private to the user who imports them. Dashboard statistics,
repository CRUD, and all AI/RAG operations (search, ask, summaries, and
knowledge indexing) are scoped to the authenticated user's repositories.
Indexing never touches another user's repositories.

### Existing database data

The `0003_repository_user_id` migration assigns every pre-existing repository
to the bootstrap admin account (`BOOTSTRAP_ADMIN_EMAIL`). Set
`BOOTSTRAP_ADMIN_PASSWORD` before the first application start so that account
can be logged into. The password is only ever read from the environment and is
never stored in source code or migrations.

## RAG Workflow

1. Import repository metadata from GitHub.
2. Sync pull requests.
3. Sync PR review bodies.
4. Sync inline PR review comments.
5. Filter empty, very short, bot-like, or approval-only text.
6. Embed useful review bodies and inline comments.
7. Upsert documents into ChromaDB with repository, reviewer, PR, file, and line metadata.
8. Retrieve semantically similar documents for a question.
9. Ask Gemini to answer only from retrieved evidence and cite source numbers.

If retrieval is empty for Ask TeamBrain, the API indexes available database review material once and retries retrieval before answering.

## Testing

Backend:

```bash
.venv/bin/pytest
```

Frontend:

```bash
cd frontend
npm run build
```

## Screenshots

Add screenshots of the dashboard, import flow, Ask TeamBrain chat, and AI summary here after running the app locally.
