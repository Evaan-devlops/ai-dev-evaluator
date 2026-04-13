from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

LayerType = Literal["system", "user", "history", "knowledge", "tools", "state"]


@dataclass
class RunScoreBreakdown:
    persona_adherence: int
    policy_accuracy: int
    empathy_tone: int
    context_awareness: int
    actionability: int
    personalization: int
    no_hallucination: int
    completeness: int


@dataclass
class RunResult:
    run_id: str
    run_number: int
    quality_score: int
    score_max: int
    score_breakdown: RunScoreBreakdown
    insight: str
    llm_response: str
    latency_ms: int
    total_tokens: int
    active_layers: list[LayerType]
    timestamp: str


@dataclass
class RunHistoryItem:
    run_id: str
    run_number: int
    active_layers: list[LayerType]
    quality_score: int
    score_max: int
    total_tokens: int
    latency_ms: int


@dataclass
class ContextLayer:
    id: LayerType
    title: str
    description: str
    enabled: bool
    content: str
    token_estimate: int
    order: int
    collapsed: bool
    color: str
