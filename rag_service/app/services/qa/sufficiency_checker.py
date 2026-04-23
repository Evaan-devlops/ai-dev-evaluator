from __future__ import annotations

from dataclasses import dataclass

from app.core.constants import MIN_EVIDENCE_CHARS, SUFFICIENCY_THRESHOLD
from app.schemas.retrieval import RetrievalCandidate


@dataclass
class SufficiencyResult:
    sufficient: bool
    reason: str
    missing_evidence_type: str | None
    suggested_actions: list[str]


def check_sufficiency(
    candidates: list[RetrievalCandidate],
    query: str,
) -> SufficiencyResult:
    if not candidates:
        return SufficiencyResult(
            sufficient=False,
            reason="No evidence retrieved.",
            missing_evidence_type="any",
            suggested_actions=["search_lexical", "search_semantic"],
        )

    total_chars = sum(len(c.text) for c in candidates)
    top_score = max(c.score for c in candidates)
    query_words = set(query.lower().split())

    # Check word coverage across top candidates
    covered_words: set[str] = set()
    for c in candidates[:5]:
        covered_words.update(c.text.lower().split())
    coverage = len(query_words & covered_words) / max(len(query_words), 1)

    if total_chars < MIN_EVIDENCE_CHARS:
        return SufficiencyResult(
            sufficient=False,
            reason="Evidence too sparse.",
            missing_evidence_type="volume",
            suggested_actions=["search_semantic", "fetch_neighbors"],
        )

    if coverage < SUFFICIENCY_THRESHOLD and top_score < 0.7:
        return SufficiencyResult(
            sufficient=False,
            reason=f"Low query coverage ({coverage:.0%}) and low top score ({top_score:.2f}).",
            missing_evidence_type="relevance",
            suggested_actions=["search_lexical", "expand_same_section"],
        )

    return SufficiencyResult(
        sufficient=True,
        reason="Evidence is sufficient.",
        missing_evidence_type=None,
        suggested_actions=[],
    )
