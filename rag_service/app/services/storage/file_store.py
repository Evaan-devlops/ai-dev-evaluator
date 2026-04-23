from __future__ import annotations

import hashlib
import os
from pathlib import Path

import aiofiles

from app.core.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.core.constants import SUPPORTED_CONTENT_TYPES


class FileStore:
    def __init__(self) -> None:
        self.base_dir = Path(settings.UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _doc_dir(self, document_id: str) -> Path:
        path = self.base_dir / document_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def save(
        self,
        document_id: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> Path:
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise UnsupportedFileTypeError(content_type)

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(data) > max_bytes:
            raise FileTooLargeError(len(data) / 1024 / 1024, settings.MAX_UPLOAD_SIZE_MB)

        dest = self._doc_dir(document_id) / filename
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
        return dest

    def get_path(self, document_id: str, filename: str) -> Path:
        return self._doc_dir(document_id) / filename

    def checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


file_store = FileStore()
