import fitz
import pytest

from app.utils.pdf import extract_text_from_pdf, normalize_extracted_text

SAMPLE_TEXT = (
    "Python developer with extensive experience in building web applications " * 5
).strip()


def _make_pdf(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_extract_text_single_page():
    pdf_bytes = _make_pdf([SAMPLE_TEXT])
    result = extract_text_from_pdf(pdf_bytes)
    assert "Python developer" in result
    assert len(result) > 50


def test_extract_text_multipage():
    pdf_bytes = _make_pdf(["Page one content here.", "Page two content here."])
    result = extract_text_from_pdf(pdf_bytes)
    assert "Page one" in result
    assert "Page two" in result


def test_extract_text_empty_pdf():
    pdf_bytes = _make_pdf([""])
    result = extract_text_from_pdf(pdf_bytes)
    assert result == ""


def test_extract_text_invalid_bytes():
    with pytest.raises(ValueError, match="not a valid PDF"):
        extract_text_from_pdf(b"this is not a pdf at all")


def test_normalize_extracted_text_collapses_messy_spacing():
    raw_text = "  Skills\t\tPython\xa0\xa0FastAPI  \n\n\n\n  Experience    Backend APIs  \r\n"

    result = normalize_extracted_text(raw_text)

    assert result == "Skills Python FastAPI\n\nExperience Backend APIs"


def test_normalize_extracted_text_preserves_single_line_breaks():
    raw_text = "Summary\nBuilt APIs\nTested deployments"

    result = normalize_extracted_text(raw_text)

    assert result == raw_text
