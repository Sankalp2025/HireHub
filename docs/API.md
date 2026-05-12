# HireHub Backend API Contract

Base URL for local development:

```text
http://localhost:8000/api/v1
```

All successful JSON endpoints use this envelope unless noted:

```json
{
  "data": {},
  "error": null
}
```

Error responses use the same shape:

```json
{
  "data": null,
  "error": {
    "code": "http_404",
    "message": "Resource not found"
  }
}
```

Protected endpoints require:

```text
Authorization: Bearer <access_token>
```

## Health

`GET /health`

Example response:

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

## Auth

`POST /auth/register`

Request:

```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "Example User"
}
```

Response data:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Example User",
  "created_at": "2026-05-12T12:00:00Z"
}
```

`POST /auth/login`

Request:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response data:

```json
{
  "access_token": "jwt_access_token",
  "refresh_token": "opaque_refresh_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

`GET /auth/me`

Response data:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Example User",
  "created_at": "2026-05-12T12:00:00Z"
}
```

`POST /auth/refresh`

Request:

```json
{
  "refresh_token": "opaque_refresh_token"
}
```

Response data uses the same shape as `POST /auth/login`.

`POST /auth/logout`

Request:

```json
{
  "refresh_token": "opaque_refresh_token"
}
```

Response: `204 No Content`

## Pagination

List endpoints support:

```text
?page=1&per_page=20
```

Paginated response data:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 20,
  "total_pages": 0,
  "has_next": false,
  "has_prev": false
}
```

## Resumes

`POST /resumes`

Request:

```json
{
  "title": "Backend Resume",
  "content": "Resume text with at least 50 characters..."
}
```

Response data:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Backend Resume",
  "content": "Resume text with at least 50 characters...",
  "created_at": "2026-05-12T12:00:00Z",
  "updated_at": "2026-05-12T12:00:00Z"
}
```

`POST /resumes/upload`

Request: multipart form data with:

- `file`: PDF file, max 5 MB
- `title`: resume title

Response data uses the same shape as `POST /resumes`.

`GET /resumes`

Response data uses the pagination shape with resume objects in `items`.

`GET /resumes/{id}`

Response data uses the resume shape.

`PATCH /resumes/{id}`

Request supports partial updates:

```json
{
  "title": "Updated Resume",
  "content": "Updated resume text with at least 50 characters..."
}
```

Response data uses the resume shape.

`DELETE /resumes/{id}`

Response: `204 No Content`

## Job Descriptions

`POST /job-descriptions`

Request:

```json
{
  "title": "Backend Engineer",
  "company": "Example Company",
  "role": "Backend Engineer",
  "content": "Job description text with at least 50 characters..."
}
```

`company` and `role` can be `null` or omitted.

Response data:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Backend Engineer",
  "company": "Example Company",
  "role": "Backend Engineer",
  "content": "Job description text with at least 50 characters...",
  "created_at": "2026-05-12T12:00:00Z",
  "updated_at": "2026-05-12T12:00:00Z"
}
```

`GET /job-descriptions`

Response data uses the pagination shape with job description objects in `items`.

`GET /job-descriptions/{id}`

Response data uses the job description shape.

`PATCH /job-descriptions/{id}`

Request supports partial updates:

```json
{
  "title": "Updated Job Description",
  "company": null,
  "role": "Platform Engineer",
  "content": "Updated job description text with at least 50 characters..."
}
```

Response data uses the job description shape.

`DELETE /job-descriptions/{id}`

Response: `204 No Content`

## Analyses

`POST /analyses`

Use saved resume and job description IDs:

```json
{
  "resume_id": "uuid",
  "jd_id": "uuid"
}
```

Or use raw text:

```json
{
  "resume_text": "Resume text with at least 50 characters...",
  "jd_text": "Job description text with at least 50 characters..."
}
```

Mixed input is also supported, such as `resume_id` with `jd_text`.

Response data:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "resume_id": "uuid",
  "jd_id": "uuid",
  "match_score": "72.35",
  "missing_skills": ["kubernetes", "cloud deployment"],
  "suggestions": [
    "Add evidence of these role-specific skills if you have them: kubernetes, cloud deployment.",
    "Tailor your summary and experience bullets to the target job description."
  ],
  "keyword_overlap": {
    "matched": ["python", "fastapi", "postgresql"],
    "missing": ["kubernetes", "cloud deployment"],
    "missing_term_frequency": {
      "kubernetes": 2,
      "cloud deployment": 1
    },
    "matched_count": 3,
    "total_jd_keywords": 5,
    "keyword_score": "64.29",
    "cosine_similarity_score": "87.31",
    "score_weights": {
      "keyword_score": "0.65",
      "cosine_similarity_score": "0.35"
    },
    "missing_by_category": {
      "hard_skill": ["kubernetes"],
      "domain_term": ["cloud deployment"]
    },
    "category_breakdown": {
      "hard_skill": {
        "matched": 3,
        "missing": 1,
        "total": 4,
        "score": "75.00"
      }
    }
  },
  "analyzed_at": "2026-05-12T12:00:00Z"
}
```

`GET /analyses`

Response data uses the pagination shape with analysis objects in `items`.

`GET /analyses/{id}`

Response data uses the analysis shape.

## Frontend Notes

Use `POST /auth/login` for JSON login from the app. Swagger UI uses a hidden form-compatible endpoint internally.

The configured local frontend origin is:

```text
http://localhost:5173
```

Do not include a trailing slash in the origin value.
