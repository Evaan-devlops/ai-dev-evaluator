from __future__ import annotations

from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/llm", tags=["llm"])

Provider = Literal["mock", "gemini", "openai", "nvidia"]


class LLMTestRequest(BaseModel):
    provider: Provider
    model: str
    api_key: str = ""


class LLMTestResponse(BaseModel):
    ok: bool
    provider: Provider
    model: str
    message: str


class LLMGenerateRequest(BaseModel):
    provider: Provider
    model: str
    api_key: str = ""
    input: str
    system_instruction: str = ""
    max_output_tokens: int = Field(default=800, ge=16)
    temperature: float = 0.2


class LLMGenerateResponse(BaseModel):
    ok: bool
    provider: Provider
    model: str
    output_text: str


class LLMEmbeddingRequest(BaseModel):
    provider: Provider
    api_key: str = ""
    text: str
    model: str = "text-embedding-3-small"


async def _test_openai(client: httpx.AsyncClient, payload: LLMTestRequest) -> None:
    response = await client.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {payload.api_key}"},
        json={
            "model": payload.model,
            "input": "Reply with OK.",
            "max_output_tokens": 16,
        },
    )
    response.raise_for_status()


async def _test_gemini(client: httpx.AsyncClient, payload: LLMTestRequest) -> None:
    response = await client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{payload.model}:generateContent",
        params={"key": payload.api_key},
        json={
            "contents": [{"parts": [{"text": "Reply with OK."}]}],
            "generationConfig": {"maxOutputTokens": 16, "temperature": 0},
        },
    )
    response.raise_for_status()


async def _test_nvidia(client: httpx.AsyncClient, payload: LLMTestRequest) -> None:
    response = await client.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {payload.api_key}"},
        json={
            "model": payload.model,
            "messages": [{"role": "user", "content": "Reply with OK."}],
            "max_tokens": 16,
            "temperature": 0,
        },
    )
    response.raise_for_status()


async def _generate_openai(client: httpx.AsyncClient, payload: LLMGenerateRequest) -> str:
    response = await client.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {payload.api_key}"},
        json={
            "model": payload.model,
            "input": payload.input,
            "instructions": payload.system_instruction or None,
            "max_output_tokens": payload.max_output_tokens,
            "temperature": payload.temperature,
        },
    )
    response.raise_for_status()
    data = response.json()
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    outputs = data.get("output", [])
    for item in outputs:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return str(content["text"]).strip()

    return ""


async def _generate_gemini(client: httpx.AsyncClient, payload: LLMGenerateRequest) -> str:
    request_body: dict[str, object] = {
        "contents": [{"parts": [{"text": payload.input}]}],
        "generationConfig": {
            "maxOutputTokens": payload.max_output_tokens,
            "temperature": payload.temperature,
        },
    }
    if payload.system_instruction.strip():
        request_body["systemInstruction"] = {"parts": [{"text": payload.system_instruction}]}

    response = await client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{payload.model}:generateContent",
        params={"key": payload.api_key},
        json=request_body,
    )
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(str(part.get("text", "")).strip() for part in parts if part.get("text")).strip()


async def _generate_nvidia(client: httpx.AsyncClient, payload: LLMGenerateRequest) -> str:
    messages: list[dict[str, str]] = []
    if payload.system_instruction.strip():
        messages.append({"role": "system", "content": payload.system_instruction})
    messages.append({"role": "user", "content": payload.input})

    response = await client.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {payload.api_key}"},
        json={
            "model": payload.model,
            "messages": messages,
            "max_tokens": payload.max_output_tokens,
            "temperature": payload.temperature,
        },
    )
    response.raise_for_status()
    data = response.json()
    return str(data.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()


async def _embed_openai(client: httpx.AsyncClient, payload: LLMEmbeddingRequest) -> list[float]:
    response = await client.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {payload.api_key}"},
        json={
            "model": payload.model,
            "input": payload.text,
        },
    )
    response.raise_for_status()
    data = response.json()
    embedding = data.get("data", [{}])[0].get("embedding")
    if not isinstance(embedding, list):
        return []
    return [float(value) for value in embedding]


async def generate_text_with_provider(payload: LLMGenerateRequest) -> str:
    if payload.provider == "mock":
        return payload.input.strip()

    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required to generate text for this provider.")

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            if payload.provider == "openai":
                return await _generate_openai(client, payload)
            if payload.provider == "gemini":
                return await _generate_gemini(client, payload)
            return await _generate_nvidia(client, payload)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:400] if exc.response.text else exc.response.reason_phrase
        raise HTTPException(status_code=400, detail=f"Text generation failed: {detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"Text generation failed: {exc}") from exc


async def generate_embedding_with_provider(payload: LLMEmbeddingRequest) -> list[float]:
    if payload.provider != "openai" or not payload.api_key.strip() or not payload.text.strip():
        return []

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            return await _embed_openai(client, payload)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:400] if exc.response.text else exc.response.reason_phrase
        raise HTTPException(status_code=400, detail=f"Embedding generation failed: {detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"Embedding generation failed: {exc}") from exc


@router.post("/test", response_model=LLMTestResponse)
async def test_llm(payload: LLMTestRequest) -> LLMTestResponse:
    if payload.provider == "mock":
        return LLMTestResponse(
            ok=True,
            provider=payload.provider,
            model=payload.model or "mock-provider",
            message="Mock provider test passed.",
        )

    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required to test this provider.")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            if payload.provider == "openai":
                await _test_openai(client, payload)
            elif payload.provider == "gemini":
                await _test_gemini(client, payload)
            elif payload.provider == "nvidia":
                await _test_nvidia(client, payload)
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:400] if exc.response.text else exc.response.reason_phrase
        raise HTTPException(status_code=400, detail=f"LLM test failed: {detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"LLM test failed: {exc}") from exc

    return LLMTestResponse(
        ok=True,
        provider=payload.provider,
        model=payload.model,
        message="LLM test completed successfully.",
    )


@router.post("/generate", response_model=LLMGenerateResponse)
async def generate_text(payload: LLMGenerateRequest) -> LLMGenerateResponse:
    output_text = await generate_text_with_provider(payload)

    return LLMGenerateResponse(
        ok=True,
        provider=payload.provider,
        model=payload.model,
        output_text=output_text,
    )
