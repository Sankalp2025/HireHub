# HireHub

HireHub is a resume and job description analysis platform. Users can register, save resumes, save job descriptions, run a match analysis, and review saved analysis history.

![HireHub backend demo](docs/media/hirehub-demo.gif)

The demo runs the real FastAPI authentication and analysis flow against an
isolated PostgreSQL database, then presents an explainable resume-job alignment
score with category coverage, matched terms, skill gaps, and suggestions.

```bash
make demo
```

[Watch the MP4 version](docs/media/hirehub-demo.mp4) or read the
[demo details](demo/README.md).

## Current Status

The backend MVP is working end-to-end.

Implemented so far:
- Dockerized FastAPI + PostgreSQL local setup
- Health check endpoint with real database connectivity check
- SQLAlchemy models and Alembic migrations (auto-run on container start)
- JWT auth with Argon2 password hashing
- Refresh token rotation and logout
- Swagger-compatible OAuth2 token endpoint
- Protected resume CRUD endpoints
- Protected PDF resume upload endpoint
- Protected job description CRUD endpoints
- Analysis creation and history endpoints with explainable category-weighted scoring
- Snapshot-based analysis persistence
- Paginated list endpoints with configurable page size
- Rate limiting on auth endpoints (10/minute per IP)
- Consistent API error envelope across all endpoints
- CORS middleware for frontend integration
- Integration, unit, property, migration, and smoke test coverage
- Ruff linting, pre-commit hooks, and GitHub Actions CI

Current backend routes:
- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/resumes`
- `POST /api/v1/resumes/upload`
- `GET /api/v1/resumes`
- `GET /api/v1/resumes/{id}`
- `PATCH /api/v1/resumes/{id}`
- `DELETE /api/v1/resumes/{id}`
- `POST /api/v1/job-descriptions`
- `GET /api/v1/job-descriptions`
- `GET /api/v1/job-descriptions/{id}`
- `PATCH /api/v1/job-descriptions/{id}`
- `DELETE /api/v1/job-descriptions/{id}`
- `POST /api/v1/analyses`
- `GET /api/v1/analyses`
- `GET /api/v1/analyses/{id}`

## Tech Stack

Backend:
- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy async
- asyncpg
- Alembic
- PostgreSQL
- PyJWT
- pwdlib / Argon2
- SlowAPI (rate limiting)
- scikit-learn (TF-IDF analysis)
- PyMuPDF (PDF resume text extraction)

Tooling:
- Ruff (linting and formatting)
- pre-commit
- pytest + pytest-asyncio
- GitHub Actions CI

Infrastructure:
- Docker
- Docker Compose

Frontend:
- A React + TypeScript frontend built by a collaborator is in progress on the `frontend` branch and consumes this backend API.

## Local Setup

Copy the environment template:

```bash
cp .env.example .env
```

Start the app:

```bash
docker compose up --build -d
```

Database migrations run automatically on backend container start
(via `backend/entrypoint.sh`, which runs `alembic upgrade head`
before launching uvicorn). No manual migration step is needed for
local setup.

To create a new migration after changing models:

```bash
docker compose exec backend alembic revision --autogenerate -m "your message"
```

Check container status:

```bash
docker compose ps
```

Test the backend health endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "data": {
    "status": "ok",
    "db": "connected",
    "analysis_engine": "ready"
  },
  "error": null
}
```

Open the interactive API docs (Swagger UI supports OAuth2 login via the Authorize button):

```text
http://localhost:8000/docs
```

The frontend-facing API contract is summarized in:

```text
docs/API.md
```

Stop the app:

```bash
docker compose down
```

To fully reset the local database:

```bash
docker compose down -v
```

## Running Tests

Tests run against a dedicated `hirehub_test` database (auto-created if it doesn't exist).

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

The test suite requires a running PostgreSQL instance on `localhost:5432`. Start just the database with:

```bash
docker compose up -d db
```

Normal local and CI test runs exclude the smoke test unless `RUN_SMOKE_TESTS=1` is set.

## Linting

```bash
cd backend
ruff check .
ruff format .
```

Pre-commit hooks run ruff automatically on staged files:

```bash
pre-commit install
```

## Analysis Approach

The analysis pipeline produces an explainable resume-job alignment score from
category-weighted skill coverage. Hard skills and domain terms carry more weight
than generic fallback keywords. TF-IDF cosine similarity remains visible as a
lexical diagnostic, but it does not currently affect the headline score.

It currently:
- resolves resume and JD input from saved IDs or raw text
- normalizes terms using curated skill phrases, known skill aliases, regex cleanup, and stopword filtering
- groups missing terms by category such as hard skills, soft skills, domain terms, and fallback keywords
- ranks missing terms by job-description frequency
- calculates TF-IDF cosine similarity as a separate lexical diagnostic
- produces a category-weighted final score with a transparent breakdown
- generates rule-based suggestions
- stores the full analysis result in PostgreSQL

The backend stores `resume_snapshot` and `jd_snapshot` inside each analysis result so historical analyses remain stable even if the original resume or job description changes later.

## Project Structure

```text
backend/
  app/
    models/
    routers/
    schemas/
    services/
    config.py
    database.py
    dependencies.py
    limiter.py
    main.py
    security.py
  alembic/
  tests/
  Dockerfile
  entrypoint.sh
  pyproject.toml
  pytest.ini
  requirements.txt

.github/workflows/ci.yml
.pre-commit-config.yaml
docker-compose.yml
.env.example
README.md
```
