from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, func

from app.db.base import Base


class AnswerLog(Base):
    __tablename__ = "answer_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_log_id: Mapped[str] = mapped_column(String(36), ForeignKey("query_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), nullable=False)
    citations_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    query_log: Mapped["QueryLog"] = relationship("QueryLog", back_populates="answer")
