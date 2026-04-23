from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.schemas.retrieval import RetrievalCandidate
from app.services.ingestion.embedding_service import embed_text


class SemanticRetriever:
    """pgvector cosine similarity retriever."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = ChunkRepository(session)

    async def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int,
    ) -> list[RetrievalCandidate]:
        embedding = await embed_text(query)
        if not embedding:
            return []

        chunks = await self.repo.semantic_search(document_id, embedding, top_k)
        return [
            RetrievalCandidate(
                chunk_id=c.id,
                text=c.text,
                score=0.85,
                source="semantic",
                page_number=None,
                section_title=c.section_title,
                document_id=document_id,
            )
            for c in chunks
        ]
