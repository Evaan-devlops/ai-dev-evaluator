from __future__ import annotations

import random
import time

from app.schemas.workbench import ContextLayerSchema


def _active_set(layers: list[ContextLayerSchema]) -> set[str]:
    return {layer.id for layer in layers if layer.enabled}


def generate_mock_response(layers: list[ContextLayerSchema]) -> tuple[str, int]:
    """
    Returns a (response_text, latency_ms) tuple.
    Response content is determined by which layers are active.
    Latency is deterministic based on active layer count.
    """
    active = _active_set(layers)
    base_latency = 180 + len(active) * 55
    latency_ms = base_latency + random.randint(-10, 10)

    has_system = "system" in active
    has_history = "history" in active
    has_knowledge = "knowledge" in active
    has_tools = "tools" in active
    has_state = "state" in active

    customer_name = "Marcus" if has_state else None
    greeting_name = f" {customer_name}" if customer_name else ""
    tier_note = " As a Platinum member, you deserve nothing less than our best." if has_state else ""

    if not has_system and not has_knowledge and not has_tools and not has_state and not has_history:
        # Only user (or nothing)
        return (
            "I'm sorry to hear you're having trouble with your headphones. "
            "Please contact our support team for assistance with your return. "
            "You can reach us at support@novatech.com or call 1-800-NOVATECH.",
            latency_ms,
        )

    paragraphs: list[str] = []

    # Opening — persona-driven if system is on
    if has_system:
        apology_parts: list[str] = ["I'm Alex, Senior Resolution Specialist at NovaTech Electronics."]
        apology_parts.append(f"Hi{greeting_name}! " + apology_parts.pop(0))
        apology_parts.append(
            "I completely understand your frustration, and I sincerely apologize for everything "
            "you've been through to get here."
        )
        if has_history:
            apology_parts.append(
                "I can see you spoke with us two days ago about Order #NT-2024-88341 — the fact that "
                "the session ended without a resolution is unacceptable, and I'm sorry you had to call back."
            )
        paragraphs.append(" ".join(apology_parts))
    else:
        paragraphs.append(
            f"Hello{greeting_name}. I understand you're having an issue with your headphones. "
            "Let me see what I can do."
        )

    # Policy details — only if knowledge is on
    if has_knowledge:
        policy_para = (
            "Regarding the portal issue: we have a known bug (INC-2024-1147) affecting orders "
            "placed November 10–20, 2024 — yours falls in exactly that window, which is why you've "
            "been seeing error code 4042. I sincerely apologize; you've been fighting a system bug "
            "that was entirely our fault. For your ProAudio X1, since this is a confirmed hardware "
            "defect, our policy provides a 45-day return window (not the standard 30), and we use "
            "an advanced replacement workflow — meaning your replacement ships before you send back "
            "the original. You're also entitled to a $15 inconvenience credit for the portal issue."
        )
        paragraphs.append(policy_para)

    # Tool action steps — only if tools is on
    if has_tools:
        action_parts = ["Here is exactly what I'm doing right now:"]
        action_parts.append(
            "\n1. Running lookup_order(\"NT-2024-88341\") to confirm your order and warranty status."
        )
        action_parts.append(
            "\n2. Initiating process_replacement(\"NT-2024-88341\", \"PA-X1-BLK\", \"express\") — "
            "your replacement will arrive in 1-2 business days. A prepaid return label will be "
            "emailed to you within the hour."
        )
        action_parts.append(
            "\n3. Issuing a service credit via issue_service_credit — "
            "$15 for the portal issue (PORTAL-4042) and $10 for the disconnection."
        )
        paragraphs.append("".join(action_parts))
    elif has_knowledge:
        paragraphs.append(
            "To resolve this, I'll process your replacement manually right now. "
            "You can expect a prepaid return shipping label via email shortly. "
            "The $15 credit will be applied to your account for your next purchase."
        )

    # Personalization close — only if state is on
    if has_state:
        close_para = (
            f"Marcus, you've been with NovaTech for over six years and have a perfect payment record "
            f"and zero dispute history.{tier_note} "
            "I will personally monitor this case until your replacement is in your hands. "
            "Thank you for your patience, and I'm sorry again for making you fight this hard for a resolution you deserved on day one."
        )
        paragraphs.append(close_para)
    elif has_system:
        paragraphs.append(
            "Please don't hesitate to reach out if there's anything else I can do. "
            "I'm committed to making sure this is fully resolved for you today."
        )

    return "\n\n".join(paragraphs), latency_ms
