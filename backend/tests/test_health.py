from httpx import AsyncClient


async def test_health_envelope_shape(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert "db" in body["data"]
