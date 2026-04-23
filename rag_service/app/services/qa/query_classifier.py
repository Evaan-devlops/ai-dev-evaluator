from __future__ import annotations

import re

from app.domain.enums import QueryType


_PATTERNS: list[tuple[re.Pattern, QueryType]] = [
    (re.compile(r"\b(table|row|column|cell|spreadsheet)\b", re.I), QueryType.table),
    (re.compile(r"\b(compare|difference|vs\.?|versus|contrast)\b", re.I), QueryType.comparison),
    (re.compile(r"\b(summarize|overview|summary|describe)\b", re.I), QueryType.summary),
    (re.compile(r"\b(clause|section \d|paragraph \d|provision|article)\b", re.I), QueryType.clause),
    (re.compile(r"\b(see also|refers to|as per|cross.?ref)\b", re.I), QueryType.cross_reference),
    (re.compile(r"\b(follow.?up|continue|next|previous|last time|you mentioned)\b", re.I), QueryType.follow_up),
    (re.compile(r"\b(and|also|additionally|furthermore|moreover|as well)\b.*\b(and|also)\b", re.I), QueryType.multi_hop),
]


def classify_query(query: str) -> QueryType:
    for pattern, query_type in _PATTERNS:
        if pattern.search(query):
            return query_type
    return QueryType.fact
