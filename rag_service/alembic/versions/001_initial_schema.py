"""Initial schema with pgvector support

Revision ID: 001
Revises:
Create Date: 2026-04-22

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False, server_default="unstructured"),
        sa.Column("status", sa.String(32), nullable=False, server_default="uploaded"),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("page_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "pages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False, server_default=""),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("layout_type", sa.String(32), nullable=False, server_default="text"),
        sa.Column("ocr_confidence", sa.Float, nullable=True),
    )
    op.create_index("ix_pages_document_id", "pages", ["document_id"])

    op.create_table(
        "chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_id", sa.String(36), sa.ForeignKey("pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("normalized_text", sa.Text, nullable=False, server_default=""),
        sa.Column("section_title", sa.String(512), nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("embedding", sa.Text, nullable=True),  # stored as vector via raw SQL
        sa.Column("prev_chunk_id", sa.String(36), sa.ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("next_chunk_id", sa.String(36), sa.ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])

    # Alter the column to proper vector type after pgvector extension is installed
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_chunks_fts ON chunks USING gin(to_tsvector('english', normalized_text))")

    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("page_start", sa.Integer, nullable=True),
        sa.Column("page_end", sa.Integer, nullable=True),
        sa.Column("content_ref", sa.String(36), nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_graph_nodes_document_id", "graph_nodes", ["document_id"])

    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_node_id", sa.String(36), sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_node_id", sa.String(36), sa.ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("edge_type", sa.String(32), nullable=False),
        sa.Column("weight", sa.Float, nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_graph_edges_document_id", "graph_edges", ["document_id"])

    op.create_table(
        "query_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("query_type", sa.String(32), nullable=False, server_default="fact"),
        sa.Column("used_agent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("retrieval_trace_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "answer_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("query_log_id", sa.String(36), sa.ForeignKey("query_logs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answer_text", sa.Text, nullable=False),
        sa.Column("confidence", sa.String(32), nullable=False),
        sa.Column("citations_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_answer_logs_query_log_id", "answer_logs", ["query_log_id"])


def downgrade() -> None:
    op.drop_table("answer_logs")
    op.drop_table("query_logs")
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
    op.drop_table("chunks")
    op.drop_table("pages")
    op.drop_table("documents")
