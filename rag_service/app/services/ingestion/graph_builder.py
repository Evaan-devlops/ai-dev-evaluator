from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import DocumentMode, EdgeType, NodeType
from app.services.ingestion.chunk_service import RawChunk
from app.services.ingestion.structure_extractor import Section
from app.utils.ids import new_id


@dataclass
class GraphNodeData:
    id: str
    node_type: NodeType
    title: str | None
    summary: str | None
    page_start: int | None
    page_end: int | None
    content_ref: str | None
    metadata: dict


@dataclass
class GraphEdgeData:
    id: str
    from_node_id: str
    to_node_id: str
    edge_type: EdgeType
    weight: float | None
    metadata: dict


@dataclass
class DocumentGraph:
    nodes: list[GraphNodeData] = field(default_factory=list)
    edges: list[GraphEdgeData] = field(default_factory=list)


def build_graph(
    mode: DocumentMode,
    chunks: list[RawChunk],
    pages: list[dict],
    sections: list[Section] | None = None,
) -> DocumentGraph:
    if mode == DocumentMode.structured and sections:
        return _build_tree_graph(sections, chunks)
    if mode == DocumentMode.scanned:
        return _build_page_graph(pages, chunks)
    return _build_chunk_graph(chunks)


def _build_chunk_graph(chunks: list[RawChunk]) -> DocumentGraph:
    graph = DocumentGraph()
    node_ids: list[str] = []

    for chunk in chunks:
        node_id = new_id()
        node_ids.append(node_id)
        graph.nodes.append(GraphNodeData(
            id=node_id,
            node_type=NodeType.chunk,
            title=chunk.section_title,
            summary=None,
            page_start=chunk.page_number,
            page_end=chunk.page_number,
            content_ref=None,
            metadata={"chunk_index": chunk.chunk_index, **chunk.metadata},
        ))

    # Link neighbors
    for i in range(len(node_ids) - 1):
        graph.edges.append(GraphEdgeData(
            id=new_id(),
            from_node_id=node_ids[i],
            to_node_id=node_ids[i + 1],
            edge_type=EdgeType.neighbor,
            weight=1.0,
            metadata={},
        ))

    return graph


def _build_page_graph(pages: list[dict], chunks: list[RawChunk]) -> DocumentGraph:
    graph = DocumentGraph()
    node_ids: list[str] = []

    for page in pages:
        node_id = new_id()
        node_ids.append(node_id)
        graph.nodes.append(GraphNodeData(
            id=node_id,
            node_type=NodeType.page,
            title=f"Page {page.get('page_number', 0)}",
            summary=None,
            page_start=page.get("page_number"),
            page_end=page.get("page_number"),
            content_ref=None,
            metadata={},
        ))

    for i in range(len(node_ids) - 1):
        graph.edges.append(GraphEdgeData(
            id=new_id(),
            from_node_id=node_ids[i],
            to_node_id=node_ids[i + 1],
            edge_type=EdgeType.page_link,
            weight=1.0,
            metadata={},
        ))

    return graph


def _build_tree_graph(sections: list[Section], chunks: list[RawChunk]) -> DocumentGraph:
    graph = DocumentGraph()
    section_node_map: dict[str, str] = {}

    for section in sections:
        node_id = new_id()
        section_node_map[section.title] = node_id
        graph.nodes.append(GraphNodeData(
            id=node_id,
            node_type=NodeType.section if section.level == 1 else NodeType.subsection,
            title=section.title,
            summary=None,
            page_start=section.page_start,
            page_end=section.page_end,
            content_ref=None,
            metadata={"level": section.level},
        ))

    # Add chunk nodes and link to sections
    for chunk in chunks:
        chunk_node_id = new_id()
        graph.nodes.append(GraphNodeData(
            id=chunk_node_id,
            node_type=NodeType.chunk,
            title=None,
            summary=None,
            page_start=chunk.page_number,
            page_end=chunk.page_number,
            content_ref=None,
            metadata={"chunk_index": chunk.chunk_index},
        ))

        if chunk.section_title and chunk.section_title in section_node_map:
            graph.edges.append(GraphEdgeData(
                id=new_id(),
                from_node_id=section_node_map[chunk.section_title],
                to_node_id=chunk_node_id,
                edge_type=EdgeType.parent_child,
                weight=1.0,
                metadata={},
            ))

    return graph
