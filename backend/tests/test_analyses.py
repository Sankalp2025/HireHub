from httpx import AsyncClient

from tests.conftest import auth_headers_for
from tests.factories import analysis_raw_payload, job_description_payload, resume_payload
from tests.helpers import assert_error_envelope, assert_success_envelope

RESUME_TEXT = (
    "Experienced Python developer with expertise in FastAPI, SQLAlchemy, PostgreSQL, "
    "Docker, and REST API design. Built scalable microservices handling high traffic. "
    "Strong background in software engineering best practices and agile methodologies. "
) * 3

JD_TEXT = (
    "We need a senior Python developer proficient in FastAPI, PostgreSQL, Docker, "
    "Kubernetes, and CI/CD pipelines. Experience with microservices architecture "
    "and cloud platforms like AWS is required for our growing engineering team. "
) * 3


async def test_create_analysis_with_raw_text(client: AsyncClient):
    headers = await auth_headers_for(client)
    resp = await client.post(
        "/api/v1/analyses",
        json=analysis_raw_payload(resume_text=RESUME_TEXT, jd_text=JD_TEXT),
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert "match_score" in data
    assert "missing_skills" in data
    assert "suggestions" in data
    assert "keyword_overlap" in data
    assert data["resume_id"] is None
    assert data["jd_id"] is None


async def test_create_analysis_with_saved_ids(client: AsyncClient):
    headers = await auth_headers_for(client)

    resume_resp = await client.post(
        "/api/v1/resumes",
        json=resume_payload(title="Test Resume", content=RESUME_TEXT),
        headers=headers,
    )
    resume_id = resume_resp.json()["data"]["id"]

    jd_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="Test JD",
            company=None,
            role=None,
            content=JD_TEXT,
        ),
        headers=headers,
    )
    jd_id = jd_resp.json()["data"]["id"]

    resp = await client.post(
        "/api/v1/analyses",
        json={"resume_id": resume_id, "jd_id": jd_id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["resume_id"] == resume_id
    assert data["jd_id"] == jd_id


async def test_analysis_response_fields(client: AsyncClient):
    headers = await auth_headers_for(client)
    resp = await client.post(
        "/api/v1/analyses",
        json=analysis_raw_payload(resume_text=RESUME_TEXT, jd_text=JD_TEXT),
        headers=headers,
    )
    data = resp.json()["data"]
    assert float(data["match_score"]) >= 0
    assert float(data["match_score"]) <= 100

    ko = data["keyword_overlap"]
    assert "matched" in ko
    assert "missing" in ko
    assert "matched_count" in ko
    assert "total_jd_keywords" in ko
    assert "score_weights" in ko
    assert "keyword_score" in ko["score_weights"]
    assert "cosine_similarity_score" in ko["score_weights"]
    assert "category_breakdown" in ko
    assert "hard_skill" in ko["category_breakdown"]
    assert {"matched", "missing", "total", "score"} <= set(
        ko["category_breakdown"]["hard_skill"]
    )


async def test_list_analyses_pagination(client: AsyncClient):
    headers = await auth_headers_for(client)
    for _ in range(3):
        await client.post(
            "/api/v1/analyses",
            json=analysis_raw_payload(resume_text=RESUME_TEXT, jd_text=JD_TEXT),
            headers=headers,
        )

    resp = await client.get(
        "/api/v1/analyses",
        params={"page": 1, "per_page": 2},
        headers=headers,
    )
    assert resp.status_code == 200
    page = resp.json()["data"]
    assert len(page["items"]) == 2
    assert page["total"] == 3
    assert page["has_next"] is True


async def test_list_analyses_empty_page(client: AsyncClient):
    headers = await auth_headers_for(client)

    resp = await client.get("/api/v1/analyses", headers=headers)

    assert resp.status_code == 200
    page = assert_success_envelope(resp)
    assert page["items"] == []
    assert page["total"] == 0
    assert page["total_pages"] == 0
    assert page["has_next"] is False
    assert page["has_prev"] is False


async def test_list_analyses_rejects_invalid_page(client: AsyncClient):
    headers = await auth_headers_for(client)

    resp = await client.get("/api/v1/analyses", params={"page": 0}, headers=headers)

    error = assert_error_envelope(resp, 422)
    assert error["code"] == "validation_error"


async def test_cross_user_isolation(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    create_resp = await client.post(
        "/api/v1/analyses",
        json=analysis_raw_payload(resume_text=RESUME_TEXT, jd_text=JD_TEXT),
        headers=headers_a,
    )
    analysis_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/analyses/{analysis_id}", headers=headers_b)
    assert resp.status_code == 404


async def test_cannot_analyze_with_another_users_resume(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    resume_resp = await client.post(
        "/api/v1/resumes",
        json=resume_payload(title="A Resume", content=RESUME_TEXT),
        headers=headers_a,
    )
    resume_id = resume_resp.json()["data"]["id"]

    resp = await client.post(
        "/api/v1/analyses",
        json={"resume_id": resume_id, "jd_text": JD_TEXT},
        headers=headers_b,
    )

    assert resp.status_code == 404


async def test_cannot_analyze_with_another_users_job_description(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    jd_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="A JD",
            company=None,
            role=None,
            content=JD_TEXT,
        ),
        headers=headers_a,
    )
    jd_id = jd_resp.json()["data"]["id"]

    resp = await client.post(
        "/api/v1/analyses",
        json={"resume_text": RESUME_TEXT, "jd_id": jd_id},
        headers=headers_b,
    )

    assert resp.status_code == 404


async def test_analysis_remains_fetchable_after_source_resume_update(client: AsyncClient):
    headers = await auth_headers_for(client)

    resume_resp = await client.post(
        "/api/v1/resumes",
        json=resume_payload(title="Resume", content=RESUME_TEXT),
        headers=headers,
    )
    resume_id = resume_resp.json()["data"]["id"]

    jd_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(title="JD", company=None, role=None, content=JD_TEXT),
        headers=headers,
    )
    jd_id = jd_resp.json()["data"]["id"]

    analysis_resp = await client.post(
        "/api/v1/analyses",
        json={"resume_id": resume_id, "jd_id": jd_id},
        headers=headers,
    )
    assert analysis_resp.status_code == 201
    original_score = analysis_resp.json()["data"]["match_score"]
    analysis_id = analysis_resp.json()["data"]["id"]

    updated_text = (
        "Customer support specialist with retail operations and scheduling experience. "
        * 4
    )
    update_resp = await client.patch(
        f"/api/v1/resumes/{resume_id}",
        json={"content": updated_text},
        headers=headers,
    )
    assert update_resp.status_code == 200

    fetched = await client.get(f"/api/v1/analyses/{analysis_id}", headers=headers)
    assert fetched.status_code == 200
    data = fetched.json()["data"]
    assert data["resume_id"] == resume_id
    assert data["jd_id"] == jd_id
    assert data["match_score"] == original_score


async def test_422_on_short_text(client: AsyncClient):
    headers = await auth_headers_for(client)
    resp = await client.post(
        "/api/v1/analyses",
        json={"resume_text": "too short", "jd_text": "too short"},
        headers=headers,
    )
    assert resp.status_code == 422
