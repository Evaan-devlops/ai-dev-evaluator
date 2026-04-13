from __future__ import annotations

from app.schemas.workbench import ContextLayerSchema, RunScoreBreakdownSchema


def _active_set(layers: list[ContextLayerSchema]) -> set[str]:
    return {layer.id for layer in layers if layer.enabled}


def _cap(value: int) -> int:
    return min(5, value)


def score_run(layers: list[ContextLayerSchema]) -> RunScoreBreakdownSchema:
    """
    Deterministic rule-based scoring.
    Each dimension starts at 1 and gains points based on which layers are enabled.
    Each dimension is capped at 5. Total (quality_score) max is 40.
    """
    active = _active_set(layers)
    active_count = len(active)

    persona_adherence = 1
    if "system" in active:
        persona_adherence += 3
    if "state" in active:
        persona_adherence += 1
    persona_adherence = _cap(persona_adherence)

    policy_accuracy = 1
    if "knowledge" in active:
        policy_accuracy += 3
    if "system" in active:
        policy_accuracy += 1
    policy_accuracy = _cap(policy_accuracy)

    empathy_tone = 1
    if "system" in active:
        empathy_tone += 2
    if "history" in active:
        empathy_tone += 1
    empathy_tone = _cap(empathy_tone)

    context_awareness = 1
    if "history" in active:
        context_awareness += 2
    if "state" in active:
        context_awareness += 1
    if "knowledge" in active:
        context_awareness += 1
    context_awareness = _cap(context_awareness)

    actionability = 1
    if "tools" in active:
        actionability += 3
    if "knowledge" in active:
        actionability += 1
    actionability = _cap(actionability)

    personalization = 1
    if "state" in active:
        personalization += 3
    if "system" in active:
        personalization += 1
    personalization = _cap(personalization)

    no_hallucination = 1
    if "knowledge" in active:
        no_hallucination += 2
    if "tools" in active:
        no_hallucination += 1
    no_hallucination = _cap(no_hallucination)

    # completeness: +1 per 2 active layers, max +4
    completeness_bonus = min(4, active_count // 2)
    completeness = _cap(1 + completeness_bonus)

    return RunScoreBreakdownSchema(
        persona_adherence=persona_adherence,
        policy_accuracy=policy_accuracy,
        empathy_tone=empathy_tone,
        context_awareness=context_awareness,
        actionability=actionability,
        personalization=personalization,
        no_hallucination=no_hallucination,
        completeness=completeness,
    )


def build_insight(active: set[str]) -> str:
    """Return an insight string describing the impact of the current layer combination."""
    all_layers = {"system", "user", "history", "knowledge", "tools", "state"}

    if active == {"user"}:
        return (
            "Without context layers, the model has no persona, policy knowledge, or "
            "customer history. Response is generic and unhelpful."
        )
    if "system" in active and "knowledge" not in active and "history" not in active:
        return (
            "System instructions give the model a persona and tone. Empathy improves "
            "but specific resolution is still missing."
        )
    if "knowledge" in active and "tools" not in active:
        return (
            "Retrieved knowledge enables policy-accurate responses. The model can now "
            "cite specific return windows and known portal issues."
        )
    if "tools" in active and "history" not in active and "state" not in active:
        return (
            "With tool definitions available, the model can propose concrete actions "
            "like replacement orders and service credits."
        )
    if all_layers.issubset(active):
        return (
            "Full context produces a highly personalized, policy-accurate, actionable "
            "response. The model leverages all available signals optimally."
        )

    # Fallback for partial combinations
    parts: list[str] = []
    if "system" in active:
        parts.append("persona and tone guidance")
    if "knowledge" in active:
        parts.append("policy-accurate information")
    if "tools" in active:
        parts.append("actionable tool calls")
    if "history" in active:
        parts.append("prior conversation context")
    if "state" in active:
        parts.append("personalized customer data")

    if parts:
        return f"Active layers provide: {', '.join(parts)}. Add more layers to improve response quality."
    return "No meaningful context layers active. Enable layers to improve the response."
