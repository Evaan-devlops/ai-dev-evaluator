from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.page import Page
from app.utils.ids import new_id


class PageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_create(self, document_id: str, pages_data: list[dict]) -> list[Page]:
        pages: list[Page] = []
        for item in pages_data:
            page = Page(
                id=new_id(),
                document_id=document_id,
                page_number=item["page_number"],
                raw_text=item.get("text", ""),
                summary=item.get("summary"),
                layout_type=item.get("layout_type", "text"),
                ocr_confidence=item.get("ocr_confidence"),
            )
            self.session.add(page)
            pages.append(page)
        await self.session.flush()
        return pages

    async def get_by_number(self, document_id: str, page_number: int) -> Page | None:
        result = await self.session.execute(
            select(Page)
            .where(Page.document_id == document_id, Page.page_number == page_number)
        )
        return result.scalar_one_or_none()

    async def list_by_document(self, document_id: str) -> list[Page]:
        result = await self.session.execute(
            select(Page)
            .where(Page.document_id == document_id)
            .order_by(Page.page_number)
        )
        return list(result.scalars().all())
