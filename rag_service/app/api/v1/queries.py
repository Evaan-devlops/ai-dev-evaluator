from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.config import settings
from app.domain.enums import ConfidenceLabel
from app.repositories.document_repository import DocumentRepository
from app.repositories.query_repository import QueryRepository
from app.schemas.query import AskRequest, AskResponse, EvidenceItem
from app.services.agent.decision_trace import build_trace
from app.services.agent.react_loop import run_react_loop
from app.services.qa.answer_generator import generate_answer
from app.services.qa.query_classifier import classify_query
from app.services.qa.sufficiency_checker import check_sufficiency
from app.services.retrieval.citation_builder import build_citations
from app.services.retrieval.hybrid_retriever import HybridRetriever
from app.services.retrieval.reranker import rerank

router = APIRouter()


@router.post("/queries/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    session: AsyncSession = Depends(get_session),
) -> AskResponse:
    doc_repo = DocumentRepository(session)
    doc = await doc_repo.get(request.document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Classify query
    query_type = classify_query(request.query)

    # 2. Hybrid retrieval
    retriever = HybridRetriever(session)
    candidates = await retriever.retrieve(request.document_id, request.query, request.top_k)

    # 3. Rerank
    candidates = rerank(candidates, request.query, query_type)

    # 4. Sufficiency check
    sufficiency = check_sufficiency(candidates, request.query)

    used_agent = False
    agent_state = None
    retrieval_path = f"hybrid({query_type.value})"

    # 5. Bounded ReAct loop if insufficient and allowed
    if not sufficiency.sufficient and request.allow_agent:
        candidates, sufficiency, agent_state = await run_react_loop(
            request.document_id,
            request.query,
            candidates,
            sufficiency,
            session,
        )
        used_agent = True
        retrieval_path += f" → agent({agent_state.stopped_because}, {agent_state.step} steps)"
        candidates = rerank(candidates, request.query, query_type)

    # 6. Generate answer
    answer_text, confidence = await generate_answer(
        request.query,
        candidates,
        sufficiency,
        request.conversation_context,
    )

    # 7. Build citations
    citations = build_citations(candidates[:10], request.document_id)

    # 8. Persist logs
    trace = build_trace(agent_state).model_dump() if agent_state else {"path": retrieval_path}
    query_repo = QueryRepository(session)
    q_log = await query_repo.create_query_log(
        request.document_id,
        request.query,
        query_type.value,
        used_agent,
        trace,
    )
    await query_repo.create_answer_log(
        q_log.id,
        answer_text,
        confidence.value,
        [c.model_dump() for c in citations],
    )
    await session.commit()

    evidence_items = [
        EvidenceItem(
            chunk_id=c.chunk_id,
            node_id=c.node_id,
            text=c.text[:400],
            score=round(c.score, 4),
            source=c.source,
        )
        for c in candidates[:10]
    ]

    return AskResponse(
        answer=answer_text,
        confidence=confidence,
        citations=citations,
        evidence=evidence_items,
        used_agent=used_agent,
        retrieval_path_summary=retrieval_path,
        query_type=query_type,
    )
