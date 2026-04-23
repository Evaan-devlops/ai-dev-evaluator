from __future__ import annotations

from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    document: Mapped["Document"] = relationship("Document", back_populates="graph_nodes")
    outgoing_edges: Mapped[list["GraphEdge"]] = relationship("GraphEdge", foreign_keys="GraphEdge.from_node_id", back_populates="from_node", cascade="all, delete-orphan")
    incoming_edges: Mapped[list["GraphEdge"]] = relationship("GraphEdge", foreign_keys="GraphEdge.to_node_id", back_populates="to_node")
