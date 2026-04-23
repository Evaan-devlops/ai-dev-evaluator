from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import config, documents, health, queries

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(config.router, tags=["config"])
router.include_router(documents.router, tags=["documents"])
router.include_router(queries.router, tags=["queries"])
