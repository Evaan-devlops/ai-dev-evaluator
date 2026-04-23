from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.schemas.retrieval import RetrievalCandidate
from app.utils.text import normalize_text


class LexicalRetriever:
    """PostgreSQL full-text search retriever."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = ChunkRepository(session)

    async def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int,
    ) -> list[RetrievalCandidate]:
        normalized_query = normalize_text(query)
        chunks = await self.repo.fulltext_search(document_id, normalized_query, top_k)
        return [
            RetrievalCandidate(
                chunk_id=c.id,
                text=c.text,
                score=0.8,  # Fixed score for FTS matches
                source="lexical",
                page_number=None,
                section_title=c.section_title,
                document_id=document_id,
            )
            for c in chunks
        ]
