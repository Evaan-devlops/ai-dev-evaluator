from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.graph_node import GraphNode
from app.db.models.graph_edge import GraphEdge
from app.services.ingestion.graph_builder import GraphNodeData, GraphEdgeData
from app.utils.ids import new_id


class GraphRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create_nodes(self, document_id: str, nodes: list[GraphNodeData]) -> None:
        for node in nodes:
            db_node = GraphNode(
                id=node.id,
                document_id=document_id,
                node_type=node.node_type.value,
                title=node.title,
                summary=node.summary,
                page_start=node.page_start,
                page_end=node.page_end,
                content_ref=node.content_ref,
                metadata_json=node.metadata,
            )
            self.session.add(db_node)
        await self.session.flush()

    async def bulk_create_edges(self, document_id: str, edges: list[GraphEdgeData]) -> None:
        for edge in edges:
            db_edge = GraphEdge(
                id=edge.id,
                document_id=document_id,
                from_node_id=edge.from_node_id,
                to_node_id=edge.to_node_id,
                edge_type=edge.edge_type.value,
                weight=edge.weight,
                metadata_json=edge.metadata,
            )
            self.session.add(db_edge)
        await self.session.flush()

    async def get_node(self, node_id: str) -> GraphNode | None:
        result = await self.session.execute(select(GraphNode).where(GraphNode.id == node_id))
        return result.scalar_one_or_none()

    async def get_neighbors(self, node_id: str) -> list[GraphNode]:
        edges_result = await self.session.execute(
            select(GraphEdge).where(
                (GraphEdge.from_node_id == node_id) | (GraphEdge.to_node_id == node_id)
            )
        )
        edges = list(edges_result.scalars().all())
        neighbor_ids = {
            e.to_node_id if e.from_node_id == node_id else e.from_node_id
            for e in edges
        } - {node_id}
        if not neighbor_ids:
            return []
        result = await self.session.execute(select(GraphNode).where(GraphNode.id.in_(neighbor_ids)))
        return list(result.scalars().all())

    async def get_children(self, node_id: str) -> list[GraphNode]:
        edges_result = await self.session.execute(
            select(GraphEdge).where(
                GraphEdge.from_node_id == node_id,
                GraphEdge.edge_type == "parent_child",
            )
        )
        child_ids = [e.to_node_id for e in edges_result.scalars().all()]
        if not child_ids:
            return []
        result = await self.session.execute(select(GraphNode).where(GraphNode.id.in_(child_ids)))
        return list(result.scalars().all())

    async def get_parent(self, node_id: str) -> GraphNode | None:
        edge_result = await self.session.execute(
            select(GraphEdge).where(
                GraphEdge.to_node_id == node_id,
                GraphEdge.edge_type == "parent_child",
            ).limit(1)
        )
        edge = edge_result.scalar_one_or_none()
        if not edge:
            return None
        return await self.get_node(edge.from_node_id)

    async def list_nodes_by_document(self, document_id: str) -> list[GraphNode]:
        result = await self.session.execute(
            select(GraphNode).where(GraphNode.document_id == document_id)
        )
        return list(result.scalars().all())
