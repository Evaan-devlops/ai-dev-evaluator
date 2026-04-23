from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.utils.pdf import extract_tables_from_page


@dataclass
class ExtractedTable:
    page_number: int
    rows: list[list[str]]

    def to_text(self) -> str:
        """Render table as plain-text markdown."""
        if not self.rows:
            return ""
        lines: list[str] = []
        for i, row in enumerate(self.rows):
            lines.append(" | ".join(cell.replace("\n", " ") for cell in row))
            if i == 0:
                lines.append("-" * max(len(lines[0]), 10))
        return "\n".join(lines)


def extract_tables(path: Path, page_number: int) -> list[ExtractedTable]:
    raw = extract_tables_from_page(path, page_number)
    return [ExtractedTable(page_number=page_number, rows=rows) for rows in raw]
