# HireHub

HireHub is a resume and job description analysis platform. Users can register, save resumes, save job descriptions, run a match analysis, and review saved analysis history.

## Current Status

The backend MVP is working end-to-end.

Implemented so far:
- Dockerized FastAPI + PostgreSQL local setup
- Health check endpoint with real database connectivity check
- SQLAlchemy models and Alembic migrations
- JWT auth with Argon2 password hashing
- Protected resume CRUD endpoints
- Protected job description CRUD endpoints
- Analysis creation and history endpoints
- Snapshot-based analysis persistence

Current backend routes:
- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/resumes`
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

Infrastructure:
- Docker
- Docker Compose

Frontend:
- React + TypeScript is currently planned, but the frontend stack can still change as long as it consumes the backend API.

## Local Setup

Copy the environment template:

```bash
cp .env.example .env
```

Start the app:

```bash
docker compose up --build -d
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

Open the interactive API docs:

```text
http://localhost:8000/docs
```

Stop the app:

```bash
docker compose down
```

To fully reset the local database:

```bash
docker compose down -v
```

## Analysis Approach

The current analysis pipeline is intentionally simple and explainable.

It currently:
- resolves resume and JD input from saved IDs or raw text
- normalizes keywords using regex and lowercase matching
- computes matched and missing keywords
- calculates a percentage-based match score
- generates rule-based suggestions
- stores the full analysis result in PostgreSQL

The backend also stores `resume_snapshot` and `jd_snapshot` inside each analysis result so historical analyses remain stable even if the original resume or job description changes later.

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
    main.py
    security.py
  alembic/
  Dockerfile
  requirements.txt

docs/
docker-compose.yml
.env.example
outline.md
README.md
```

## Notes For Testing

- Protected routes require a bearer token from `POST /api/v1/auth/login`.
- In the current implementation, Swagger's OAuth2 authorize popup does not fully match the custom JSON login route, so protected endpoint testing is easiest with `curl` or Postman.
- `localhost` is the expected host for local testing.
