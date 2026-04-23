from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.exceptions import FileTooLargeError, IngestionError, UnsupportedFileTypeError
from app.domain.enums import DocumentMode, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.graph_repository import GraphRepository
from app.repositories.page_repository import PageRepository
from app.schemas.document import (
    DocumentMetaResponse,
    DocumentStatusResponse,
    DocumentStructureResponse,
    DocumentUploadResponse,
    PageResponse,
    StructureNode,
)
from app.services.ingestion.ingest_service import run_ingestion
from app.services.storage.file_store import file_store

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
) -> DocumentUploadResponse:
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "upload"

    try:
        checksum = file_store.checksum(data)
        doc_repo = DocumentRepository(session)
        doc = await doc_repo.create(filename, content_type, checksum)
        await session.commit()

        file_path = await file_store.save(doc.id, filename, content_type, data)

        mode = await run_ingestion(doc.id, file_path, content_type, session)
        refreshed = await doc_repo.get(doc.id)

        return DocumentUploadResponse(
            document_id=doc.id,
            filename=filename,
            detected_mode=mode,
            status=DocumentStatus.indexed,
            page_count=refreshed.page_count if refreshed is not None else 0,
        )
    except (FileTooLargeError, UnsupportedFileTypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IngestionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/documents/{document_id}", response_model=DocumentMetaResponse)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentMetaResponse:
    repo = DocumentRepository(session)
    doc = await repo.get(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentMetaResponse(
        document_id=doc.id,
        filename=doc.filename,
        content_type=doc.content_type,
        mode=DocumentMode(doc.mode),
        status=DocumentStatus(doc.status),
        page_count=doc.page_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentStatusResponse:
    repo = DocumentRepository(session)
    doc = await repo.get(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return DocumentStatusResponse(
        document_id=doc.id,
        status=DocumentStatus(doc.status),
        mode=DocumentMode(doc.mode),
    )


@router.get("/documents/{document_id}/structure", response_model=DocumentStructureResponse)
async def get_document_structure(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentStructureResponse:
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    graph_repo = GraphRepository(session)
    db_nodes = await graph_repo.list_nodes_by_document(document_id)

    node_map = {n.id: n for n in db_nodes}
    children_map: dict[str, list[str]] = {n.id: [] for n in db_nodes}

    for node in db_nodes:
        children = await graph_repo.get_children(node.id)
        children_map[node.id] = [c.id for c in children]

    nodes = [
        StructureNode(
            node_id=n.id,
            node_type=n.node_type,
            title=n.title,
            page_start=n.page_start,
            page_end=n.page_end,
            children=children_map.get(n.id, []),
        )
        for n in db_nodes
    ]

    return DocumentStructureResponse(
        document_id=document_id,
        mode=DocumentMode(doc.mode),
        nodes=nodes,
    )


@router.get("/documents/{document_id}/pages/{page_number}", response_model=PageResponse)
async def get_page(
    document_id: str,
    page_number: int,
    session: AsyncSession = Depends(get_session),
) -> PageResponse:
    repo = PageRepository(session)
    page = await repo.get_by_number(document_id, page_number)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found.")
    return PageResponse(
        document_id=document_id,
        page_number=page.page_number,
        raw_text=page.raw_text,
        summary=page.summary,
        layout_type=page.layout_type,
    )
