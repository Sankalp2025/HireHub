# Testing - HireHub API

HireHub's backend tests are integration-heavy because the highest-risk behavior is in API contracts, authentication, user data isolation, persistence, and analysis scoring.

## Stack

- `pytest`
- `pytest-asyncio`
- `httpx.AsyncClient` with `ASGITransport`
- PostgreSQL test database
- Alembic migrations for schema setup
- Ruff for linting

SQLite is intentionally avoided because the application uses PostgreSQL-specific `JSONB` columns.

## Database Safety

Tests use `TEST_DATABASE_URL`. The test harness copies this value into `DATABASE_URL` before importing the app so the app and Alembic point at the same isolated database.

The default local test URL is:

```bash
postgresql+asyncpg://hirehub:hirehub_dev@localhost:5432/hirehub_test
```

The test harness refuses to run unless the database URL contains `_test`. This is a guardrail because the fixture truncates application tables before and after each test.

## Local Setup

Install dependencies from the backend directory:

```bash
pip install -r requirements.txt
```

Create a test database if it does not already exist:

```bash
createdb hirehub_test
```

If your local Postgres credentials differ, export a test URL:

```bash
export TEST_DATABASE_URL="postgresql+asyncpg://hirehub:hirehub_dev@localhost:5432/hirehub_test"
```

Run the suite:

```bash
cd backend
pytest tests/
```

The test session runs `alembic upgrade head` automatically, overrides FastAPI's `get_db` dependency, and truncates these tables around every test:

- `analysis_results`
- `job_descriptions`
- `resumes`
- `refresh_tokens`
- `users`

## Expected Results

A healthy run should report all tests passing across:

- health endpoint envelope
- registration and login
- Swagger token endpoint
- refresh-token rotation, invalid-token handling, expiration, inactive-user handling, concurrency, and logout
- resume CRUD and user isolation
- job description CRUD, nullable field clearing, and user isolation
- analysis creation, pagination, validation, snapshots, and user isolation
- PDF resume upload and text extraction
- Alembic migration health
- skill extractor scoring, category grouping, frequency ranking, and property-based score bounds

Run linting separately:

```bash
cd backend
ruff check .
```

## CI

GitHub Actions starts a PostgreSQL service, installs `backend/requirements.txt`, runs Ruff, and then runs `pytest tests/`.

The CI database is `hirehub_test`, which satisfies the test harness guardrail.

## Good Next Tests To Add

- validation response envelopes for every router
- deletion side effects, especially analyses whose source resume or job description is later soft-deleted
- CORS behavior for the frontend origin
- refresh-token cleanup behavior for old revoked or expired tokens
- analysis scoring regression tests using realistic resume/JD fixtures
