from __future__ import annotations

from app.schemas.agent import AgentStep, DecisionTrace
from app.services.agent.state import AgentState


def build_trace(state: AgentState) -> DecisionTrace:
    steps = [
        AgentStep(
            step=s["step"],
            action=s["action"],
            input_summary=s["input_summary"],
            result_summary=s["result_summary"],
            tokens_used=0,
        )
        for s in state.decision_steps
    ]
    return DecisionTrace(
        steps=steps,
        stopped_because=state.stopped_because,
        total_steps=state.step,
        total_tokens=state.context_tokens_used,
    )
