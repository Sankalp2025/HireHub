from httpx import AsyncClient

from app.routers import health


async def test_health_envelope_shape(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert "db" in body["data"]


async def test_health_returns_503_when_database_is_disconnected(
    client: AsyncClient,
    monkeypatch,
):
    class DisconnectedEngine:
        def connect(self):
            raise ConnectionError("database unavailable")

    monkeypatch.setattr(health, "engine", DisconnectedEngine())

    resp = await client.get("/api/v1/health")

    assert resp.status_code == 503
    body = resp.json()
    assert body["error"] is None
    assert body["data"] == {
        "status": "unavailable",
        "db": "disconnected",
        "analysis_engine": "ready",
    }
