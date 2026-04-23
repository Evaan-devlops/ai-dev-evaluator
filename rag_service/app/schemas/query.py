from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.domain.enums import ConfidenceLabel, QueryType


class AskRequest(BaseModel):
    document_id: str
    query: str
    conversation_context: list[dict[str, str]] | None = None
    top_k: int = Field(default=8, ge=1, le=50)
    allow_agent: bool = True


class CitationItem(BaseModel):
    document_id: str
    page_number: int | None
    section_title: str | None
    evidence_snippet: str
    chunk_id: str | None
    node_id: str | None


class EvidenceItem(BaseModel):
    chunk_id: str | None
    node_id: str | None
    text: str
    score: float
    source: str


class AskResponse(BaseModel):
    answer: str
    confidence: ConfidenceLabel
    citations: list[CitationItem]
    evidence: list[EvidenceItem]
    used_agent: bool
    retrieval_path_summary: str
    query_type: QueryType
