from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import random

app = FastAPI(title="Context Lab Mock Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Enums / constants
# =========================
class Provider(str, Enum):
    gemini = "gemini-2.5-flash"
    openai = "gpt-4o-mini"
    mock = "mock-provider"


class LayerKey(str, Enum):
    system = "system"
    user = "user"
    history = "history"
    knowledge = "knowledge"
    tools = "tools"
    state = "state"


ORDERED_LAYERS = [
    LayerKey.system,
    LayerKey.user,
    LayerKey.history,
    LayerKey.knowledge,
    LayerKey.tools,
    LayerKey.state,
]

MAX_TOKEN_BUDGET = 4000

LAYER_META: Dict[LayerKey, Dict] = {
    LayerKey.system: {
        "id": 1,
        "name": "System Instructions",
        "subtitle": "Who the model is, how it should behave, what rules to follow",
        "tokens": 228,
        "warning": "Generic bot voice, no persona, no empathy-first rule, no agent identity",
        "content": """You are Alex, a Senior Resolution Specialist at NovaTech Electronics.
You have 8 years of experience and authority to approve resolutions up to $2,000 without manager approval.

CORE RULES:
- Always lead with empathy BEFORE offering solutions
- Use the customer's first name naturally in conversation
- Never say 'I can't' or 'that's not possible'; frame what you CAN do
- Acknowledge every frustration the customer mentions before moving forward
- Take personal ownership: say 'I will' instead of 'the team will'
- If the customer had a bad experience, apologize explicitly for it
- Introduce yourself by name and role when appropriate
- When policy details are available, cite specific policy numbers when proposing a solution
""",
    },
    LayerKey.user: {
        "id": 2,
        "name": "User Input",
        "subtitle": "The current message from the customer (always on)",
        "tokens": 109,
        "always_on": True,
        "content": """No! The portal just gave me some error - it wouldn't let me submit anything. So I called your support line and sat on hold for 45 MINUTES before I got disconnected. This is now my third attempt to get this resolved. I'm absolutely livid - these are $1,899 headphones that I need for my professional work and the left ear is crackling after barely a month. I'm about to dispute this on my credit card if someone doesn't fix this RIGHT NOW.""",
    },
    LayerKey.history: {
        "id": 3,
        "name": "Conversation History",
        "subtitle": "Prior turns maintaining coherence and avoiding repetition",
        "tokens": 271,
        "warning": "Suggests self-service again, forgets order #, ignores prior troubleshooting",
        "content": """[user] Hi, I need help with a defective product. Order number NVT-2024-91847.
[assistant] I'd be happy to help you with that. I can see this is for the NovaSound Pro 3000 headphones purchased on January 15th. What issue are you experiencing?
[user] The left ear has developed a crackling sound. I already tried the troubleshooting steps on your website - reset the headphones, updated firmware, tried different audio sources. Nothing works. It's clearly a hardware defect.
[assistant] Thank you for trying those troubleshooting steps, Marcus. The crackling in the left ear after firmware updates and resets does sound like a hardware issue. Let me look into the best resolution options for you. Were you able to submit a return through the portal?""",
    },
    LayerKey.knowledge: {
        "id": 4,
        "name": "Retrieved Knowledge",
        "subtitle": "RAG results: policies, docs, database records",
        "tokens": 518,
        "warning": "Hallucinating 30-day policy (actual: 45-day audio, 90-day Platinum override)",
        "content": """POLICY EXCERPTS
- Premium audio devices have a 45-day return/replacement window for manufacturing defects.
- Platinum customers receive an extended 90-day replacement eligibility override for defective premium devices.
- No restocking fee applies to confirmed defective items.
- If self-service portal fails for orders placed before February 1st, agent-assisted manual processing is allowed.
- When portal failure and support delay both occurred, agent may issue up to $15 inconvenience credit.
- Senior Resolution Specialists may approve replacements/refunds up to $2,000.

ORDER SNAPSHOT
- Customer: Marcus Rivera
- Tier: Platinum
- Lifetime spend: $12,400
- Product: NovaSound Pro 3000
- Price paid: $1,899
- Purchase date: 2026-01-15
- Issue reported within warranty window: Yes""",
    },
    LayerKey.tools: {
        "id": 5,
        "name": "Tool Definitions",
        "subtitle": "Available tools the model can call to take action",
        "tokens": 318,
        "warning": "Vague promises instead of concrete actions like process_replacement()",
        "content": """### lookup_order(order_id: string)
Look up full order details including items, pricing, dates, and current status.
Returns: order details, shipping info, payment method, and return eligibility.

### process_replacement(order_id: string, item_sku: string, shipping_priority: 'standard' | 'express' | 'overnight')
Initiate a replacement shipment for a defective item.
Returns: replacement order ID, tracking number, estimated delivery date.

### issue_refund(order_id: string, amount: number, reason: string)
Initiate a refund to the original payment method.
Returns: refund case ID, refund ETA.

### issue_service_credit(customer_id: string, amount: number, reason: string)
Add a service credit to the customer's NovaTech account.
Returns: credit confirmation, new account balance.

### escalate_to_supervisor(case_id: string, reason: string, priority: 'normal' | 'urgent')
Escalate the case to a supervisor with full context.
Returns: escalation ticket ID, estimated callback time.""",
    },
    LayerKey.state: {
        "id": 6,
        "name": "State & Memory",
        "subtitle": "Persistent facts: customer profile, session context, metadata",
        "tokens": 231,
        "warning": "One-size-fits-all response, ignores Platinum tier and professional use case",
        "content": """SESSION / MEMORY
- Customer first name: Marcus
- Customer tier: Platinum
- Satisfaction risk: High
- Recent experience markers: portal failure, long hold, disconnect, third attempt
- Use case: professional audio work
- Preferred resolution style: direct, ownership-driven, low back-and-forth
- Recommended posture: acknowledge frustration, avoid asking for already-known details, propose action immediately
- Case priority: urgent retention risk""",
    },
}


# =========================
# Request / response models
# =========================
class LayerDTO(BaseModel):
    key: LayerKey
    id: int
    name: str
    subtitle: str
    tokens: int
    always_on: bool = False
    warning: Optional[str] = None
    content: str


class ContextMetaResponse(BaseModel):
    max_budget: int
    ordered_layers: List[LayerKey]
    layers: List[LayerDTO]


class ScoreBreakdown(BaseModel):
    persona: int = Field(ge=0, le=5)
    policy: int = Field(ge=0, le=5)
    empathy: int = Field(ge=0, le=5)
    context: int = Field(ge=0, le=5)
    actionability: int = Field(ge=0, le=5)
    personalization: int = Field(ge=0, le=5)
    hallucination: int = Field(ge=0, le=5)
    completeness: int = Field(ge=0, le=5)

    @property
    def total(self) -> int:
        return (
            self.persona
            + self.policy
            + self.empathy
            + self.context
            + self.actionability
            + self.personalization
            + self.hallucination
            + self.completeness
        )


class EvaluateRequest(BaseModel):
    provider: Provider = Provider.mock
    active_layers: List[LayerKey]
    run_id: Optional[int] = None


class EvaluateResponse(BaseModel):
    run_id: int
    provider: Provider
    active_layers: List[LayerKey]
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
    active_layers: List[LayerKey]
    score: int
    tokens: int
    latency_ms: int
    provider: Provider


# =========================
# Helpers
# =========================
def layer_to_dto(key: LayerKey) -> LayerDTO:
    meta = LAYER_META[key]
    return LayerDTO(
        key=key,
        id=meta["id"],
        name=meta["name"],
        subtitle=meta["subtitle"],
        tokens=meta["tokens"],
        always_on=meta.get("always_on", False),
        warning=meta.get("warning"),
        content=meta["content"],
    )


def normalize_layers(layers: List[LayerKey]) -> List[LayerKey]:
    layer_set = set(layers)
    layer_set.add(LayerKey.user)  # user is always on
    return [layer for layer in ORDERED_LAYERS if layer in layer_set]


def build_prompt(active_layers: List[LayerKey]) -> str:
    sections: List[str] = []

    if LayerKey.system in active_layers:
        sections.append(f"[SYSTEM]\n{LAYER_META[LayerKey.system]['content'].strip()}")

    for middle_key in [LayerKey.history, LayerKey.knowledge, LayerKey.tools, LayerKey.state]:
        if middle_key in active_layers:
            sections.append(f"[{middle_key.value.upper()}]\n{LAYER_META[middle_key]['content'].strip()}")

    sections.append(f"[USER]\n{LAYER_META[LayerKey.user]['content'].strip()}")
    return "\n\n".join(sections)


def token_count(active_layers: List[LayerKey]) -> int:
    return sum(LAYER_META[layer]["tokens"] for layer in active_layers)


def score_layers(active_layers: List[LayerKey]) -> ScoreBreakdown:
    has = set(active_layers)

    breakdown = ScoreBreakdown(
        persona=1,
        policy=1,
        empathy=2,
        context=1,
        actionability=0,
        personalization=1,
        hallucination=2,
        completeness=4,
    )

    if LayerKey.system in has:
        breakdown.persona = 5
        breakdown.empathy = 5
        breakdown.personalization = max(breakdown.personalization, 2)
        breakdown.context = max(breakdown.context, 2)

    if LayerKey.history in has:
        breakdown.context = 5
        breakdown.personalization = max(breakdown.personalization, 3)
        breakdown.completeness = 5

    if LayerKey.knowledge in has:
        breakdown.policy = 5
        breakdown.hallucination = 5
        breakdown.context = max(breakdown.context, 4)

    if LayerKey.tools in has:
        breakdown.actionability = 5
        breakdown.completeness = 5

    if LayerKey.state in has:
        breakdown.personalization = 5
        breakdown.context = 5
        breakdown.persona = 5

    # Realism: without knowledge, policy stays capped
    if LayerKey.system in has and LayerKey.knowledge not in has:
        breakdown.actionability = min(breakdown.actionability, 1)
        breakdown.policy = min(breakdown.policy, 3)

    return breakdown


def build_mock_response(active_layers: List[LayerKey]) -> str:
    has = set(active_layers)

    if has == {LayerKey.user}:
        return (
            "Oh no, I'm really sorry you're dealing with this. I completely understand how "
            "frustrating that must be, especially after trying multiple times. Could you please "
            "share your order number and the email used for the purchase so I can look into "
            "the next steps for you?"
        )

    parts: List[str] = []

    if LayerKey.system in has:
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

    if LayerKey.history in has:
        parts.append(
            "I can also see you've already completed the troubleshooting steps and previously "
            "shared order number NVT-2024-91847, so I won't ask you to repeat information "
            "you've already given."
        )

    if LayerKey.knowledge in has:
        parts.append(
            "Because this is a confirmed defect on a premium audio device and you're within "
            "the eligible window, this qualifies for a manual agent-assisted replacement. "
            "There is no restocking fee for defective items."
        )

    if LayerKey.state in has:
        parts.append(
            "Given your Platinum status, your professional use case, and the fact that this "
            "is now your third attempt, I'm treating this as an urgent retention-risk case."
        )

    if LayerKey.tools in has:
        parts.append(
            "Here's what I will do next:\n"
            "1. Look up and confirm the full order details for NVT-2024-91847.\n"
            "2. Process a replacement for the defective NovaSound Pro 3000.\n"
            "3. Add a $15 inconvenience credit because the self-service portal failed and "
            "your support call disconnected."
        )
    else:
        parts.append("I'll help get this resolved as quickly as possible.")

    return "\n\n".join(parts)


def build_insight(active_layers: List[LayerKey], score: int) -> str:
    has = set(active_layers)

    if has == {LayerKey.user}:
        return (
            "With only user input, the response is empathetic but generic. It lacks policy "
            "grounding, prior context, and concrete next actions."
        )
    if LayerKey.system in has and len(has) == 2:
        return (
            "Adding system instructions improves persona and tone, but the model still lacks "
            "policy facts and enough context to act decisively."
        )
    if LayerKey.history in has and LayerKey.knowledge not in has and LayerKey.tools not in has:
        return (
            "Conversation history stops the model from asking for details the customer already "
            "provided and improves continuity."
        )
    if LayerKey.knowledge in has and LayerKey.tools not in has:
        return (
            "Retrieved knowledge reduces hallucination and improves policy accuracy because "
            "the model now has the actual return and replacement rules."
        )
    if LayerKey.tools in has and LayerKey.state not in has:
        return (
            "Tool definitions make the response more actionable because the model can propose "
            "concrete operational next steps instead of vague promises."
        )
    if LayerKey.state in has:
        return (
            "Full context produces the strongest result: empathetic, policy-aware, personalized, "
            "and action-oriented with realistic next actions."
        )
    return f"Score improved to {score}/40 as more useful context layers were added."


def latency_for(provider: Provider, layers: List[LayerKey]) -> int:
    base = {
        Provider.mock: 900,
        Provider.gemini: 1500,
        Provider.openai: 1700,
    }[provider]
    return base + (token_count(layers) * 4) + random.randint(50, 250)


# In-memory run history
RUN_HISTORY: List[HistoryRow] = []
_RUN_COUNTER: int = 0


# =========================
# Routes
# =========================
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/context/meta", response_model=ContextMetaResponse)
def get_context_meta():
    return ContextMetaResponse(
        max_budget=MAX_TOKEN_BUDGET,
        ordered_layers=ORDERED_LAYERS,
        layers=[layer_to_dto(key) for key in ORDERED_LAYERS],
    )


@app.get("/api/mock/history")
def get_mock_history():
    return {
        "history": LAYER_META[LayerKey.history]["content"],
        "tokens": LAYER_META[LayerKey.history]["tokens"],
    }


@app.get("/api/mock/knowledge")
def get_mock_knowledge():
    return {
        "knowledge": LAYER_META[LayerKey.knowledge]["content"],
        "tokens": LAYER_META[LayerKey.knowledge]["tokens"],
    }


@app.get("/api/mock/tools")
def get_mock_tools():
    return {
        "tools": LAYER_META[LayerKey.tools]["content"],
        "tokens": LAYER_META[LayerKey.tools]["tokens"],
    }


@app.get("/api/mock/state")
def get_mock_state():
    return {
        "state": LAYER_META[LayerKey.state]["content"],
        "tokens": LAYER_META[LayerKey.state]["tokens"],
    }


@app.post("/api/context/assemble")
def assemble_context(payload: EvaluateRequest):
    active_layers = normalize_layers(payload.active_layers)
    return {
        "active_layers": active_layers,
        "token_budget_used": token_count(active_layers),
        "token_budget_max": MAX_TOKEN_BUDGET,
        "assembled_prompt": build_prompt(active_layers),
    }


@app.post("/api/context/evaluate", response_model=EvaluateResponse)
def evaluate_context(payload: EvaluateRequest):
    global _RUN_COUNTER

    active_layers = normalize_layers(payload.active_layers)
    used_tokens = token_count(active_layers)

    if used_tokens > MAX_TOKEN_BUDGET:
        raise HTTPException(status_code=400, detail="Token budget exceeded")

    assembled_prompt = build_prompt(active_layers)
    response_text = build_mock_response(active_layers)
    breakdown = score_layers(active_layers)
    score = breakdown.total
    latency_ms = latency_for(payload.provider, active_layers)
    insight = build_insight(active_layers, score)

    # Use provided run_id or auto-increment
    if payload.run_id is not None:
        run_id = payload.run_id
    else:
        _RUN_COUNTER += 1
        run_id = _RUN_COUNTER

    row = HistoryRow(
        run_id=run_id,
        active_layers=active_layers,
        score=score,
        tokens=used_tokens,
        latency_ms=latency_ms,
        provider=payload.provider,
    )

    existing_index = next(
        (i for i, item in enumerate(RUN_HISTORY) if item.run_id == run_id), None
    )
    if existing_index is None:
        RUN_HISTORY.append(row)
    else:
        RUN_HISTORY[existing_index] = row

    return EvaluateResponse(
        run_id=run_id,
        provider=payload.provider,
        active_layers=active_layers,
        active_count=len(active_layers),
        token_budget_used=used_tokens,
        token_budget_max=MAX_TOKEN_BUDGET,
        assembled_prompt=assembled_prompt,
        model_response=response_text,
        breakdown=breakdown,
        score=score,
        latency_ms=latency_ms,
        insight=insight,
    )


@app.get("/api/context/history", response_model=List[HistoryRow])
def get_run_history():
    return sorted(RUN_HISTORY, key=lambda x: x.run_id)


@app.delete("/api/context/history")
def reset_history():
    global _RUN_COUNTER
    RUN_HISTORY.clear()
    _RUN_COUNTER = 0
    return {"message": "Run history cleared", "cleared": True}
