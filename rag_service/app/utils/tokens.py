from __future__ import annotations

import math


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, math.ceil(len(text.strip()) / 4))


def fits_in_budget(texts: list[str], max_tokens: int) -> list[str]:
    """Return as many texts as fit within the token budget."""
    result: list[str] = []
    used = 0
    for text in texts:
        t = estimate_tokens(text)
        if used + t > max_tokens:
            break
        result.append(text)
        used += t
    return result
