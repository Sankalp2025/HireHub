import os

import pytest
from httpx import AsyncClient


@pytest.mark.smoke
async def test_running_backend_health_smoke():
    if os.environ.get("RUN_SMOKE_TESTS") != "1":
        pytest.skip("Set RUN_SMOKE_TESTS=1 to run live backend smoke tests.")

    base_url = os.environ.get("SMOKE_BASE_URL", "http://localhost:8000")
    async with AsyncClient(base_url=base_url) as client:
        resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ok"
