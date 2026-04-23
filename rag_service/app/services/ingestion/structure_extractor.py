from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Section:
    title: str
    level: int
    page_start: int
    page_end: int | None
    content: str
    subsections: list["Section"] = field(default_factory=list)


_HEADING_RE = re.compile(
    r"^(#{1,6})\s+(.+)$"           # Markdown headings
    r"|^([A-Z][A-Z0-9 ]{2,60})$"   # ALL-CAPS headings
    r"|^(\d+(?:\.\d+)*)\s+(.+)$",  # Numbered headings like "1.2.3 Title"
    re.MULTILINE,
)


def extract_sections(pages: list[dict]) -> list[Section]:
    """Extract document sections from page text."""
    sections: list[Section] = []
    current: Section | None = None

    for page in pages:
        page_number = page.get("page_number", 1)
        text = page.get("text", "")
        lines = text.splitlines()

        for line in lines:
            stripped = line.strip()
            match = _HEADING_RE.match(stripped)
            if match:
                if current:
                    current.page_end = page_number
                    sections.append(current)
                level = _heading_level(stripped)
                current = Section(
                    title=stripped.lstrip("#").strip(),
                    level=level,
                    page_start=page_number,
                    page_end=None,
                    content="",
                )
            elif current:
                current.content += line + "\n"

    if current:
        current.page_end = pages[-1].get("page_number", 1) if pages else 1
        sections.append(current)

    return sections


def _heading_level(line: str) -> int:
    if line.startswith("#"):
        return len(line) - len(line.lstrip("#"))
    if re.match(r"^\d+\.\d+", line):
        return 2
    if re.match(r"^\d+\.", line):
        return 1
    return 1
