from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import LLMError


class LLMProvider:
    """Unified LLM provider — uses settings.LLM_PROVIDER to dispatch."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        access_token: str | None = None,
        embedding_model: str | None = None,
        embedding_token: str | None = None,
    ) -> None:
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.access_token = access_token or settings.LLM_ACCESS_TOKEN
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL
        self.embedding_token = embedding_token or settings.EMBEDDING_ACCESS_TOKEN

    async def generate_text(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str:
        if not self.access_token:
            return f"[mock] {prompt[:200]}"

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                if self.provider == "openai":
                    return await self._openai_generate(client, prompt, system, max_tokens, temperature)
                if self.provider == "gemini":
                    return await self._gemini_generate(client, prompt, system, max_tokens, temperature)
                return await self._openai_generate(client, prompt, system, max_tokens, temperature)
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM request failed: {exc}") from exc

    async def generate_structured(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 800,
    ) -> dict[str, Any]:
        raw = await self.generate_text(
            prompt,
            system=system or "Respond with valid JSON only.",
            max_tokens=max_tokens,
            temperature=0.0,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(lines[1:-1]) if len(lines) >= 3 else raw
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(raw[start:end + 1])
                except json.JSONDecodeError:
                    pass
        return {}

    async def generate_embedding(self, text: str) -> list[float]:
        token = self.embedding_token or self.access_token
        if not token or not text.strip():
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"model": self.embedding_model, "input": text[:8000]},
                )
                response.raise_for_status()
                data = response.json()
                embedding = data.get("data", [{}])[0].get("embedding", [])
                return [float(v) for v in embedding]
        except httpx.HTTPError as exc:
            raise LLMError(f"Embedding request failed: {exc}") from exc

    async def _openai_generate(
        self,
        client: httpx.AsyncClient,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        return str(response.json().get("choices", [{}])[0].get("message", {}).get("content", "")).strip()

    async def _gemini_generate(
        self,
        client: httpx.AsyncClient,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        body: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        response = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            params={"key": self.access_token},
            json=body,
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        return "\n".join(str(p.get("text", "")) for p in parts if p.get("text")).strip()


_default_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = LLMProvider()
    return _default_provider
