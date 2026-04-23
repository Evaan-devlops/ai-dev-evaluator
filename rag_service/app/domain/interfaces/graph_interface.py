from __future__ import annotations

from typing import Protocol, Any


class GraphInterface(Protocol):
    """Common interface for TreeGraph, ChunkGraph, PageGraph."""

    async def search_candidates(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Return candidate nodes matching the query."""
        ...

    async def fetch_node(self, node_id: str) -> dict[str, Any] | None:
        """Fetch a single node by ID."""
        ...

    async def fetch_neighbors(self, node_id: str) -> list[dict[str, Any]]:
        """Fetch direct neighbors of a node."""
        ...

    async def fetch_parent(self, node_id: str) -> dict[str, Any] | None:
        """Fetch parent node."""
        ...

    async def fetch_children(self, node_id: str) -> list[dict[str, Any]]:
        """Fetch child nodes."""
        ...

    async def follow_references(self, node_id: str) -> list[dict[str, Any]]:
        """Follow cross-references from a node."""
        ...
