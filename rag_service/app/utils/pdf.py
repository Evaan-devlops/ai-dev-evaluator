from __future__ import annotations

from pathlib import Path


def extract_pages_fitz(path: Path) -> list[dict]:
    """Extract page text using PyMuPDF (fitz). Returns list of {page_number, text}."""
    try:
        import fitz  # type: ignore[import]
    except ImportError:
        return []

    pages: list[dict] = []
    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc):
            text = page.get_text("text") or ""
            pages.append({"page_number": i + 1, "text": text})
    return pages


def extract_pages_pdfplumber(path: Path) -> list[dict]:
    """Extract page text using pdfplumber (handles layout better)."""
    try:
        import pdfplumber  # type: ignore[import]
    except ImportError:
        return []

    pages: list[dict] = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({"page_number": i + 1, "text": text})
    return pages


def extract_tables_from_page(path: Path, page_number: int) -> list[list[list[str]]]:
    """Extract tables from a specific page. Returns list of tables (each is list of rows)."""
    try:
        import pdfplumber  # type: ignore[import]
    except ImportError:
        return []

    with pdfplumber.open(str(path)) as pdf:
        if page_number < 1 or page_number > len(pdf.pages):
            return []
        page = pdf.pages[page_number - 1]
        tables = page.extract_tables() or []
        return [[[cell or "" for cell in row] for row in table] for table in tables]
