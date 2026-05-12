import re

import fitz  # pymupdf


def normalize_extracted_text(text: str) -> str:
    normalized = text.replace("\xa0", " ").replace("\t", " ")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ ]{2,}", " ", line).strip() for line in normalized.split("\n")]
    normalized = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", normalized).strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("File is not a valid PDF") from exc

    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    doc.close()

    return normalize_extracted_text("\n".join(pages_text))
