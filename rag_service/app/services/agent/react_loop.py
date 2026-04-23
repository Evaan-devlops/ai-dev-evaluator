from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.retrieval import RetrievalCandidate
from app.services.agent.actions import ALLOWED_ACTIONS, execute_action
from app.services.agent.state import AgentState
from app.services.agent.stop_conditions import should_stop
from app.services.qa.sufficiency_checker import SufficiencyResult, check_sufficiency


async def run_react_loop(
    document_id: str,
    query: str,
    initial_candidates: list[RetrievalCandidate],
    initial_sufficiency: SufficiencyResult,
    session: AsyncSession,
) -> tuple[list[RetrievalCandidate], SufficiencyResult, AgentState]:
    """
    Bounded ReAct-style retrieval loop.
    Stops when evidence is sufficient, max steps reached, or context budget exhausted.
    """
    state = AgentState(query=query, document_id=document_id)
    state.add_candidates(initial_candidates)
    current_sufficiency = initial_sufficiency

    stop, reason = should_stop(state, current_sufficiency)
    if stop:
        state.stopped_because = reason
        return state.accumulated_candidates, current_sufficiency, state

    action_context: dict = {}

    # Track last relevant node/section for context-aware actions
    if initial_candidates:
        top = initial_candidates[0]
        action_context["last_node_id"] = top.node_id
        action_context["last_section_title"] = top.section_title

    while True:
        state.step += 1
        action = _choose_action(current_sufficiency)
        new_candidates = await execute_action(action, document_id, query, session, action_context)
        state.add_candidates(new_candidates)

        if new_candidates:
            top_new = new_candidates[0]
            action_context["last_node_id"] = top_new.node_id
            action_context["last_section_title"] = top_new.section_title

        state.record_step(
            action=action,
            input_summary=f"gap: {current_sufficiency.missing_evidence_type}",
            result_summary=f"retrieved {len(new_candidates)} new candidates",
        )

        current_sufficiency = check_sufficiency(state.accumulated_candidates, query)
        stop, reason = should_stop(state, current_sufficiency)
        if stop:
            state.stopped_because = reason
            break

    return state.accumulated_candidates, current_sufficiency, state


def _choose_action(sufficiency: SufficiencyResult) -> str:
    """Deterministic action selection based on missing evidence type."""
    suggested = sufficiency.suggested_actions
    for action in suggested:
        if action in ALLOWED_ACTIONS:
            return action
    return "search_semantic"
