from httpx import AsyncClient

from tests.conftest import auth_headers_for

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
        json={"resume_text": RESUME_TEXT, "jd_text": JD_TEXT},
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
        json={"title": "Test Resume", "content": RESUME_TEXT},
        headers=headers,
    )
    resume_id = resume_resp.json()["data"]["id"]

    jd_resp = await client.post(
        "/api/v1/job-descriptions",
        json={"title": "Test JD", "content": JD_TEXT},
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
        json={"resume_text": RESUME_TEXT, "jd_text": JD_TEXT},
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


async def test_list_analyses_pagination(client: AsyncClient):
    headers = await auth_headers_for(client)
    for _ in range(3):
        await client.post(
            "/api/v1/analyses",
            json={"resume_text": RESUME_TEXT, "jd_text": JD_TEXT},
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


async def test_cross_user_isolation(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    create_resp = await client.post(
        "/api/v1/analyses",
        json={"resume_text": RESUME_TEXT, "jd_text": JD_TEXT},
        headers=headers_a,
    )
    analysis_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/analyses/{analysis_id}", headers=headers_b)
    assert resp.status_code == 404


async def test_422_on_short_text(client: AsyncClient):
    headers = await auth_headers_for(client)
    resp = await client.post(
        "/api/v1/analyses",
        json={"resume_text": "too short", "jd_text": "too short"},
        headers=headers,
    )
    assert resp.status_code == 422
