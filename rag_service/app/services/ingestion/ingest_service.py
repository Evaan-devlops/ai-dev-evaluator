from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import IngestionError
from app.domain.enums import DocumentMode, DocumentStatus
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.page_repository import PageRepository
from app.services.ingestion.chunk_service import chunk_pages
from app.services.ingestion.embedding_service import embed_batch
from app.services.ingestion.graph_builder import build_graph
from app.services.ingestion.mode_detector import detect_mode
from app.services.ingestion.parser_service import parse_document
from app.services.ingestion.structure_extractor import extract_sections
from app.services.ingestion.summary_service import summarize_page


async def run_ingestion(
    document_id: str,
    file_path: Path,
    content_type: str,
    session: AsyncSession,
) -> DocumentMode:
    """
    Full ingestion pipeline:
    1. Parse → detect mode → extract structure → chunk → summarize → embed → build graph → persist
    """
    doc_repo = DocumentRepository(session)
    page_repo = PageRepository(session)
    chunk_repo = ChunkRepository(session)
    graph_repo = GraphRepository(session)

    await doc_repo.update_status(document_id, DocumentStatus.parsing)

    try:
        # Parse
        pages = parse_document(file_path, content_type)
        if not pages:
            raise IngestionError("Document parsing produced no pages.")

        # Detect mode
        mode = detect_mode(pages)

        # Extract sections for structured docs
        sections = None
        if mode in (DocumentMode.structured, DocumentMode.semi_structured):
            sections = extract_sections(pages)

        # Summarize pages (best-effort)
        for page in pages:
            page["summary"] = await summarize_page(page.get("text", ""))

        # Persist pages
        db_pages = await page_repo.bulk_create(document_id, pages)
        page_id_map = {p.page_number: p.id for p in db_pages}

        # Chunk
        raw_chunks = chunk_pages(pages, mode, sections)

        # Embed
        texts = [c.text for c in raw_chunks]
        embeddings = await embed_batch(texts)

        chunks_data = [
            {
                "chunk_index": c.chunk_index,
                "text": c.text,
                "page_number": c.page_number,
                "section_title": c.section_title,
                "metadata": c.metadata,
                "embedding": embeddings[i],
            }
            for i, c in enumerate(raw_chunks)
        ]

        # Persist chunks
        await chunk_repo.bulk_create(document_id, chunks_data, page_id_map)

        # Build and persist graph
        graph = build_graph(mode, raw_chunks, pages, sections)
        await graph_repo.bulk_create_nodes(document_id, graph.nodes)
        await graph_repo.bulk_create_edges(document_id, graph.edges)

        # Update document record
        await doc_repo.update_after_ingestion(document_id, mode, len(pages), DocumentStatus.indexed)
        await session.commit()
        return mode

    except Exception as exc:
        await session.rollback()
        await doc_repo.update_status(document_id, DocumentStatus.failed)
        await session.commit()
        raise IngestionError(f"Ingestion failed: {exc}") from exc
