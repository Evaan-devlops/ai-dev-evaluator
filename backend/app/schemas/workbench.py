from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


LayerType = Literal["system", "user", "history", "knowledge", "tools", "state"]


class ContextLayerSchema(BaseModel):
    id: LayerType
    title: str
    description: str
    enabled: bool
    content: str
    token_estimate: int
    order: int
    collapsed: bool
    color: str


class RunScoreBreakdownSchema(BaseModel):
    persona_adherence: int = Field(ge=0, le=10)
    policy_accuracy: int = Field(ge=0, le=10)
    empathy_tone: int = Field(ge=0, le=10)
    context_awareness: int = Field(ge=0, le=10)
    actionability: int = Field(ge=0, le=10)
    personalization: int = Field(ge=0, le=10)
    no_hallucination: int = Field(ge=0, le=10)
    completeness: int = Field(ge=0, le=10)


class RunResultSchema(BaseModel):
    run_id: str
    run_number: int
    quality_score: int
    score_max: int
    score_breakdown: RunScoreBreakdownSchema
    insight: str
    llm_response: str
    latency_ms: int
    total_tokens: int
    active_layers: list[LayerType]
    timestamp: str


class RunHistoryItemSchema(BaseModel):
    run_id: str
    run_number: int
    active_layers: list[LayerType]
    quality_score: int
    score_max: int
    total_tokens: int
    latency_ms: int


class DefaultsResponse(BaseModel):
    layers: list[ContextLayerSchema]
    token_budget_max: int
    run_history: list[RunHistoryItemSchema]
    initial_result: RunResultSchema | None


class AssembleRequest(BaseModel):
    layers: list[ContextLayerSchema]


class AssembleResponse(BaseModel):
    assembled_prompt: str
    per_layer_tokens: dict[str, int]
    total_tokens: int


class RunRequest(BaseModel):
    layers: list[ContextLayerSchema]
    assembled_prompt: str
    provider: str = "mock"


class ResetResponse(BaseModel):
    message: str
    run_history_cleared: bool
