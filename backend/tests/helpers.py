from httpx import Response


def assert_success_envelope(response: Response) -> dict:
    body = response.json()
    assert "data" in body
    assert "error" in body
    assert body["error"] is None
    assert body["data"] is not None
    return body["data"]


def assert_error_envelope(response: Response, status_code: int) -> dict:
    assert response.status_code == status_code
    body = response.json()
    assert body["data"] is None
    assert body["error"] is not None
    assert "code" in body["error"]
    assert "message" in body["error"]
    return body["error"]
