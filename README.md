# HireHub

HireHub is a resume and job description analyzer. Users will be able to store resumes, store job descriptions, run a match analysis, and view previous analysis results.

## Current Status

Backend foundation is in progress.

Currently implemented:
- Docker Compose setup
- PostgreSQL container
- FastAPI backend container
- Basic FastAPI app
- Environment variable setup
- Health endpoint at `/api/v1/health`

Not implemented yet:
- Auth
- Database models
- Alembic migrations
- Resume CRUD
- Job description CRUD
- Analysis logic

## Tech Stack

Backend:
- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy async
- asyncpg
- Alembic
- PostgreSQL

Infrastructure:
- Docker
- Docker Compose

Frontend:
- React + TypeScript is currently planned, but the frontend stack can still change as long as it consumes the agreed backend API.

## Local Setup

Copy the environment template:

```bash
cp .env.example .env
```

Start the app:

```bash
docker compose up --build -d
```

Test the backend:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "data": {
    "status": "ok",
    "db": "not_checked",
    "analysis_engine": "ready"
  },
  "error": null
}
```

Stop the app:

```bash
docker compose down
```

## Project Structure

```text
backend/
  app/
    __init__.py
    main.py
    config.py
    database.py
  Dockerfile
  requirements.txt

docker-compose.yml
.env.example
outline.md
```

## Next Backend Steps

- Add a real database health check
- Create SQLAlchemy models
- Set up Alembic
- Create the first migration
- Build auth endpoints
