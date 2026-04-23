from __future__ import annotations

from app.domain.enums import ConfidenceLabel
from app.schemas.retrieval import RetrievalCandidate
from app.services.llm.provider import get_llm_provider
from app.services.qa.context_builder import build_evidence_context
from app.services.qa.sufficiency_checker import SufficiencyResult
from app.utils.tokens import estimate_tokens


async def generate_answer(
    query: str,
    candidates: list[RetrievalCandidate],
    sufficiency: SufficiencyResult,
    conversation_context: list[dict] | None = None,
    max_tokens: int = 600,
) -> tuple[str, ConfidenceLabel]:
    """Generate a grounded answer from evidence. Returns (answer_text, confidence)."""
    if not candidates or not sufficiency.sufficient:
        return (
            "Insufficient evidence was found in the document to answer this query confidently.",
            ConfidenceLabel.insufficient_evidence,
        )

    context = build_evidence_context(candidates, max_tokens=3000)
    provider = get_llm_provider()

    history_block = ""
    if conversation_context:
        turns = "\n".join(
            f"{turn.get('role', 'user').capitalize()}: {turn.get('content', '')}"
            for turn in conversation_context[-6:]
        )
        history_block = f"\n\nConversation history:\n{turns}"

    prompt = "\n\n".join(filter(None, [
        f"Query: {query}",
        history_block,
        "Evidence from document:",
        context,
        "Answer the query using only the evidence above. Include a brief citation for each claim.",
    ]))

    system = (
        "You are a document QA system. "
        "Answer only from the provided evidence. "
        "Do not invent facts. "
        "If evidence is partial, say so clearly."
    )

    answer = await provider.generate_text(prompt, system=system, max_tokens=max_tokens, temperature=0.1)
    if not answer.strip():
        return "Could not generate an answer.", ConfidenceLabel.insufficient_evidence

    top_score = max(c.score for c in candidates)
    confidence = (
        ConfidenceLabel.direct_evidence
        if top_score >= 0.8
        else ConfidenceLabel.multi_evidence_inference
    )
    return answer.strip(), confidence
