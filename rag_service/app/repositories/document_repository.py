from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import Document
from app.domain.enums import DocumentMode, DocumentStatus
from app.utils.ids import new_id
from app.utils.time import utcnow


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        filename: str,
        content_type: str,
        checksum: str | None = None,
    ) -> Document:
        doc = Document(
            id=new_id(),
            filename=filename,
            content_type=content_type,
            mode=DocumentMode.unstructured.value,
            status=DocumentStatus.uploaded.value,
            checksum=checksum,
            page_count=0,
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def get(self, document_id: str) -> Document | None:
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def update_status(self, document_id: str, status: DocumentStatus) -> None:
        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status=status.value, updated_at=utcnow())
        )

    async def update_after_ingestion(
        self,
        document_id: str,
        mode: DocumentMode,
        page_count: int,
        status: DocumentStatus,
    ) -> None:
        await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(mode=mode.value, page_count=page_count, status=status.value, updated_at=utcnow())
        )
