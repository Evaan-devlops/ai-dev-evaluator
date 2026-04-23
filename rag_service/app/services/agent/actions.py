from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.graph_repository import GraphRepository
from app.schemas.retrieval import RetrievalCandidate
from app.services.ingestion.embedding_service import embed_text
from app.utils.text import normalize_text


ALLOWED_ACTIONS = {
    "search_lexical",
    "search_semantic",
    "search_structure",
    "fetch_node",
    "fetch_neighbors",
    "fetch_parent",
    "fetch_children",
    "fetch_page",
    "expand_same_section",
}


async def execute_action(
    action: str,
    document_id: str,
    query: str,
    session: AsyncSession,
    context: dict,
) -> list[RetrievalCandidate]:
    chunk_repo = ChunkRepository(session)
    graph_repo = GraphRepository(session)

    if action == "search_lexical":
        chunks = await chunk_repo.fulltext_search(document_id, normalize_text(query), top_k=5)
        return [
            RetrievalCandidate(chunk_id=c.id, text=c.text, score=0.75, source="lexical",
                               section_title=c.section_title, document_id=document_id)
            for c in chunks
        ]

    if action == "search_semantic":
        embedding = await embed_text(query)
        if not embedding:
            return []
        chunks = await chunk_repo.semantic_search(document_id, embedding, top_k=5)
        return [
            RetrievalCandidate(chunk_id=c.id, text=c.text, score=0.8, source="semantic",
                               section_title=c.section_title, document_id=document_id)
            for c in chunks
        ]

    if action == "fetch_neighbors":
        node_id = context.get("last_node_id")
        if not node_id:
            return []
        neighbors = await graph_repo.get_neighbors(node_id)
        return [
            RetrievalCandidate(node_id=n.id, text=n.summary or n.title or "", score=0.6,
                               source="graph", page_number=n.page_start,
                               section_title=n.title, document_id=document_id)
            for n in neighbors if (n.summary or n.title)
        ]

    if action == "fetch_parent":
        node_id = context.get("last_node_id")
        if not node_id:
            return []
        parent = await graph_repo.get_parent(node_id)
        if not parent:
            return []
        return [
            RetrievalCandidate(node_id=parent.id, text=parent.summary or parent.title or "",
                               score=0.65, source="graph", page_number=parent.page_start,
                               section_title=parent.title, document_id=document_id)
        ]

    if action == "expand_same_section":
        section_title = context.get("last_section_title")
        if not section_title:
            return []
        all_chunks = await chunk_repo.list_by_document(document_id)
        related = [c for c in all_chunks if c.section_title == section_title][:5]
        return [
            RetrievalCandidate(chunk_id=c.id, text=c.text, score=0.65, source="structure",
                               section_title=c.section_title, document_id=document_id)
            for c in related
        ]

    return []
