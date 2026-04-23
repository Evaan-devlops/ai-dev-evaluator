from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import DocumentMode, DocumentStatus


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    detected_mode: DocumentMode
    status: DocumentStatus
    page_count: int


class DocumentMetaResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str
    mode: DocumentMode
    status: DocumentStatus
    page_count: int
    created_at: datetime
    updated_at: datetime


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    mode: DocumentMode


class StructureNode(BaseModel):
    node_id: str
    node_type: str
    title: str | None
    page_start: int | None
    page_end: int | None
    children: list[str]


class DocumentStructureResponse(BaseModel):
    document_id: str
    mode: DocumentMode
    nodes: list[StructureNode]


class PageResponse(BaseModel):
    document_id: str
    page_number: int
    raw_text: str
    summary: str | None
    layout_type: str
