"""Demo seed data for the /api/context/ endpoints.

Uses the new API shape expected by the frontend:
- integer run_ids
- new breakdown field names (persona, policy, empathy, context,
  actionability, personalization, hallucination, completeness)
"""
from __future__ import annotations

from app.data.seeds import (
    SYSTEM_CONTENT,
    USER_CONTENT,
    HISTORY_CONTENT,
    KNOWLEDGE_CONTENT,
    TOOLS_CONTENT,
    STATE_CONTENT,
    _RESPONSE_USER_ONLY,
    _RESPONSE_SYSTEM_USER,
    _RESPONSE_SYSTEM_USER_KNOWLEDGE,
    _RESPONSE_5_LAYERS,
    _RESPONSE_ALL_LAYERS,
)

MAX_BUDGET = 4000

ORDERED_LAYERS = ["system", "user", "history", "knowledge", "tools", "state"]

LAYER_META_CONTEXT = [
    {
        "key": "system",
        "id": 1,
        "name": "System Instructions",
        "subtitle": "Who the model is, how it should behave, what rules to follow",
        "tokens": 300,
        "always_on": False,
        "warning": "Generic bot voice, no persona, no empathy-first rule, no agent identity",
        "content": SYSTEM_CONTENT,
    },
    {
        "key": "user",
        "id": 2,
        "name": "User Input",
        "subtitle": "The current message from the customer (always on)",
        "tokens": 110,
        "always_on": True,
        "warning": None,
        "content": USER_CONTENT,
    },
    {
        "key": "history",
        "id": 3,
        "name": "Conversation History",
        "subtitle": "Prior turns maintaining coherence and avoiding repetition",
        "tokens": 400,
        "always_on": False,
        "warning": "Suggests self-service again, forgets order #, ignores prior troubleshooting",
        "content": HISTORY_CONTENT,
    },
    {
        "key": "knowledge",
        "id": 4,
        "name": "Retrieved Knowledge",
        "subtitle": "RAG results: policies, docs, database records",
        "tokens": 600,
        "always_on": False,
        "warning": "Hallucinating 30-day policy (actual: 45-day audio, 90-day Platinum override)",
        "content": KNOWLEDGE_CONTENT,
    },
    {
        "key": "tools",
        "id": 5,
        "name": "Tool Definitions",
        "subtitle": "Available tools the model can call to take action",
        "tokens": 300,
        "always_on": False,
        "warning": None,
        "content": TOOLS_CONTENT,
    },
    {
        "key": "state",
        "id": 6,
        "name": "State & Memory",
        "subtitle": "Persistent facts: customer profile, session context, metadata",
        "tokens": 200,
        "always_on": False,
        "warning": "One-size-fits-all response, ignores Platinum tier and professional use case",
        "content": STATE_CONTENT,
    },
]


def _assembled(active: list[str]) -> str:
    """Build a minimal assembled prompt string for seeded runs."""
    content = {m["key"]: m["content"] for m in LAYER_META_CONTEXT}
    parts = []
    if "system" in active:
        parts.append(f"[SYSTEM]\n{content['system'].strip()}")
    for k in ["history", "knowledge", "tools", "state"]:
        if k in active:
            parts.append(f"[{k.upper()}]\n{content[k].strip()}")
    parts.append(f"[USER]\n{content['user'].strip()}")
    return "\n\n".join(parts)


# Seeded runs — oldest first (run_id 1 = oldest, 5 = newest/best)
SEEDED_RUNS_CONTEXT: list[dict] = [
    {
        "run_id": 1,
        "provider": "mock-provider",
        "active_layers": ["user"],
        "active_count": 1,
        "token_budget_used": 110,
        "token_budget_max": MAX_BUDGET,
        "assembled_prompt": _assembled(["user"]),
        "model_response": _RESPONSE_USER_ONLY,
        "breakdown": {
            "persona": 2,
            "policy": 1,
            "empathy": 4,
            "context": 1,
            "actionability": 2,
            "personalization": 1,
            "hallucination": 4,
            "completeness": 3,
        },
        "score": 18,
        "latency_ms": 8200,
        "insight": (
            "Without context layers, the model has no persona, policy knowledge, or customer history. "
            "Response is generic, suggests self-service (already broken), and provides no real resolution."
        ),
    },
    {
        "run_id": 2,
        "provider": "mock-provider",
        "active_layers": ["system", "user"],
        "active_count": 2,
        "token_budget_used": 410,
        "token_budget_max": MAX_BUDGET,
        "assembled_prompt": _assembled(["system", "user"]),
        "model_response": _RESPONSE_SYSTEM_USER,
        "breakdown": {
            "persona": 5,
            "policy": 1,
            "empathy": 5,
            "context": 2,
            "actionability": 1,
            "personalization": 2,
            "hallucination": 2,
            "completeness": 5,
        },
        "score": 23,
        "latency_ms": 5900,
        "insight": (
            "System instructions give the model a persona and empathy-first tone. Alex introduces "
            "herself and takes ownership. But without policy knowledge, she can't cite specific "
            "return windows, portal incident details, or concrete resolution steps."
        ),
    },
    {
        "run_id": 3,
        "provider": "mock-provider",
        "active_layers": ["system", "user", "history"],
        "active_count": 3,
        "token_budget_used": 810,
        "token_budget_max": MAX_BUDGET,
        "assembled_prompt": _assembled(["system", "user", "history"]),
        "model_response": _RESPONSE_SYSTEM_USER,
        "breakdown": {
            "persona": 5,
            "policy": 2,
            "empathy": 5,
            "context": 5,
            "actionability": 1,
            "personalization": 4,
            "hallucination": 3,
            "completeness": 3,
        },
        "score": 28,
        "latency_ms": 5700,
        "insight": (
            "Conversation history stops the model from asking for details the customer already "
            "provided and significantly improves continuity and personalization."
        ),
    },
    {
        "run_id": 4,
        "provider": "mock-provider",
        "active_layers": ["system", "user", "history", "knowledge", "tools"],
        "active_count": 5,
        "token_budget_used": 1610,
        "token_budget_max": MAX_BUDGET,
        "assembled_prompt": _assembled(["system", "user", "history", "knowledge", "tools"]),
        "model_response": _RESPONSE_5_LAYERS,
        "breakdown": {
            "persona": 5,
            "policy": 4,
            "empathy": 5,
            "context": 5,
            "actionability": 5,
            "personalization": 3,
            "hallucination": 2,
            "completeness": 1,
        },
        "score": 30,
        "latency_ms": 8200,
        "insight": (
            "The model now references specific tools: process_replacement() for express shipping and "
            "issue_service_credit() for the inconvenience. The response becomes actionable, not just "
            "sympathetic. Without state, response still treats the customer somewhat generically."
        ),
    },
    {
        "run_id": 5,
        "provider": "mock-provider",
        "active_layers": ["system", "user", "history", "knowledge", "tools", "state"],
        "active_count": 6,
        "token_budget_used": 1810,
        "token_budget_max": MAX_BUDGET,
        "assembled_prompt": _assembled(["system", "user", "history", "knowledge", "tools", "state"]),
        "model_response": _RESPONSE_ALL_LAYERS,
        "breakdown": {
            "persona": 5,
            "policy": 3,
            "empathy": 5,
            "context": 5,
            "actionability": 5,
            "personalization": 5,
            "hallucination": 2,
            "completeness": 4,
        },
        "score": 34,
        "latency_ms": 8900,
        "insight": (
            "Full context produces a highly personalized, policy-accurate, actionable response. "
            "Marcus is addressed by name, Platinum tier acknowledged, professional use case noted, "
            "and specific tool calls are proposed. The model leverages all available signals optimally."
        ),
    },
]

# The best seeded run (highest score) — used as initial_result on page load
BEST_SEEDED_RUN_ID = 5
