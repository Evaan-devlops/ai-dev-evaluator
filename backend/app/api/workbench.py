from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.data.seeds import DEFAULT_LAYERS, SEEDED_RUNS
from app.schemas.workbench import (
    AssembleRequest,
    AssembleResponse,
    ContextLayerSchema,
    DefaultsResponse,
    ResetResponse,
    RunHistoryItemSchema,
    RunRequest,
    RunResultSchema,
    RunScoreBreakdownSchema,
)
from app.services.assembler import assemble_prompt
from app.services.evaluator import build_insight, score_run
from app.services.provider import generate_mock_response

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])

# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------

def _build_default_layers() -> list[ContextLayerSchema]:
    return [ContextLayerSchema(**layer) for layer in DEFAULT_LAYERS]


def _build_seeded_runs() -> tuple[list[RunHistoryItemSchema], dict[str, RunResultSchema]]:
    history: list[RunHistoryItemSchema] = []
    details: dict[str, RunResultSchema] = {}
    for run_data in SEEDED_RUNS:
        result = RunResultSchema(
            run_id=run_data["run_id"],
            run_number=run_data["run_number"],
            quality_score=run_data["quality_score"],
            score_max=run_data["score_max"],
            score_breakdown=RunScoreBreakdownSchema(**run_data["score_breakdown"]),
            insight=run_data["insight"],
            llm_response=run_data["llm_response"],
            latency_ms=run_data["latency_ms"],
            total_tokens=run_data["total_tokens"],
            active_layers=run_data["active_layers"],
            timestamp=run_data["timestamp"],
        )
        details[run_data["run_id"]] = result
        history.append(
            RunHistoryItemSchema(
                run_id=run_data["run_id"],
                run_number=run_data["run_number"],
                active_layers=run_data["active_layers"],
                quality_score=run_data["quality_score"],
                score_max=run_data["score_max"],
                total_tokens=run_data["total_tokens"],
                latency_ms=run_data["latency_ms"],
            )
        )
    return history, details


_run_history, _run_details = _build_seeded_runs()
_run_counter: int = len(SEEDED_RUNS)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/defaults", response_model=DefaultsResponse)
def get_defaults() -> DefaultsResponse:
    layers = _build_default_layers()
    initial_result = _run_details.get("seed-run-005") if _run_details else None
    return DefaultsResponse(
        layers=layers,
        token_budget_max=4000,
        run_history=list(_run_history),
        initial_result=initial_result,
    )


@router.post("/assemble", response_model=AssembleResponse)
def assemble(request: AssembleRequest) -> AssembleResponse:
    if not request.layers:
        raise HTTPException(status_code=422, detail="layers must not be empty")
    return assemble_prompt(request.layers)


@router.post("/run", response_model=RunResultSchema)
def run_workbench(request: RunRequest) -> RunResultSchema:
    global _run_counter

    if not request.layers:
        raise HTTPException(status_code=422, detail="layers must not be empty")

    active_layers = [layer.id for layer in request.layers if layer.enabled]
    if not active_layers:
        raise HTTPException(status_code=422, detail="At least one layer must be enabled")

    breakdown = score_run(request.layers)
    quality_score = (
        breakdown.persona_adherence
        + breakdown.policy_accuracy
        + breakdown.empathy_tone
        + breakdown.context_awareness
        + breakdown.actionability
        + breakdown.personalization
        + breakdown.no_hallucination
        + breakdown.completeness
    )

    active_set = {layer.id for layer in request.layers if layer.enabled}
    insight = build_insight(active_set)
    llm_response, latency_ms = generate_mock_response(request.layers)

    # Calculate tokens from assembled prompt
    from app.services.assembler import _estimate_tokens
    total_tokens = _estimate_tokens(request.assembled_prompt) if request.assembled_prompt else sum(
        _estimate_tokens(layer.content) for layer in request.layers if layer.enabled
    )

    _run_counter += 1
    run_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    result = RunResultSchema(
        run_id=run_id,
        run_number=_run_counter,
        quality_score=quality_score,
        score_max=40,
        score_breakdown=breakdown,
        insight=insight,
        llm_response=llm_response,
        latency_ms=latency_ms,
        total_tokens=total_tokens,
        active_layers=active_layers,
        timestamp=timestamp,
    )

    history_item = RunHistoryItemSchema(
        run_id=run_id,
        run_number=_run_counter,
        active_layers=active_layers,
        quality_score=quality_score,
        score_max=40,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
    )

    _run_details[run_id] = result
    _run_history.append(history_item)

    return result


@router.get("/runs", response_model=list[RunHistoryItemSchema])
def list_runs() -> list[RunHistoryItemSchema]:
    return list(_run_history)


@router.get("/runs/{run_id}", response_model=RunResultSchema)
def get_run(run_id: str) -> RunResultSchema:
    result = _run_details.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")
    return result


@router.post("/reset-demo", response_model=ResetResponse)
def reset_demo() -> ResetResponse:
    global _run_history, _run_details, _run_counter
    _run_history, _run_details = _build_seeded_runs()
    _run_counter = len(SEEDED_RUNS)
    return ResetResponse(message="Demo reset to initial seeded state", run_history_cleared=True)
