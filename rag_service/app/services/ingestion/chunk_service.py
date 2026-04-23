from __future__ import annotations

from dataclasses import dataclass

from app.core.constants import CHUNK_SIZE_TOKENS, CHUNK_OVERLAP_TOKENS
from app.domain.enums import DocumentMode
from app.utils.tokens import estimate_tokens


@dataclass
class RawChunk:
    chunk_index: int
    text: str
    page_number: int | None
    section_title: str | None
    metadata: dict


def chunk_pages(
    pages: list[dict],
    mode: DocumentMode,
    sections: list | None = None,
) -> list[RawChunk]:
    if mode == DocumentMode.scanned:
        return _page_chunks(pages)
    if mode == DocumentMode.structured and sections:
        return _section_chunks(sections)
    return _sliding_window_chunks(pages)


def _page_chunks(pages: list[dict]) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    for i, page in enumerate(pages):
        text = page.get("text", "").strip()
        if not text:
            continue
        chunks.append(RawChunk(
            chunk_index=i,
            text=text,
            page_number=page.get("page_number"),
            section_title=None,
            metadata={"strategy": "page"},
        ))
    return chunks


def _section_chunks(sections: list) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    idx = 0
    for section in sections:
        content = section.content.strip()
        if not content:
            continue
        sub_chunks = _split_by_tokens(content, CHUNK_SIZE_TOKENS, CHUNK_OVERLAP_TOKENS)
        for sub in sub_chunks:
            chunks.append(RawChunk(
                chunk_index=idx,
                text=sub,
                page_number=section.page_start,
                section_title=section.title,
                metadata={"strategy": "section", "level": section.level},
            ))
            idx += 1
    return chunks


def _sliding_window_chunks(pages: list[dict]) -> list[RawChunk]:
    chunks: list[RawChunk] = []
    idx = 0
    for page in pages:
        text = page.get("text", "").strip()
        if not text:
            continue
        sub_chunks = _split_by_tokens(text, CHUNK_SIZE_TOKENS, CHUNK_OVERLAP_TOKENS)
        for sub in sub_chunks:
            chunks.append(RawChunk(
                chunk_index=idx,
                text=sub,
                page_number=page.get("page_number"),
                section_title=None,
                metadata={"strategy": "sliding"},
            ))
            idx += 1
    return chunks


def _split_by_tokens(text: str, size: int, overlap: int) -> list[str]:
    """Split text into chunks of ~size tokens with overlap."""
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    # Approximate words per chunk (1 token ≈ 0.75 words)
    words_per_chunk = max(10, int(size * 0.75))
    step = max(5, words_per_chunk - int(overlap * 0.75))
    start = 0

    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        chunks.append(" ".join(words[start:end]))
        start += step

    return chunks
