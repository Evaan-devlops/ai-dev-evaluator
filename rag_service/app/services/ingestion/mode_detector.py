from __future__ import annotations

from app.core.constants import (
    STRUCTURED_MODE_HEADING_DENSITY_MIN,
    UNSTRUCTURED_MODE_HEADING_DENSITY_MAX,
    SCANNED_MODE_AVG_LINE_LENGTH_MAX,
)
from app.domain.enums import DocumentMode
from app.utils.text import heading_density, avg_line_length


def detect_mode(pages: list[dict]) -> DocumentMode:
    """Heuristic mode detection from extracted page data."""
    if not pages:
        return DocumentMode.unstructured

    all_lines: list[str] = []
    total_text = ""
    for page in pages:
        text = page.get("text", "")
        total_text += text
        all_lines.extend(text.splitlines())

    if not total_text.strip():
        return DocumentMode.scanned

    hd = heading_density(all_lines)
    al = avg_line_length(all_lines)

    # Very short lines with low heading density → likely scanned/layout-heavy
    if al < SCANNED_MODE_AVG_LINE_LENGTH_MAX and hd < UNSTRUCTURED_MODE_HEADING_DENSITY_MAX:
        return DocumentMode.scanned

    if hd >= STRUCTURED_MODE_HEADING_DENSITY_MIN:
        return DocumentMode.structured

    if hd > UNSTRUCTURED_MODE_HEADING_DENSITY_MAX:
        return DocumentMode.semi_structured

    return DocumentMode.unstructured
