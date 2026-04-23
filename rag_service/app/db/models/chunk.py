from __future__ import annotations

from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base
from app.core.config import settings


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pages.id", ondelete="SET NULL"), nullable=True, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    section_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.VECTOR_DIMENSION), nullable=True)
    prev_chunk_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    next_chunk_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    page: Mapped["Page | None"] = relationship("Page", back_populates="chunks")
