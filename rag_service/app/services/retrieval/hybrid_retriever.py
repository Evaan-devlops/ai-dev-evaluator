from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import BM25_WEIGHT, SEMANTIC_WEIGHT, STRUCTURE_WEIGHT
from app.schemas.retrieval import RetrievalCandidate
from app.services.retrieval.lexical_retriever import LexicalRetriever
from app.services.retrieval.semantic_retriever import SemanticRetriever
from app.services.retrieval.structure_retriever import StructureRetriever


class HybridRetriever:
    """Merges lexical, semantic, and structural candidates with score fusion."""

    def __init__(self, session: AsyncSession) -> None:
        self.lexical = LexicalRetriever(session)
        self.semantic = SemanticRetriever(session)
        self.structure = StructureRetriever(session)

    async def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int,
    ) -> list[RetrievalCandidate]:
        lex, sem, struct = await _parallel_retrieve(
            self.lexical, self.semantic, self.structure,
            document_id, query, top_k,
        )

        merged: dict[str, RetrievalCandidate] = {}

        def _merge(candidates: list[RetrievalCandidate], weight: float) -> None:
            for candidate in candidates:
                key = candidate.chunk_id or candidate.node_id or candidate.text[:80]
                if key not in merged:
                    merged[key] = candidate.model_copy(update={"score": candidate.score * weight})
                else:
                    merged[key] = merged[key].model_copy(
                        update={"score": merged[key].score + candidate.score * weight}
                    )

        _merge(lex, BM25_WEIGHT)
        _merge(sem, SEMANTIC_WEIGHT)
        _merge(struct, STRUCTURE_WEIGHT)

        ranked = sorted(merged.values(), key=lambda c: c.score, reverse=True)
        return ranked[:top_k]


async def _parallel_retrieve(
    lexical: LexicalRetriever,
    semantic: SemanticRetriever,
    structure: StructureRetriever,
    document_id: str,
    query: str,
    top_k: int,
) -> tuple[list[RetrievalCandidate], list[RetrievalCandidate], list[RetrievalCandidate]]:
    import asyncio
    results = await asyncio.gather(
        lexical.retrieve(document_id, query, top_k),
        semantic.retrieve(document_id, query, top_k),
        structure.retrieve(document_id, query, top_k),
        return_exceptions=True,
    )
    lex = results[0] if not isinstance(results[0], BaseException) else []
    sem = results[1] if not isinstance(results[1], BaseException) else []
    struct = results[2] if not isinstance(results[2], BaseException) else []
    return lex, sem, struct  # type: ignore[return-value]
