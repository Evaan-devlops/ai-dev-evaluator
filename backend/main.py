from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.workbench import router as workbench_router
from app.api.context import router as context_router
from app.api.llm import router as llm_router
from app.api.evaluation import router as evaluation_router
from app.api.integrations import router as integrations_router
from app.api.documents import router as documents_router
from app.core.config import settings

app = FastAPI(
    title="Context Engineering Playground API",
    description="Evaluate how context layers affect LLM response quality",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy workbench routes (/api/v1/workbench/*)
app.include_router(workbench_router)

# New context routes (/api/context/*) — used by the frontend
app.include_router(context_router)
app.include_router(llm_router)
app.include_router(evaluation_router)
app.include_router(integrations_router)
app.include_router(documents_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "context-engineering-playground"}
