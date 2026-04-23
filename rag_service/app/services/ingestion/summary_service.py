from __future__ import annotations

from app.services.llm.provider import get_llm_provider


async def summarize_page(page_text: str, max_tokens: int = 200) -> str:
    if not page_text.strip():
        return ""
    provider = get_llm_provider()
    try:
        return await provider.generate_text(
            f"Summarize this page in 2-3 sentences:\n\n{page_text[:3000]}",
            system="Return plain text only.",
            max_tokens=max_tokens,
            temperature=0.0,
        )
    except Exception:
        return ""


async def summarize_section(section_text: str, title: str, max_tokens: int = 200) -> str:
    if not section_text.strip():
        return ""
    provider = get_llm_provider()
    try:
        return await provider.generate_text(
            f"Section: {title}\n\nSummarize this section in 2-3 sentences:\n\n{section_text[:3000]}",
            system="Return plain text only.",
            max_tokens=max_tokens,
            temperature=0.0,
        )
    except Exception:
        return ""
