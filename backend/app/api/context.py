"""Context API router — exposes /api/context/* endpoints.

This is the API the frontend calls. It uses integer run_ids and the
new ScoreBreakdown field names (persona, policy, empathy, context,
actionability, personalization, hallucination, completeness).
"""
from __future__ import annotations

import copy
import random
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.data.demo_seed import (
    LAYER_META_CONTEXT,
    ORDERED_LAYERS,
    SEEDED_RUNS_CONTEXT,
    BEST_SEEDED_RUN_ID,
    MAX_BUDGET,
    _assembled,
)

router = APIRouter(prefix="/api/context", tags=["context"])


# ---------------------------------------------------------------------------
# Pydantic models (matching frontend ApiLayerDTO, ApiEvaluateResponse, etc.)
# ---------------------------------------------------------------------------

LayerKey = str  # "system" | "user" | "history" | "knowledge" | "tools" | "state"


class LayerDTO(BaseModel):
    key: str
    id: int
    name: str
    subtitle: str
    tokens: int
    always_on: bool = False
    warning: Optional[str] = None
    content: str


class ContextMetaResponse(BaseModel):
    max_budget: int
    ordered_layers: List[str]
    layers: List[LayerDTO]


class ScoreBreakdown(BaseModel):
    persona: int = Field(ge=0, le=10)
    policy: int = Field(ge=0, le=10)
    empathy: int = Field(ge=0, le=10)
    context: int = Field(ge=0, le=10)
    actionability: int = Field(ge=0, le=10)
    personalization: int = Field(ge=0, le=10)
    hallucination: int = Field(ge=0, le=10)
    completeness: int = Field(ge=0, le=10)


class EvaluateRequest(BaseModel):
    provider: str = "mock-provider"
    active_layers: List[str]
    run_id: Optional[int] = None


class EvaluateResponse(BaseModel):
    model_config = {'protected_namespaces': ()}

    run_id: int
    provider: str
    active_layers: List[str]
    active_count: int
    token_budget_used: int
    token_budget_max: int
    assembled_prompt: str
    model_response: str
    breakdown: ScoreBreakdown
    score: int
    latency_ms: int
    insight: str


class HistoryRow(BaseModel):
    run_id: int
    active_layers: List[str]
    score: int
    tokens: int
    latency_ms: int
    provider: str


# ---------------------------------------------------------------------------
# In-memory state (seeded on startup, reset-able)
# ---------------------------------------------------------------------------

def _scale_seed_score(score: int) -> int:
    return round((score / 40) * 100)


def _scale_seed_breakdown(raw: dict[str, int]) -> dict[str, int]:
    return {key: min(10, value * 2) for key, value in raw.items()}


def _build_history() -> List[HistoryRow]:
    return [
        HistoryRow(
            run_id=r["run_id"],
            active_layers=r["active_layers"],
            score=_scale_seed_score(r["score"]),
            tokens=r["token_budget_used"],
            latency_ms=r["latency_ms"],
            provider=r["provider"],
        )
        for r in SEEDED_RUNS_CONTEXT
    ]


def _build_details() -> dict[int, EvaluateResponse]:
    return {
        r["run_id"]: EvaluateResponse(
            run_id=r["run_id"],
            provider=r["provider"],
            active_layers=r["active_layers"],
            active_count=r["active_count"],
            token_budget_used=r["token_budget_used"],
            token_budget_max=r["token_budget_max"],
            assembled_prompt=r["assembled_prompt"],
            model_response=r["model_response"],
            breakdown=ScoreBreakdown(**_scale_seed_breakdown(r["breakdown"])),
            score=_scale_seed_score(r["score"]),
            latency_ms=r["latency_ms"],
            insight=r["insight"],
        )
        for r in SEEDED_RUNS_CONTEXT
    }


_history: List[HistoryRow] = _build_history()
_details: dict[int, EvaluateResponse] = _build_details()
_run_counter: int = len(SEEDED_RUNS_CONTEXT)


# ---------------------------------------------------------------------------
# Layer helpers
# ---------------------------------------------------------------------------

_LAYER_MAP = {m["key"]: m for m in LAYER_META_CONTEXT}


def _token_count(active: List[str]) -> int:
    return sum(_LAYER_MAP[k]["tokens"] for k in active if k in _LAYER_MAP)


def _normalize(layers: List[str]) -> List[str]:
    s = set(layers) | {"user"}
    return [k for k in ORDERED_LAYERS if k in s]


def _score(active: List[str]) -> ScoreBreakdown:
    has = set(active)
    b = dict(persona=1, policy=1, empathy=2, context=1,
             actionability=0, personalization=1, hallucination=2, completeness=4)

    if "system" in has:
        b["persona"] = 5; b["empathy"] = 5
        b["personalization"] = max(b["personalization"], 2)
        b["context"] = max(b["context"], 2)
    if "history" in has:
        b["context"] = 5
        b["personalization"] = max(b["personalization"], 3)
        b["completeness"] = 5
    if "knowledge" in has:
        b["policy"] = 5; b["hallucination"] = 5
        b["context"] = max(b["context"], 4)
    if "tools" in has:
        b["actionability"] = 5; b["completeness"] = 5
    if "state" in has:
        b["personalization"] = 5; b["context"] = 5; b["persona"] = 5
    if "system" in has and "knowledge" not in has:
        b["actionability"] = min(b["actionability"], 1)
        b["policy"] = min(b["policy"], 3)

    return ScoreBreakdown(**{key: min(10, value * 2) for key, value in b.items()})


def _score_total(breakdown: ScoreBreakdown) -> int:
    total = sum([
        breakdown.persona, breakdown.policy, breakdown.empathy,
        breakdown.context, breakdown.actionability, breakdown.personalization,
        breakdown.hallucination, breakdown.completeness,
    ])
    return round((total / 80) * 100)


def _mock_response(active: List[str]) -> str:
    has = set(active)
    parts: List[str] = []

    if "system" in has:
        parts.append(
            "Marcus, I'm really sorry you've had to make a third attempt to get this resolved, "
            "especially after the portal error and that 45-minute hold followed by a disconnect."
        )
        parts.append(
            "I'm Alex, a Senior Resolution Specialist at NovaTech, and I'm going to take "
            "ownership of this from here."
        )
    else:
        parts.append("I'm sorry you're dealing with this.")

    if "history" in has:
        parts.append(
            "I can see you've already completed all troubleshooting steps and shared order "
            "number NVT-2024-91847, so I won't ask you to repeat anything."
        )
    if "knowledge" in has:
        parts.append(
            "Because this is a confirmed defect on a premium audio device within the 45-day "
            "return window, this qualifies for a manual agent-assisted replacement with no restocking fee."
        )
    if "state" in has:
        parts.append(
            "Given your Platinum status, your professional use case, and the fact that this is "
            "your third attempt, I'm treating this as an urgent retention-risk case."
        )
    if "tools" in has:
        parts.append(
            "Here's what I will do:\n"
            "1. Process a replacement for your NovaSound Pro 3000 with expedited shipping.\n"
            "2. Add a $15 inconvenience credit for the portal failure and support disconnect.\n"
            "3. Handle this manually — no need to retry the self-service portal."
        )
    else:
        parts.append("I'll help get this resolved as quickly as possible.")

    return "\n\n".join(parts)


def _insight(active: List[str], score: int) -> str:
    has = set(active)
    if has == {"user"}:
        return ("With only user input, the response is empathetic but generic. "
                "It lacks policy grounding, prior context, and concrete next actions.")
    if "system" in has and len(has) == 2:
        return ("Adding system instructions improves persona and tone, but the model still lacks "
                "policy facts and enough context to act decisively.")
    if "history" in has and "knowledge" not in has and "tools" not in has:
        return ("Conversation history stops the model from asking for already-provided details "
                "and significantly improves continuity and personalization.")
    if "knowledge" in has and "tools" not in has:
        return ("Retrieved knowledge reduces hallucination and improves policy accuracy because "
                "the model now has the actual return and replacement rules.")
    if "tools" in has and "state" not in has:
        return ("Tool definitions make the response more actionable — the model can now propose "
                "concrete operational next steps instead of vague promises.")
    if "state" in has:
        return ("Full context produces the strongest result: empathetic, policy-aware, personalized, "
                "and action-oriented with realistic next actions.")
    return f"Score {score}/100 - adding more context layers improves every dimension."


def _latency(active: List[str]) -> int:
    return 900 + (_token_count(active) * 4) + random.randint(50, 250)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/meta", response_model=ContextMetaResponse)
def get_meta() -> ContextMetaResponse:
    return ContextMetaResponse(
        max_budget=MAX_BUDGET,
        ordered_layers=ORDERED_LAYERS,
        layers=[LayerDTO(**m) for m in LAYER_META_CONTEXT],
    )


@router.get("/history", response_model=List[HistoryRow])
def get_history() -> List[HistoryRow]:
    return sorted(_history, key=lambda r: r.run_id)


@router.get("/history/{run_id}", response_model=EvaluateResponse)
def get_run_by_id(run_id: int) -> EvaluateResponse:
    result = _details.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result


@router.delete("/history")
def reset_history() -> dict:
    global _history, _details, _run_counter
    _history = _build_history()
    _details = _build_details()
    _run_counter = len(SEEDED_RUNS_CONTEXT)
    return {"message": "Run history reset to seeded state", "cleared": True}


@router.post("/assemble")
def assemble(payload: EvaluateRequest) -> dict:
    active = _normalize(payload.active_layers)
    return {
        "active_layers": active,
        "token_budget_used": _token_count(active),
        "token_budget_max": MAX_BUDGET,
        "assembled_prompt": _assembled(active),
    }


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(payload: EvaluateRequest) -> EvaluateResponse:
    global _run_counter

    active = _normalize(payload.active_layers)
    used = _token_count(active)

    if used > MAX_BUDGET:
        raise HTTPException(status_code=400, detail="Token budget exceeded")

    breakdown = _score(active)
    score = _score_total(breakdown)
    response_text = _mock_response(active)
    insight_text = _insight(active, score)
    latency = _latency(active)

    if payload.run_id is not None:
        run_id = payload.run_id
    else:
        _run_counter += 1
        run_id = _run_counter

    result = EvaluateResponse(
        run_id=run_id,
        provider=payload.provider,
        active_layers=active,
        active_count=len(active),
        token_budget_used=used,
        token_budget_max=MAX_BUDGET,
        assembled_prompt=_assembled(active),
        model_response=response_text,
        breakdown=breakdown,
        score=score,
        latency_ms=latency,
        insight=insight_text,
    )

    row = HistoryRow(
        run_id=run_id,
        active_layers=active,
        score=score,
        tokens=used,
        latency_ms=latency,
        provider=payload.provider,
    )

    existing = next((i for i, h in enumerate(_history) if h.run_id == run_id), None)
    if existing is None:
        _history.append(row)
    else:
        _history[existing] = row

    _details[run_id] = result
    return result
