from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CrossReference:
    source_text: str
    target: str
    page_number: int


_REF_RE = re.compile(
    r"(?:see|refer to|as described in|per|cf\.?|see also)\s+"
    r"(?:section|appendix|table|figure|chapter)?\s*"
    r"([A-Za-z0-9._ \-]+)",
    re.IGNORECASE,
)


def extract_references(pages: list[dict]) -> list[CrossReference]:
    refs: list[CrossReference] = []
    for page in pages:
        page_number = page.get("page_number", 1)
        text = page.get("text", "")
        for match in _REF_RE.finditer(text):
            refs.append(CrossReference(
                source_text=match.group(0).strip(),
                target=match.group(1).strip(),
                page_number=page_number,
            ))
    return refs
