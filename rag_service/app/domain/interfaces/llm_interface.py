from __future__ import annotations

from typing import Protocol, Any


class LLMInterface(Protocol):
    """Swappable LLM provider interface."""

    async def generate_text(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str:
        ...

    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 800,
    ) -> dict[str, Any]:
        ...

    async def generate_embedding(self, text: str) -> list[float]:
        ...
