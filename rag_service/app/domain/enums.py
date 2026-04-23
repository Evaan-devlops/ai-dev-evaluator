from __future__ import annotations

from enum import Enum


class DocumentMode(str, Enum):
    structured = "structured"
    semi_structured = "semi_structured"
    unstructured = "unstructured"
    scanned = "scanned"


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    parsing = "parsing"
    indexed = "indexed"
    failed = "failed"


class QueryType(str, Enum):
    fact = "fact"
    summary = "summary"
    comparison = "comparison"
    clause = "clause"
    table = "table"
    cross_reference = "cross_reference"
    follow_up = "follow_up"
    multi_hop = "multi_hop"


class NodeType(str, Enum):
    section = "section"
    subsection = "subsection"
    page = "page"
    table = "table"
    chunk = "chunk"
    appendix = "appendix"
    note = "note"


class EdgeType(str, Enum):
    parent_child = "parent_child"
    neighbor = "neighbor"
    reference = "reference"
    semantic_link = "semantic_link"
    page_link = "page_link"
    section_link = "section_link"


class ConfidenceLabel(str, Enum):
    direct_evidence = "direct_evidence"
    multi_evidence_inference = "multi_evidence_inference"
    insufficient_evidence = "insufficient_evidence"
