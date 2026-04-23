from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="unstructured")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="uploaded")
    checksum: Mapped[str] = mapped_column(String(64), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pages: Mapped[list["Page"]] = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list["Chunk"]] = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    graph_nodes: Mapped[list["GraphNode"]] = relationship("GraphNode", back_populates="document", cascade="all, delete-orphan")
