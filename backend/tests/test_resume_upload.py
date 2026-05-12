import fitz
from httpx import AsyncClient

from tests.conftest import auth_headers_for

LONG_CONTENT = (
    "Python developer with extensive experience in building web applications " * 5
).strip()


def _make_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


async def test_upload_pdf_success(client: AsyncClient):
    headers = await auth_headers_for(client)
    pdf_bytes = _make_pdf(LONG_CONTENT)

    resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Uploaded Resume"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "Uploaded Resume"
    assert "Python developer" in data["content"]
    assert data["id"]
    assert data["user_id"]


async def test_upload_non_pdf_rejected(client: AsyncClient):
    headers = await auth_headers_for(client)

    resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", b"some text content", "text/plain")},
        data={"title": "Bad Upload"},
        headers=headers,
    )
    assert resp.status_code == 422
    assert "PDF" in resp.json()["error"]["message"]


async def test_upload_invalid_pdf_bytes_rejected(client: AsyncClient):
    headers = await auth_headers_for(client)

    resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", b"this is not really a pdf", "application/pdf")},
        data={"title": "Invalid PDF"},
        headers=headers,
    )
    assert resp.status_code == 422
    assert "valid PDF" in resp.json()["error"]["message"]


async def test_upload_empty_pdf_rejected(client: AsyncClient):
    headers = await auth_headers_for(client)
    pdf_bytes = _make_pdf("")

    resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("empty.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Empty PDF"},
        headers=headers,
    )
    assert resp.status_code == 422
    assert "sufficient text" in resp.json()["error"]["message"]


async def test_upload_oversized_file_rejected(client: AsyncClient):
    headers = await auth_headers_for(client)
    oversized = b"%PDF-" + b"\x00" * (6 * 1024 * 1024)

    resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("big.pdf", oversized, "application/pdf")},
        data={"title": "Big PDF"},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_upload_requires_auth(client: AsyncClient):
    pdf_bytes = _make_pdf(LONG_CONTENT)

    resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={"title": "No Auth"},
    )
    assert resp.status_code == 401


async def test_upload_missing_title(client: AsyncClient):
    headers = await auth_headers_for(client)
    pdf_bytes = _make_pdf(LONG_CONTENT)

    resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 422
