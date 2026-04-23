"""
Document upload proxy.
Accepts a file upload and fans it out to:
  1. A configured ingestion API endpoint (optional)
  2. The myRAG service at /api/v1/documents/upload (optional)
Both are fire-and-forget; partial failures are reported but do not fail the whole request.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/api/documents", tags=["documents"])

_MAX_BYTES = 25 * 1024 * 1024  # 25 MB


class IngestResult(BaseModel):
    ok: bool
    message: str
    document_id: str | None = None
    ingestion_api_status: str | None = None
    rag_service_status: str | None = None


@router.post("/ingest", response_model=IngestResult)
async def ingest_document(
    file: UploadFile = File(...),
    ingestion_endpoint: str = Form(default=""),
    ingestion_headers: str = Form(default=""),
    rag_service_url: str = Form(default=""),
) -> IngestResult:
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large (max {_MAX_BYTES // 1024 // 1024} MB)")

    filename = file.filename or "upload"
    content_type = file.content_type or "application/octet-stream"

    ingestion_status: str | None = None
    rag_status: str | None = None
    document_id: str | None = None
    messages: list[str] = []

    # ── Fan-out 1: External ingestion API ─────────────────────────────────────
    if ingestion_endpoint.strip():
        try:
            headers: dict[str, str] = {}
            if ingestion_headers.strip():
                import json
                headers = json.loads(ingestion_headers.strip())

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    ingestion_endpoint.strip(),
                    files={"file": (filename, content, content_type)},
                    headers=headers,
                )
                if resp.is_success:
                    ingestion_status = f"ok ({resp.status_code})"
                    messages.append(f"Ingestion API: {ingestion_status}")
                else:
                    ingestion_status = f"error {resp.status_code}: {resp.text[:200]}"
                    messages.append(f"Ingestion API: {ingestion_status}")
        except Exception as exc:
            ingestion_status = f"failed: {exc}"
            messages.append(f"Ingestion API: {ingestion_status}")

    # ── Fan-out 2: myRAG service ───────────────────────────────────────────────
    if rag_service_url.strip():
        try:
            url = rag_service_url.rstrip("/") + "/api/v1/documents/upload"
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(
                    url,
                    files={"file": (filename, content, content_type)},
                )
                if resp.is_success:
                    data = resp.json()
                    document_id = data.get("document_id")
                    rag_status = f"ok — document_id={document_id}"
                    messages.append(f"myRAG: {rag_status}")
                else:
                    rag_status = f"error {resp.status_code}: {resp.text[:200]}"
                    messages.append(f"myRAG: {rag_status}")
        except Exception as exc:
            rag_status = f"failed: {exc}"
            messages.append(f"myRAG: {rag_status}")

    if not ingestion_endpoint.strip() and not rag_service_url.strip():
        messages.append("No ingestion target configured — file received but not forwarded.")

    return IngestResult(
        ok=True,
        message="; ".join(messages) or "Upload received.",
        document_id=document_id,
        ingestion_api_status=ingestion_status,
        rag_service_status=rag_status,
    )
