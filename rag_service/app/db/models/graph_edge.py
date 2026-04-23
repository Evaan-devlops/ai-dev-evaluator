from __future__ import annotations

from sqlalchemy import String, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    from_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    to_node_id: Mapped[str] = mapped_column(String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_type: Mapped[str] = mapped_column(String(32), nullable=False)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    from_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[from_node_id], back_populates="outgoing_edges")
    to_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[to_node_id], back_populates="incoming_edges")
