from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.graph_node import GraphNode
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.retrieval import RetrievalCandidate
from app.utils.text import normalize_text


class StructureRetriever:
    """Retrieves by matching section titles and structural metadata."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.chunk_repo = ChunkRepository(session)

    async def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int,
    ) -> list[RetrievalCandidate]:
        query_lower = query.lower()
        result = await self.session.execute(
            select(GraphNode).where(
                GraphNode.document_id == document_id,
                GraphNode.title.isnot(None),
            )
        )
        nodes = list(result.scalars().all())

        scored: list[tuple[float, GraphNode]] = []
        for node in nodes:
            title = (node.title or "").lower()
            overlap = sum(1 for word in query_lower.split() if word in title)
            if overlap > 0:
                scored.append((overlap / max(len(query_lower.split()), 1), node))

        scored.sort(key=lambda x: x[0], reverse=True)
        candidates: list[RetrievalCandidate] = []

        for score, node in scored[:top_k]:
            summary = node.summary or node.title or ""
            candidates.append(RetrievalCandidate(
                node_id=node.id,
                text=summary,
                score=float(score),
                source="structure",
                page_number=node.page_start,
                section_title=node.title,
                document_id=document_id,
            ))

        return candidates
