from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.answer_log import AnswerLog
from app.db.models.query_log import QueryLog
from app.utils.ids import new_id


class QueryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_query_log(
        self,
        document_id: str | None,
        query_text: str,
        query_type: str,
        used_agent: bool,
        retrieval_trace: dict,
    ) -> QueryLog:
        log = QueryLog(
            id=new_id(),
            document_id=document_id,
            query_text=query_text,
            query_type=query_type,
            used_agent=used_agent,
            retrieval_trace_json=retrieval_trace,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def create_answer_log(
        self,
        query_log_id: str,
        answer_text: str,
        confidence: str,
        citations: list,
    ) -> AnswerLog:
        log = AnswerLog(
            id=new_id(),
            query_log_id=query_log_id,
            answer_text=answer_text,
            confidence=confidence,
            citations_json=citations,
        )
        self.session.add(log)
        await self.session.flush()
        return log
