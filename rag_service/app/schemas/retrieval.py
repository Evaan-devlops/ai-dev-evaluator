from __future__ import annotations

from pydantic import BaseModel


class RetrievalCandidate(BaseModel):
    chunk_id: str | None = None
    node_id: str | None = None
    text: str
    score: float
    source: str  # "lexical" | "semantic" | "structure"
    page_number: int | None = None
    section_title: str | None = None
    document_id: str
