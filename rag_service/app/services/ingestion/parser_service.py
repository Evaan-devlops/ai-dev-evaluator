from __future__ import annotations

from pathlib import Path

from app.utils.pdf import extract_pages_fitz, extract_pages_pdfplumber


def parse_document(path: Path, content_type: str) -> list[dict]:
    """Parse a document and return list of {page_number, text} dicts."""
    if content_type == "application/pdf":
        pages = extract_pages_pdfplumber(path)
        if not any(p["text"].strip() for p in pages):
            # Fallback to fitz if pdfplumber gives empty
            pages = extract_pages_fitz(path)
        return pages

    # Plain text / markdown / json / csv — single page
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    return [{"page_number": 1, "text": text}]
