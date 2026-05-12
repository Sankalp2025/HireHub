from httpx import AsyncClient

from tests.conftest import auth_headers_for
from tests.factories import LONG_JD_CONTENT, job_description_payload
from tests.helpers import assert_error_envelope, assert_success_envelope

LONG_CONTENT = LONG_JD_CONTENT


async def test_create_job_description(client: AsyncClient):
    headers = await auth_headers_for(client)
    resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(title="Backend Engineer", content=LONG_CONTENT),
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "Backend Engineer"
    assert data["company"] == "Acme"
    assert data["role"] == "Senior"


async def test_list_job_descriptions_pagination(client: AsyncClient):
    headers = await auth_headers_for(client)
    for i in range(3):
        await client.post(
            "/api/v1/job-descriptions",
            json=job_description_payload(
                title=f"JD {i}",
                company=None,
                role=None,
                content=LONG_CONTENT,
            ),
            headers=headers,
        )

    resp = await client.get(
        "/api/v1/job-descriptions",
        params={"page": 1, "per_page": 2},
        headers=headers,
    )
    assert resp.status_code == 200
    page = resp.json()["data"]
    assert len(page["items"]) == 2
    assert page["total"] == 3
    assert page["has_next"] is True


async def test_list_job_descriptions_empty_page(client: AsyncClient):
    headers = await auth_headers_for(client)

    resp = await client.get("/api/v1/job-descriptions", headers=headers)

    assert resp.status_code == 200
    page = assert_success_envelope(resp)
    assert page["items"] == []
    assert page["total"] == 0
    assert page["total_pages"] == 0
    assert page["has_next"] is False
    assert page["has_prev"] is False


async def test_list_job_descriptions_rejects_invalid_per_page(client: AsyncClient):
    headers = await auth_headers_for(client)

    resp = await client.get(
        "/api/v1/job-descriptions",
        params={"per_page": 0},
        headers=headers,
    )

    error = assert_error_envelope(resp, 422)
    assert error["code"] == "validation_error"


async def test_update_job_description(client: AsyncClient):
    headers = await auth_headers_for(client)
    create_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="Original",
            company="OldCo",
            role="Junior",
            content=LONG_CONTENT,
        ),
        headers=headers,
    )
    jd_id = create_resp.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/job-descriptions/{jd_id}",
        json={"title": "Updated"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Updated"
    assert resp.json()["data"]["company"] == "OldCo"


async def test_clear_job_description_company(client: AsyncClient):
    headers = await auth_headers_for(client)
    create_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="Original",
            company="OldCo",
            role="Senior",
            content=LONG_CONTENT,
        ),
        headers=headers,
    )
    jd_id = create_resp.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/job-descriptions/{jd_id}",
        json={"company": None},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["company"] is None
    assert resp.json()["data"]["role"] == "Senior"


async def test_delete_job_description(client: AsyncClient):
    headers = await auth_headers_for(client)
    create_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="Delete Me",
            company=None,
            role=None,
            content=LONG_CONTENT,
        ),
        headers=headers,
    )
    jd_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/job-descriptions/{jd_id}", headers=headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/job-descriptions/{jd_id}", headers=headers)
    assert get_resp.status_code == 404


async def test_cross_user_isolation(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    create_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="Private JD",
            company=None,
            role=None,
            content=LONG_CONTENT,
        ),
        headers=headers_a,
    )
    jd_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/job-descriptions/{jd_id}", headers=headers_b)
    assert resp.status_code == 404


async def test_cross_user_cannot_update_job_description(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    create_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="Private JD",
            company=None,
            role=None,
            content=LONG_CONTENT,
        ),
        headers=headers_a,
    )
    jd_id = create_resp.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/job-descriptions/{jd_id}",
        json={"title": "Stolen JD"},
        headers=headers_b,
    )
    assert resp.status_code == 404

    owner_resp = await client.get(f"/api/v1/job-descriptions/{jd_id}", headers=headers_a)
    assert owner_resp.status_code == 200
    assert owner_resp.json()["data"]["title"] == "Private JD"


async def test_cross_user_cannot_delete_job_description(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    create_resp = await client.post(
        "/api/v1/job-descriptions",
        json=job_description_payload(
            title="Private JD",
            company=None,
            role=None,
            content=LONG_CONTENT,
        ),
        headers=headers_a,
    )
    jd_id = create_resp.json()["data"]["id"]

    resp = await client.delete(f"/api/v1/job-descriptions/{jd_id}", headers=headers_b)
    assert resp.status_code == 404

    owner_resp = await client.get(f"/api/v1/job-descriptions/{jd_id}", headers=headers_a)
    assert owner_resp.status_code == 200
