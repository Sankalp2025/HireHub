# HireHub — Project Outline

> **Day 1 Reference Document**
> Both developers work from this file. The API contract in Section 3 is frozen at end of Day 1 — no changes without agreement from both devs.
> Stretch goals listed later in this document are intentionally out of MVP scope unless both devs agree to pull them in.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [API Contract](#3-api-contract)
4. [Database Schema](#4-database-schema)
5. [Tech Stack](#5-tech-stack)
6. [Project Folder Structure](#6-project-folder-structure)
7. [Development Timeline](#7-development-timeline)
8. [Environment Setup](#8-environment-setup)
9. [Day 1 Checklist](#9-day-1-checklist)
10. [Architectural Rules](#10-architectural-rules)
11. [MVP Scope and Stretch Goals](#11-mvp-scope-and-stretch-goals)
12. [Review Resources by Phase](#12-review-resources-by-phase)

---

## 1. Project Overview

**What it does**: HireHub is a resume and job description (JD) analyzer. An authenticated user submits either raw text or stored resume/JD records; the system returns a quantified match score, a list of skills the resume is missing relative to the JD, and ordered suggestions for improving the resume. In the MVP, analyses are generated with explainable NLP and rule-based scoring, then persisted so users can track how their resumes perform across multiple applications over time.

**Who it is for**: Job seekers who want fast, objective feedback on how well a specific resume version targets a specific role — without waiting on a recruiter.

**Key value propositions**:
- Instant 0–100 match score between resume and JD
- Specific skill gap list derived from NLP analysis rather than keyword matching alone
- Concrete, ranked suggestions for resume improvement
- History dashboard: every analysis saved, searchable, and comparable
- Self-hostable: open-source NLP stack, no external AI API dependency in the MVP

---

## 2. System Architecture

```
Browser (React / TypeScript)
          |
          |  HTTPS REST (JSON)
          v
   FastAPI  (Python 3.12)
          |                \
          |  SQLAlchemy     \  in-process function call
          v                  v
   PostgreSQL 16         Analysis Layer
   (users, resumes,      spaCy 3.7 + rule-based scoring
    JDs, analyses)       (semantic similarity can be added later)
```

**Key decisions**:
- Frontend never talks to the database. It calls the API and receives JSON.
- Analysis runs in-process inside FastAPI for the MVP. If it becomes a bottleneck later, it can be extracted behind the same service interface.
- JWTs are signed access tokens. Keep auth simple in the MVP: register, login, and `me`.
- All IDs are UUIDs — no sequential integers exposed in the API.
- All timestamps are UTC ISO 8601 (`2026-04-07T12:00:00Z`).
- Resumes and job descriptions use soft deletes. Analysis results may be permanently deleted by the owning user.
- Build an explainable analysis pipeline first. Taxonomies, embeddings, vector search, and background jobs are stretch goals.

---

## 3. API Contract

> **This section is the contract. Both devs agree on it Day 1 and do not change it unilaterally.**
> Frontend builds UI against MSW mock handlers that return data matching these schemas exactly.
> Backend implements the real logic behind these schemas.

**Frontend partner note**: React + TypeScript is the current plan, but the frontend stack is not locked. If the frontend stack changes, the important requirement is that it still consumes this HTTP API contract and keeps request/response shapes aligned with the backend. Early frontend work can use mocked responses from this section while the backend endpoints are still being implemented.

**Base URL**: `http://localhost:8000/api/v1`

**Response envelope** — every endpoint wraps its payload:
```json
{
  "data": <payload or null>,
  "error": { "code": "<ERROR_CODE>", "message": "<human-readable>" } or null
}
```

Error codes are machine-readable uppercase strings (e.g. `EMAIL_ALREADY_REGISTERED`, `INVALID_CREDENTIALS`, `NOT_FOUND`, `FORBIDDEN`). The frontend branches on `error.code`, never on `error.message`.

**Auth header** (all protected routes): `Authorization: Bearer <jwt_token>`

---

### 3.1 Auth

#### `POST /auth/register`
Create a new user account. No auth required.

Request:
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!",
  "full_name": "Jane Doe"
}
```

Response `201`:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "created_at": "2026-04-07T00:00:00Z"
  },
  "error": null
}
```

Errors: `400` `EMAIL_ALREADY_REGISTERED` | `422` `VALIDATION_ERROR`

---

#### `POST /auth/login`
Authenticate and receive a JWT. No auth required.

Request:
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

Response `200`:
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "error": null
}
```

Errors: `401` `INVALID_CREDENTIALS`

---

#### `GET /auth/me`
Returns the currently authenticated user. Protected.

Response `200`:
```json
{
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "created_at": "2026-04-07T00:00:00Z"
  },
  "error": null
}
```

---

### 3.2 Resumes

All resume routes are protected.

#### `POST /resumes`
Store a new resume.

Request:
```json
{
  "title": "Software Engineer Resume v3",
  "content": "Jane Doe\njane@example.com\n\nExperience:\n..."
}
```

Response `201`:
```json
{
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Software Engineer Resume v3",
    "content": "Jane Doe\njane@example.com\n\nExperience:\n...",
    "created_at": "2026-04-07T00:00:00Z",
    "updated_at": "2026-04-07T00:00:00Z"
  },
  "error": null
}
```

---

#### `GET /resumes`
List all resumes for the current user. `content` omitted for performance.

Response `200`:
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Software Engineer Resume v3",
      "created_at": "2026-04-07T00:00:00Z",
      "updated_at": "2026-04-07T00:00:00Z"
    }
  ],
  "error": null
}
```

---

#### `GET /resumes/{resume_id}`
Single resume with full content.

Response `200`: same shape as POST response (includes `content`).
Errors: `404` not found | `403` belongs to another user

---

#### `PATCH /resumes/{resume_id}`
Partial update — title and/or content. At least one field must be present.

Request: `{ "title"?: string, "content"?: string }`
Response `200`: updated resume object (same shape as POST response).

---

#### `DELETE /resumes/{resume_id}`
Soft-delete (sets `deleted_at`).

Response `200`:
```json
{ "data": { "message": "Resume deleted" }, "error": null }
```

---

### 3.3 Job Descriptions

All JD routes are protected. Identical CRUD pattern to Resumes.

#### `POST /job-descriptions`
Request:
```json
{
  "title": "Senior Backend Engineer @ Stripe",
  "company": "Stripe",
  "role": "Senior Backend Engineer",
  "content": "We are looking for a senior backend engineer who..."
}
```

Response `201`:
```json
{
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "title": "Senior Backend Engineer @ Stripe",
    "company": "Stripe",
    "role": "Senior Backend Engineer",
    "content": "We are looking for...",
    "created_at": "2026-04-07T00:00:00Z",
    "updated_at": "2026-04-07T00:00:00Z"
  },
  "error": null
}
```

#### `GET /job-descriptions` — list (no `content`), same pattern as resumes.
#### `GET /job-descriptions/{jd_id}` — full object including `content`.
#### `PATCH /job-descriptions/{jd_id}` — partial update, any of: `title`, `company`, `role`, `content`.
#### `DELETE /job-descriptions/{jd_id}` — soft delete.

---

### 3.4 Analysis (Core Feature)

All analysis routes are protected in the MVP.

#### `POST /analyze`
The primary endpoint. Accepts either raw text (Shape A) or references to stored resources (Shape B). Both shapes are persisted to the authenticated user's analysis history.

**Shape A** — raw text:
```json
{
  "resume_text": "Jane Doe\njane@example.com\n\nExperience:\n...",
  "jd_text": "We are looking for a senior backend engineer who..."
}
```

**Shape B** — stored resource IDs:
```json
{
  "resume_id": "uuid",
  "jd_id": "uuid"
}
```

Response `200`:
```json
{
  "data": {
    "id": "uuid",
    "status": "complete",
    "match_score": 73.4,
    "missing_skills": [
      "Kubernetes",
      "gRPC",
      "Terraform"
    ],
    "suggestions": [
      "Add quantified metrics to your Python experience (e.g., 'reduced latency by 40%')",
      "Include Kubernetes orchestration experience — it appears 5 times in the JD",
      "Mention distributed systems design explicitly in your summary"
    ],
    "keyword_overlap": {
      "matched": ["Python", "FastAPI", "PostgreSQL", "REST API"],
      "unmatched_jd_keywords": ["Kubernetes", "gRPC", "Terraform", "distributed systems"],
      "total_jd_keywords": 18,
      "total_resume_keywords": 22
    },
    "analyzed_at": "2026-04-07T12:00:00Z",
    "resume_id": "uuid or null",
    "jd_id": "uuid or null"
  },
  "error": null
}
```

> **`status` field**: Always `"complete"` in the MVP. It is reserved so that asynchronous processing can be added later without changing the response shape.

Errors: `404` `NOT_FOUND` if resume_id or jd_id not found | `403` `FORBIDDEN` if they belong to another user | `422` `VALIDATION_ERROR` if neither valid shape is provided

---

#### `GET /analyses`
List analysis history for the current user, paginated. Protected.

Query params: `?page=1&per_page=20&sort=analyzed_at:desc`

Response `200`:
```json
{
  "data": {
    "items": [
      {
        "id": "uuid",
        "match_score": 73.4,
        "resume_title": "Software Engineer Resume v3",
        "jd_title": "Senior Backend Engineer @ Stripe",
        "analyzed_at": "2026-04-07T12:00:00Z"
      }
    ],
    "total": 42,
    "page": 1,
    "per_page": 20,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  },
  "error": null
}
```

---

#### `GET /analyses/{analysis_id}`
Full analysis result. Protected.

Response `200`: full analysis object (same shape as `POST /analyze` response data).
Errors: `404` not found | `403` belongs to another user

---

#### `DELETE /analyses/{analysis_id}`
Delete an analysis result. Protected. This is a permanent delete in the MVP.

Response `200`:
```json
{ "data": { "message": "Analysis deleted" }, "error": null }
```

---

### 3.5 Health

#### `GET /health`
No auth required. Used by Docker healthcheck and monitoring.

Response `200`:
```json
{
  "data": {
    "status": "ok",
    "version": "0.1.0",
    "db": "connected",
    "analysis_engine": "ready"
  },
  "error": null
}
```

`analysis_engine` is `"ready"` in the MVP. If the analysis layer fails to initialize, `POST /analyze` should return `503` and `GET /health` can be expanded later to surface degraded status.

---

## 4. Database Schema

PostgreSQL 16. All tables:
- `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` (where applicable)

---

### `users`
```sql
CREATE TABLE users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            TEXT NOT NULL UNIQUE,
    full_name        TEXT NOT NULL,
    hashed_password  TEXT NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_email ON users(email);
```

---

### `resumes`
```sql
CREATE TABLE resumes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL CHECK (char_length(content) BETWEEN 50 AND 50000),
    deleted_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Partial index: only indexes active (non-deleted) rows — smaller and faster than a full index
CREATE INDEX idx_resumes_active ON resumes(user_id) WHERE deleted_at IS NULL;
```

---

### `job_descriptions`
```sql
CREATE TABLE job_descriptions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    company     TEXT,
    role        TEXT,
    content     TEXT NOT NULL CHECK (char_length(content) BETWEEN 50 AND 50000),
    deleted_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_jd_active ON job_descriptions(user_id) WHERE deleted_at IS NULL;
```

---

### `analysis_results`
```sql
CREATE TABLE analysis_results (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id        UUID REFERENCES resumes(id) ON DELETE SET NULL,
    jd_id            UUID REFERENCES job_descriptions(id) ON DELETE SET NULL,
    resume_snapshot  TEXT NOT NULL,   -- raw text copied at analysis time
    jd_snapshot      TEXT NOT NULL,   -- raw text copied at analysis time
    match_score      NUMERIC(5,2) NOT NULL,
    missing_skills   JSONB NOT NULL DEFAULT '[]',
    suggestions      JSONB NOT NULL DEFAULT '[]',
    keyword_overlap  JSONB NOT NULL DEFAULT '{}',
    analyzed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_analysis_user_id ON analysis_results(user_id);
CREATE INDEX idx_analysis_analyzed_at ON analysis_results(analyzed_at DESC);
CREATE INDEX idx_analysis_resume_id ON analysis_results(resume_id);
CREATE INDEX idx_analysis_jd_id ON analysis_results(jd_id);
```

**Why snapshots**: `resume_snapshot` and `jd_snapshot` store the raw text at the moment of analysis. If a user later edits or deletes the stored resume/JD, past analysis results remain accurate and reproducible.

---

## 5. Tech Stack

### Backend

| Package | Version | Purpose |
|---|---|---|
| Python | 3.12 | Current stable; structural pattern matching, perf improvements |
| FastAPI | >=0.115,<0.200 (pin 0.135.3) | Async framework, OpenAPI 3.1, Pydantic v2 native. 0.111 was 24 releases behind and missing OpenAPI 3.1 support. |
| Pydantic | 2.x | Schema validation, serialization, OpenAPI generation |
| SQLAlchemy | 2.x (async) | ORM with `asyncpg` driver; use `sqlalchemy[asyncio]` extra |
| asyncpg | 0.29.x | High-performance async PostgreSQL driver |
| Alembic | 1.13.x | Database migrations, tracked in git |
| PyJWT[crypto] | >=2.10 | JWT encode/decode. Replaces `python-jose` which is unmaintained and has CVEs. FastAPI's own docs now use PyJWT. |
| pwdlib[argon2] | >=0.2 | Password hashing with Argon2id (OWASP recommended). Replaces `passlib[bcrypt]` which is unmaintained and raises deprecation warnings on Python 3.12. |
| spaCy | 3.7.x | NLP: tokenization, noun-chunk extraction, lightweight entity extraction |
| sentence-transformers | 3.x | Optional semantic similarity after the keyword-based MVP is stable |
| httpx | 0.27.x | Async HTTP client (used in tests) |
| pytest + pytest-asyncio | latest | Async test runner |
| uvicorn[standard] | 0.29.x | ASGI server |

### Frontend

| Package | Version | Purpose |
|---|---|---|
| React | 18.x | Concurrent rendering |
| TypeScript | 5.x | Type safety enforced against API contract schemas |
| Vite | 5.x | Fast dev server, ESM-first bundling |
| React Router | 6.x | Client-side routing |
| TanStack Query | 5.x | Server state, caching, loading/error states |
| Axios | 1.x | HTTP client with auth header interceptor |
| Tailwind CSS | 3.x | Utility-first styling |
| shadcn/ui | latest | Accessible component primitives (Radix UI based) |
| Recharts | 2.x | Match score gauge and keyword overlap charts |
| Zod | 3.x | Runtime schema validation mirroring Pydantic schemas |
| MSW (Mock Service Worker) | 2.x | Intercepts fetch/XHR — how frontend runs without a real backend in Weeks 1-2 |
| Vitest + Testing Library | ^2.x (paired with Vite 5) | Unit + component tests. **Pin Vitest and Vite as a matched pair**: Vite 5 + Vitest 2, or Vite 6 + Vitest 4. Mismatching versions breaks `npm test`. |

### Infrastructure

| Tool | Version | Purpose |
|---|---|---|
| PostgreSQL | 16 | JSONB for skills arrays, `gen_random_uuid()` built-in, `TIMESTAMPTZ` |
| Docker + Docker Compose | 26.x | `docker compose up` starts DB + backend + frontend |
| pgAdmin or DBeaver | latest | DB inspection during development |

---

## 6. Project Folder Structure

```
HireHub/
├── docker-compose.yml
├── docker-compose.override.yml        # local dev overrides (volume mounts for hot reload)
├── .env.example                        # committed — no real secrets
├── .env                                # gitignored — real local values
├── .gitignore
├── README.md
│
├── docs/
│   ├── API_CONTRACT.md                 # exported from /openapi.json on Day 1
│   └── ARCHITECTURE.md                 # ASCII or Mermaid architecture diagram
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py                      # configured for async engine + all models
│   │   └── versions/
│   │       └── 0001_initial_schema.py  # all initial tables
│   └── app/
│       ├── main.py                     # FastAPI app factory, CORS, router registration, lifespan
│       ├── config.py                   # Pydantic Settings, reads .env
│       ├── database.py                 # async engine, AsyncSessionLocal, get_db dependency
│       │
│       ├── models/                     # SQLAlchemy ORM models
│       │   ├── __init__.py             # imports all models (required for Alembic autogenerate)
│       │   ├── user.py
│       │   ├── resume.py
│       │   ├── job_description.py
│       │   ├── analysis_result.py
│       │
│       ├── schemas/                    # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── common.py               # APIResponse[T] generic envelope, PaginatedResponse[T]
│       │   ├── auth.py                 # RegisterRequest, LoginRequest, TokenResponse, UserResponse
│       │   ├── resume.py               # ResumeCreate, ResumeUpdate, ResumeResponse, ResumeListItem
│       │   ├── job_description.py      # JDCreate, JDUpdate, JDResponse, JDListItem
│       │   └── analysis.py             # AnalyzeRequest, AnalysisResponse, AnalysisListItem
│       │
│       ├── routers/                    # FastAPI APIRouter, one per domain
│       │   ├── __init__.py
│       │   ├── health.py
│       │   ├── auth.py
│       │   ├── resumes.py
│       │   ├── job_descriptions.py
│       │   └── analyses.py
│       │
│       ├── services/                   # Business logic — no HTTP concerns here
│       │   ├── __init__.py
│       │   ├── auth_service.py         # register, authenticate, hash/verify password
│       │   ├── resume_service.py       # CRUD against DB
│       │   ├── jd_service.py           # CRUD against DB
│       │   ├── analysis_service.py     # orchestrates analysis + writes to DB
│       │   └── nlp_service.py          # text normalization, skill extraction, scoring
│       │
│       ├── dependencies.py             # FastAPI Depends: get_db, get_current_user
│       ├── security.py                 # JWT create/decode helpers
│       └── exceptions.py              # Custom exceptions + global exception handlers
│
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_resumes.py
│       ├── test_job_descriptions.py
│       └── test_analyses.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── router.tsx                  # React Router route definitions
        │
        ├── types/                      # TypeScript interfaces — must match API schemas exactly
        │   ├── api.ts                  # APIResponse<T>, PaginatedResponse<T>
        │   ├── auth.ts                 # RegisterRequest, LoginRequest, TokenResponse, User
        │   ├── resume.ts               # ResumeCreate, ResumeUpdate, Resume, ResumeListItem
        │   ├── jobDescription.ts       # JDCreate, JDUpdate, JobDescription, JDListItem
        │   └── analysis.ts             # AnalyzeRequest, Analysis, AnalysisListItem, KeywordOverlap
        │
        ├── api/                        # Axios instances + typed request functions
        │   ├── client.ts               # axios instance with base URL + auth interceptor
        │   ├── auth.ts
        │   ├── resumes.ts
        │   ├── jobDescriptions.ts
        │   └── analyses.ts
        │
        ├── hooks/                      # TanStack Query hooks wrapping api/ functions
        │   ├── useAuth.ts
        │   ├── useResumes.ts
        │   ├── useJobDescriptions.ts
        │   └── useAnalyses.ts
        │
        ├── components/
        │   ├── ui/                     # shadcn/ui generated (do not hand-edit)
        │   ├── layout/
        │   │   ├── AppShell.tsx        # nav + sidebar wrapper
        │   │   └── AuthLayout.tsx
        │   ├── auth/
        │   │   ├── LoginForm.tsx
        │   │   └── RegisterForm.tsx
        │   ├── resume/
        │   │   ├── ResumeList.tsx
        │   │   ├── ResumeCard.tsx
        │   │   └── ResumeForm.tsx
        │   ├── jd/
        │   │   ├── JDList.tsx
        │   │   ├── JDCard.tsx
        │   │   └── JDForm.tsx
        │   └── analysis/
        │       ├── AnalyzeForm.tsx         # paste text or select stored resume + JD
        │       ├── MatchScoreGauge.tsx     # Recharts gauge displaying match_score
        │       ├── MissingSkillsChips.tsx  # chip list for missing_skills array
        │       ├── SuggestionsList.tsx     # ordered list for suggestions array
        │       └── AnalysisHistoryTable.tsx
        │
        ├── pages/
        │   ├── LoginPage.tsx
        │   ├── RegisterPage.tsx
        │   ├── DashboardPage.tsx
        │   ├── ResumesPage.tsx
        │   ├── JobDescriptionsPage.tsx
        │   ├── AnalyzePage.tsx
        │   └── AnalysisDetailPage.tsx
        │
        ├── mocks/                          # MSW — frontend's mock backend (Weeks 1 + 2)
        │   ├── browser.ts                  # MSW service worker setup
        │   ├── handlers/
        │   │   ├── auth.ts
        │   │   ├── resumes.ts
        │   │   ├── jobDescriptions.ts
        │   │   └── analyses.ts
        │   └── data/                       # Static fixture JSON matching API schemas exactly
        │       ├── users.json
        │       ├── resumes.json
        │       ├── jobDescriptions.json
        │       └── analyses.json
        │
        └── lib/
            ├── queryClient.ts              # TanStack Query client config
            ├── authStore.ts                # Auth state (Zustand or Context)
            └── validators.ts               # Zod schemas mirroring Pydantic schemas
```

---

## 7. Development Timeline

### Week 1 — Skeleton, Database, Contract Lock

**Backend (you)**

| Day | Deliverable |
|---|---|
| 1 | Repo structure, Docker Compose (db + backend), FastAPI skeleton, Alembic + all 4 tables, `GET /health` working |
| 2–3 | Auth endpoints (register, login, me), JWT middleware, password hashing, tests for auth |
| 4–5 | Resume CRUD endpoints, JD CRUD endpoints, service layer pattern, unit tests |

**Frontend (partner)**

| Day | Deliverable |
|---|---|
| 1 | Scaffold Vite/React/TS, configure MSW + Tailwind + shadcn, write TypeScript types from this document |
| 2–3 | Auth pages (login, register) using MSW mock handlers |
| 4–5 | Resume and JD list/detail/create pages using MSW mock handlers |

**End of Week 1 milestone**: Backend has working auth + CRUD. Frontend has complete auth + CRUD UI with no real backend dependency. **API contract is frozen.**

---

### Week 2 — NLP Logic and Frontend Features

**Backend (you)**

| Day | Deliverable |
|---|---|
| 1 | NLP service skeleton: normalize text, extract keywords/skills, and define an explainable scoring rubric |
| 2 | Implement `POST /analyze` for both raw text and stored resource inputs; persist snapshots and results |
| 3 | Implement `GET /analyses`, `GET /analyses/{id}`, and `DELETE /analyses/{id}`; add integration tests for the analysis flow |
| 4–5 | Tune scoring weights, improve suggestions, document the scoring approach in the README, and fix integration issues |

**Frontend (partner)**

| Day | Deliverable |
|---|---|
| 1–2 | Analyze flow UI: paste resume + JD or select from stored list; loading state; results display (score gauge, missing skills chips, suggestions) |
| 3–4 | Analysis history dashboard: list view, pagination, click-to-detail |
| 5 | Polish: error states, empty states, accessibility pass |

---

### Week 3 — Integration, Testing, Deployment

**Joint**

| Day | Deliverable |
|---|---|
| 1 | Point frontend at real backend (swap MSW handlers to passthrough); smoke test every endpoint |
| 2 | Fix any schema mismatches (should be zero if contract was respected) |
| 3 | End-to-end tests (Playwright) covering: register → login → store resume → store JD → analyze → view history |
| 4 | Performance pass: profile the analysis endpoint, verify DB indexes, and polish API errors |
| 5 | Docker production build, final README, demo recording; only then consider stretch goals |

---

## 8. Environment Setup

### `.env.example` (committed to git)
```
# ── Backend ──────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://hirehub:hirehub_dev@db:5432/hirehub
SECRET_KEY=changeme_generate_with_openssl_rand_hex_32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ENVIRONMENT=development
BACKEND_CORS_ORIGINS=["http://localhost:5173"]

# ── PostgreSQL (consumed by docker-compose) ──────────────
POSTGRES_USER=hirehub
POSTGRES_PASSWORD=hirehub_dev
POSTGRES_DB=hirehub

# ── Frontend ─────────────────────────────────────────────
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ENABLE_MOCKS=true
```

Copy `.env.example` to `.env` locally. `.env` is in `.gitignore`.

---

### `docker-compose.yml` (service summary)

**`db`**: `postgres:16-alpine` | port `5432` | healthcheck: `pg_isready -U hirehub -d hirehub`

**`backend`**: builds from `./backend/Dockerfile` | port `8000` | depends on `db` (healthy) | mounts `./backend/app` for hot reload | entrypoint: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

**`frontend`**: builds from `./frontend/Dockerfile` | port `5173` | depends on `backend` | mounts `./frontend/src` for HMR | entrypoint: `npm run dev -- --host`

---

### `backend/requirements.txt` (pinned)
```
fastapi==0.135.3
uvicorn[standard]==0.29.0
pydantic[email]==2.7.1
pydantic-settings==2.3.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pyjwt[crypto]==2.10.1
pwdlib[argon2]==0.2.1
spacy==3.7.4
sentence-transformers==3.0.0
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
```

---

### `frontend/package.json` (key deps)
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.23.0",
    "@tanstack/react-query": "^5.40.0",
    "axios": "^1.7.0",
    "recharts": "^2.12.0",
    "zod": "^3.23.0",
    "msw": "^2.3.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "vitest": "^2.0.0",
    "@testing-library/react": "^16.0.0"
  }
}
```

---

## 9. Day 1 Checklist

### Backend (you) — today

- [ ] Create directory structure per Section 6 (`backend/`, `frontend/`, `docs/`)
- [ ] Write `docker-compose.yml` with `db` and `backend` services
- [ ] Write `.env.example` with all variables from Section 8
- [ ] Write `backend/requirements.txt` with pinned versions (use `pyjwt[crypto]` and `pwdlib[argon2]` — NOT `python-jose` or `passlib`)
- [ ] Write `backend/Dockerfile` (Python 3.12-slim, pip install, uvicorn entrypoint)
- [ ] Scaffold `backend/app/main.py` — FastAPI app, CORS middleware, register all routers, DB lifespan
- [ ] Scaffold `backend/app/config.py` — Pydantic `Settings` reading from `.env`
- [ ] Scaffold `backend/app/database.py` — async engine + `AsyncSessionLocal` + `get_db` dependency
- [ ] Write all 4 SQLAlchemy models under `backend/app/models/`
- [ ] Run `alembic init alembic` and configure `env.py` for async engine + all model imports
- [ ] Write and apply first migration: `alembic revision --autogenerate -m "initial_schema"` then `alembic upgrade head`
- [ ] Confirm all 4 tables exist in PostgreSQL
- [ ] Implement `GET /health` — confirm `{"data":{"status":"ok","db":"connected","analysis_engine":"ready"},"error":null}` returns from `http://localhost:8000/api/v1/health`
- [ ] Write `backend/app/schemas/common.py` — `APIResponse[T]` and `PaginatedResponse[T]` generics
- [ ] Write skeleton router files for all domains — each route returns `501 Not Implemented` with a TODO comment
- [ ] Confirm FastAPI auto-docs at `http://localhost:8000/docs` shows all planned endpoints with correct schemas
- [ ] Export and share `http://localhost:8000/openapi.json` with frontend partner

### Frontend (partner) — today

- [ ] `npm create vite@latest frontend -- --template react-ts` inside the monorepo
- [ ] Install all packages from `package.json` above
- [ ] Configure Tailwind CSS and shadcn/ui
- [ ] Write all TypeScript types in `src/types/` — must match every schema in Section 3 field-for-field (note: resume/JD update endpoints are `PATCH`, not `PUT`; analysis response includes `status` and `keyword_overlap.unmatched_jd_keywords`; there is no logout endpoint in the MVP)
- [ ] Set up MSW: `npx msw init public/`, create `src/mocks/browser.ts`, write stub handlers for every endpoint returning fixture JSON
- [ ] Set up React Router with all page routes defined (page components can be blank stubs)
- [ ] Set up TanStack Query `queryClient.ts`
- [ ] Set up Axios `client.ts` with base URL from `VITE_API_BASE_URL` and auth header interceptor
- [ ] Confirm `npm run dev` starts without errors and MSW is active (browser console shows `[MSW] Mocking enabled`)

### Joint — end of Day 1

- [ ] Backend shares `openapi.json` with frontend partner
- [ ] Frontend partner validates MSW handler response shapes against `openapi.json` field-for-field
- [ ] Both devs confirm TypeScript types in `src/types/` match Pydantic schemas in `backend/app/schemas/`
- [ ] **API contract declared FROZEN** — no endpoint changes until Week 3 integration begins without explicit agreement from both devs

---

## 10. Architectural Rules

These belong in the project README. Treat them as invariants.

1. **API contract first.** No endpoint is implemented before its Pydantic schema (`backend/app/schemas/`) and TypeScript type (`frontend/src/types/`) both exist and agree.

2. **Snapshots in analysis_results.** Always copy `resume_snapshot` and `jd_snapshot` at analysis time. A user editing or deleting a stored resume must never change the output of a past analysis.

3. **No raw SQL.** All database access goes through SQLAlchemy ORM in `services/`. All schema changes go through Alembic migrations.

4. **No business logic in routers.** Routers handle HTTP concerns: parse the request body, call a service function, return the response. Services own all logic.

5. **Frontend never reads the database.** Not even in tests. MSW is the only mock layer — the frontend test suite never imports SQLAlchemy, asyncpg, or any database driver.

6. **UUID everywhere.** No sequential integer IDs in any public-facing API field. All IDs are UUIDs generated server-side.

7. **Soft deletes for user-authored source records.** `deleted_at IS NOT NULL` means deleted for `resumes` and `job_descriptions`. Analysis results may be permanently deleted by the owner.

8. **UTC only.** All timestamps stored as `TIMESTAMPTZ` in PostgreSQL and returned as ISO 8601 strings with a `Z` suffix (`2026-04-07T12:00:00Z`). No naive datetimes anywhere.

9. **MVP first.** Build an explainable analysis pipeline using normalization, keyword/skill extraction, overlap scoring, and rule-based suggestions before attempting embeddings, taxonomies, or background jobs.

10. **Stretch goals never block integration.** ESCO, sentence-transformer tuning, caching, pgvector, and Celery are optional enhancements and only begin after the full core flow works end-to-end.

---

## 11. MVP Scope and Stretch Goals

### Must Build (MVP)

- FastAPI app structure with routers, services, models, and schemas
- PostgreSQL schema + Alembic migrations
- Auth: `register`, `login`, `me`
- Resume CRUD
- Job description CRUD
- `POST /analyze`
- `GET /analyses`
- `GET /analyses/{id}`
- `DELETE /analyses/{id}`
- Analysis persistence with resume/JD snapshots
- Explainable scoring rubric and rule-based suggestions
- Basic automated tests
- Dockerized local development setup
- README that explains architecture and scoring

### Should Build If Time Allows

- Pagination polish on analysis history
- Stronger validation and ownership checks
- Better keyword normalization and suggestion quality
- Additional integration tests
- More polished health reporting for the analysis layer

### Stretch Goals (Post-MVP)

- ESCO skill taxonomy integration
- Sentence-transformer semantic similarity
- Hash-based analysis caching
- pgvector embedding storage and retrieval
- Background jobs with Celery
- Public anonymous analysis endpoint with rate limiting
- Token revocation/blocklist logout
- Advanced analytics or benchmarking views

---

## 12. Review Resources by Phase

Use these just before the phase where they matter. Do not try to study everything up front.

### Before Week 1 (App Structure, DB, Migrations)

- FastAPI app structure: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/
- Pydantic settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- SQLAlchemy 2.0 unified tutorial: https://docs.sqlalchemy.org/20/tutorial/
- SQLAlchemy asyncio support: https://docs.sqlalchemy.org/20/orm/extensions/asyncio.html
- Alembic tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Docker Compose quickstart: https://docs.docker.com/compose/gettingstarted/

### Before Auth Work

- FastAPI JWT auth flow: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- PyJWT usage examples: https://pyjwt.readthedocs.io/en/stable/usage.html
- pwdlib password hashing guide: https://frankie567.github.io/pwdlib/guide/

### Before CRUD Endpoints

- FastAPI response models: https://fastapi.tiangolo.com/tutorial/response-model/
- FastAPI CORS: https://fastapi.tiangolo.com/tutorial/cors/
- PostgreSQL UUID type: https://www.postgresql.org/docs/current/datatype-uuid.html
- PostgreSQL JSON/JSONB: https://www.postgresql.org/docs/current/datatype-json.html

### Before Analysis Week

- spaCy processing pipelines: https://spacy.io/usage/processing-pipelines
- spaCy models and languages: https://spacy.io/usage/models
- Sentence-transformers semantic similarity: https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html

### Before Testing and Integration

- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- pytest fixtures: https://docs.pytest.org/en/stable/explanation/fixtures.html
- HTTPX transports and ASGI testing: https://www.python-httpx.org/advanced/transports/

### Only If Stretch Goals Start

- ESCO overview and usage: https://esco.ec.europa.eu/en/use-esco
