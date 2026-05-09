from httpx import AsyncClient

from tests.conftest import auth_headers_for

LONG_CONTENT = (
    "Python developer with extensive experience in building web applications " * 5
).strip()


async def test_create_resume(client: AsyncClient):
    headers = await auth_headers_for(client)
    resp = await client.post(
        "/api/v1/resumes",
        json={"title": "My Resume", "content": LONG_CONTENT},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "My Resume"
    assert data["content"] == LONG_CONTENT
    assert data["id"]
    assert data["user_id"]


async def test_list_resumes_pagination(client: AsyncClient):
    headers = await auth_headers_for(client)
    for i in range(3):
        await client.post(
            "/api/v1/resumes",
            json={"title": f"Resume {i}", "content": LONG_CONTENT},
            headers=headers,
        )

    resp = await client.get("/api/v1/resumes", params={"page": 1, "per_page": 2}, headers=headers)
    assert resp.status_code == 200
    page = resp.json()["data"]
    assert len(page["items"]) == 2
    assert page["total"] == 3
    assert page["has_next"] is True
    assert page["has_prev"] is False


async def test_get_resume(client: AsyncClient):
    headers = await auth_headers_for(client)
    create_resp = await client.post(
        "/api/v1/resumes",
        json={"title": "Fetch Me", "content": LONG_CONTENT},
        headers=headers,
    )
    rid = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/resumes/{rid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Fetch Me"


async def test_update_resume(client: AsyncClient):
    headers = await auth_headers_for(client)
    create_resp = await client.post(
        "/api/v1/resumes",
        json={"title": "Old Title", "content": LONG_CONTENT},
        headers=headers,
    )
    rid = create_resp.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/resumes/{rid}",
        json={"title": "New Title"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "New Title"
    assert resp.json()["data"]["content"] == LONG_CONTENT


async def test_delete_resume_soft_delete(client: AsyncClient):
    headers = await auth_headers_for(client)
    create_resp = await client.post(
        "/api/v1/resumes",
        json={"title": "Delete Me", "content": LONG_CONTENT},
        headers=headers,
    )
    rid = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/resumes/{rid}", headers=headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/resumes/{rid}", headers=headers)
    assert get_resp.status_code == 404


async def test_cross_user_isolation(client: AsyncClient):
    headers_a = await auth_headers_for(client, email="a@example.com", full_name="User A")
    headers_b = await auth_headers_for(client, email="b@example.com", full_name="User B")

    create_resp = await client.post(
        "/api/v1/resumes",
        json={"title": "Private", "content": LONG_CONTENT},
        headers=headers_a,
    )
    rid = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/resumes/{rid}", headers=headers_b)
    assert resp.status_code == 404
