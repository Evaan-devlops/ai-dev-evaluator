from __future__ import annotations

from app.core.config import settings
from app.services.agent.state import AgentState
from app.services.qa.sufficiency_checker import SufficiencyResult


def should_stop(
    state: AgentState,
    sufficiency: SufficiencyResult,
) -> tuple[bool, str]:
    if sufficiency.sufficient:
        return True, "sufficient_evidence"

    if state.step >= settings.MAX_AGENT_STEPS:
        return True, f"max_steps_reached ({settings.MAX_AGENT_STEPS})"

    if state.context_tokens_used >= settings.MAX_CONTEXT_TOKENS:
        return True, "context_budget_exhausted"

    return False, ""
