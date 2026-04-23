from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chunk import Chunk
from app.utils.ids import new_id
from app.utils.text import normalize_text


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(
        self,
        document_id: str,
        chunks_data: list[dict],
        page_id_map: dict[int, str],
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        ids: list[str] = [new_id() for _ in chunks_data]

        for i, item in enumerate(chunks_data):
            page_id = page_id_map.get(item.get("page_number", 0))
            chunk = Chunk(
                id=ids[i],
                document_id=document_id,
                page_id=page_id,
                chunk_index=item["chunk_index"],
                text=item["text"],
                normalized_text=normalize_text(item["text"]),
                section_title=item.get("section_title"),
                metadata_json=item.get("metadata", {}),
                embedding=item.get("embedding") or None,
                prev_chunk_id=ids[i - 1] if i > 0 else None,
                next_chunk_id=None,
            )
            self.session.add(chunk)
            chunks.append(chunk)

        await self.session.flush()

        # Patch next_chunk_id
        for i in range(len(chunks) - 1):
            chunks[i].next_chunk_id = chunks[i + 1].id
        await self.session.flush()

        return chunks

    async def semantic_search(
        self,
        document_id: str,
        embedding: list[float],
        top_k: int,
    ) -> list[Chunk]:
        if not embedding:
            return []
        vec_str = f"[{','.join(f'{v:.8f}' for v in embedding)}]"
        stmt = text(
            "SELECT id FROM chunks "
            "WHERE document_id = :doc_id AND embedding IS NOT NULL "
            "ORDER BY embedding <=> CAST(:vec AS vector) "
            "LIMIT :k"
        )
        result = await self.session.execute(stmt, {"doc_id": document_id, "vec": vec_str, "k": top_k})
        ids = [row[0] for row in result.fetchall()]
        if not ids:
            return []
        result2 = await self.session.execute(select(Chunk).where(Chunk.id.in_(ids)))
        chunks_map = {c.id: c for c in result2.scalars().all()}
        return [chunks_map[id_] for id_ in ids if id_ in chunks_map]

    async def fulltext_search(
        self,
        document_id: str,
        query: str,
        top_k: int,
    ) -> list[Chunk]:
        stmt = text(
            "SELECT id FROM chunks "
            "WHERE document_id = :doc_id "
            "AND to_tsvector('english', normalized_text) @@ plainto_tsquery('english', :q) "
            "LIMIT :k"
        )
        result = await self.session.execute(stmt, {"doc_id": document_id, "q": query, "k": top_k})
        ids = [row[0] for row in result.fetchall()]
        if not ids:
            return []
        result2 = await self.session.execute(select(Chunk).where(Chunk.id.in_(ids)))
        return list(result2.scalars().all())

    async def get_by_id(self, chunk_id: str) -> Chunk | None:
        result = await self.session.execute(select(Chunk).where(Chunk.id == chunk_id))
        return result.scalar_one_or_none()

    async def list_by_document(self, document_id: str) -> list[Chunk]:
        result = await self.session.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        return list(result.scalars().all())
