from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AgentStep(BaseModel):
    step: int
    action: str
    input_summary: str
    result_summary: str
    tokens_used: int


class DecisionTrace(BaseModel):
    steps: list[AgentStep]
    stopped_because: str
    total_steps: int
    total_tokens: int
