from __future__ import annotations

from app.schemas.retrieval import RetrievalCandidate
from app.utils.tokens import fits_in_budget


def build_evidence_context(
    candidates: list[RetrievalCandidate],
    max_tokens: int,
) -> str:
    """Build a context string from top candidates, respecting token budget."""
    texts = [c.text for c in candidates]
    selected = fits_in_budget(texts, max_tokens)
    parts: list[str] = []
    for i, text in enumerate(selected):
        c = candidates[i]
        header = f"[Evidence {i + 1}]"
        if c.section_title:
            header += f" {c.section_title}"
        if c.page_number:
            header += f" (page {c.page_number})"
        parts.append(f"{header}\n{text}")
    return "\n\n".join(parts)
