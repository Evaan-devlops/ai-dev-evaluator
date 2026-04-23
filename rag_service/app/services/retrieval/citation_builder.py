from __future__ import annotations

from app.core.constants import CITATION_SNIPPET_LENGTH
from app.schemas.query import CitationItem
from app.schemas.retrieval import RetrievalCandidate
from app.utils.text import truncate


def build_citations(
    candidates: list[RetrievalCandidate],
    document_id: str,
) -> list[CitationItem]:
    seen: set[str] = set()
    citations: list[CitationItem] = []

    for candidate in candidates:
        snippet = truncate(candidate.text, CITATION_SNIPPET_LENGTH)
        dedup_key = snippet[:80]
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        citations.append(CitationItem(
            document_id=document_id,
            page_number=candidate.page_number,
            section_title=candidate.section_title,
            evidence_snippet=snippet,
            chunk_id=candidate.chunk_id,
            node_id=candidate.node_id,
        ))

    return citations
