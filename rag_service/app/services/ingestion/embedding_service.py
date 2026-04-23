from __future__ import annotations

from app.services.llm.provider import get_llm_provider


async def embed_text(text: str) -> list[float]:
    """Generate embedding for a text string."""
    provider = get_llm_provider()
    return await provider.generate_embedding(text)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts sequentially."""
    results: list[list[float]] = []
    for text in texts:
        try:
            emb = await embed_text(text)
        except Exception:
            emb = []
        results.append(emb)
    return results
