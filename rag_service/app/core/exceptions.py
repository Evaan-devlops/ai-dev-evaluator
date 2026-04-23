from __future__ import annotations


class RagServiceError(Exception):
    """Base error for rag_service."""


class DocumentNotFoundError(RagServiceError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document '{document_id}' not found.")
        self.document_id = document_id


class IngestionError(RagServiceError):
    """Raised when document ingestion fails."""


class RetrievalError(RagServiceError):
    """Raised when retrieval fails."""


class EmbeddingError(RagServiceError):
    """Raised when embedding generation fails."""


class LLMError(RagServiceError):
    """Raised when LLM call fails."""


class FileTooLargeError(RagServiceError):
    def __init__(self, size_mb: float, max_mb: int) -> None:
        super().__init__(f"File size {size_mb:.1f} MB exceeds max {max_mb} MB.")


class UnsupportedFileTypeError(RagServiceError):
    def __init__(self, content_type: str) -> None:
        super().__init__(f"Unsupported file type: {content_type}")


class InsufficientEvidenceError(RagServiceError):
    """Raised when no sufficient evidence is found to answer."""
