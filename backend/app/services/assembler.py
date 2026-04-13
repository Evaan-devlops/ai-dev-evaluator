from __future__ import annotations

from app.schemas.workbench import AssembleResponse, ContextLayerSchema


LAYER_LABELS: dict[str, str] = {
    "system": "=== SYSTEM INSTRUCTIONS ===",
    "user": "=== USER INPUT ===",
    "history": "=== CONVERSATION HISTORY ===",
    "knowledge": "=== RETRIEVED KNOWLEDGE ===",
    "tools": "=== TOOL DEFINITIONS ===",
    "state": "=== STATE & MEMORY ===",
}


def _estimate_tokens(text: str) -> int:
    """Simple character-based token estimate: chars / 4."""
    return max(1, len(text) // 4)


def assemble_prompt(layers: list[ContextLayerSchema]) -> AssembleResponse:
    """
    Assembles enabled layers in order into a single prompt string.
    Returns the assembled prompt, per-layer token counts, and total tokens.
    """
    sorted_layers = sorted(layers, key=lambda layer: layer.order)
    enabled_layers = [layer for layer in sorted_layers if layer.enabled]

    sections: list[str] = []
    per_layer_tokens: dict[str, int] = {}

    for layer in enabled_layers:
        label = LAYER_LABELS.get(layer.id, f"=== {layer.id.upper()} ===")
        section_text = f"{label}\n{layer.content}"
        sections.append(section_text)
        per_layer_tokens[layer.id] = _estimate_tokens(layer.content)

    assembled_prompt = "\n\n".join(sections)
    total_tokens = sum(per_layer_tokens.values())

    return AssembleResponse(
        assembled_prompt=assembled_prompt,
        per_layer_tokens=per_layer_tokens,
        total_tokens=total_tokens,
    )
