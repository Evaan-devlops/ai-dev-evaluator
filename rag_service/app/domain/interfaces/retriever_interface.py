from __future__ import annotations

from typing import Protocol, Any


class RetrieverInterface(Protocol):
    """Common interface for lexical, semantic, and structure retrievers."""

    async def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Return ranked evidence items for a query."""
        ...
