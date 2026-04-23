from __future__ import annotations

from app.domain.enums import QueryType
from app.schemas.retrieval import RetrievalCandidate
from app.utils.text import normalize_text


def rerank(
    candidates: list[RetrievalCandidate],
    query: str,
    query_type: QueryType,
) -> list[RetrievalCandidate]:
    """Deterministic reranker with query-type bias."""
    query_words = set(normalize_text(query).split())

    def _score(c: RetrievalCandidate) -> float:
        base = c.score
        text_words = set(normalize_text(c.text[:200]).split())
        lexical_overlap = len(query_words & text_words) / max(len(query_words), 1)

        # Query-type boosts
        type_boost = 0.0
        if query_type == QueryType.table and c.source == "structure":
            type_boost += 0.15
        if query_type in (QueryType.fact, QueryType.clause) and c.source == "lexical":
            type_boost += 0.1
        if query_type == QueryType.summary and c.source == "semantic":
            type_boost += 0.1
        if query_type == QueryType.multi_hop and c.source == "structure":
            type_boost += 0.1

        return base + lexical_overlap * 0.2 + type_boost

    return sorted(candidates, key=_score, reverse=True)
