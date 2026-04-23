from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def extract_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def heading_density(lines: list[str]) -> float:
    """Fraction of lines that look like headings."""
    if not lines:
        return 0.0
    heading_pattern = re.compile(r"^(#{1,6}\s+\S|[A-Z][A-Z0-9 ]{2,50}$|\d+\.\d*\s+\S)")
    headings = sum(1 for line in lines if heading_pattern.match(line.strip()))
    return headings / len(lines)


def avg_line_length(lines: list[str]) -> float:
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        return 0.0
    return sum(len(ln) for ln in non_empty) / len(non_empty)
