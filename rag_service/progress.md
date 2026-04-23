# RAG Service — Progress

## Phase 1 — Bootstrap & Core Infrastructure ✅

### What was added
- `app/main.py` — FastAPI app entry point with CORS
- `app/core/config.py` — Pydantic Settings from `.env`
- `app/core/logging.py` — Structured stdout logging
- `app/core/exceptions.py` — Domain-specific exceptions
- `app/core/constants.py` — Tunable constants (chunk size, weights, thresholds)
- `app/domain/enums.py` — DocumentMode, DocumentStatus, QueryType, NodeType, EdgeType, ConfidenceLabel
- `app/domain/types.py` — Type aliases
- `app/domain/interfaces/` — GraphInterface, RetrieverInterface, LLMInterface (Protocol-based)
- `app/utils/` — ids, text, tokens, pdf, time helpers

### Concepts used
- Pydantic Settings for env-driven config
- Protocol-based interface design (duck typing)
- Custom exception hierarchy

---

## Phase 2 — Database Models & Ingestion Pipeline ✅

### What was added
- `app/db/base.py` — SQLAlchemy DeclarativeBase
- `app/db/session.py` — Async session factory with asyncpg driver
- `app/db/models/` — Document, Page, Chunk (with pgvector), GraphNode, GraphEdge, QueryLog, AnswerLog
- `alembic/` — Async-compatible migration environment + initial schema migration
  - `versions/001_initial_schema.py` — All tables, vector column, IVFFlat index, FTS GIN index

### Ingestion services
- `parser_service.py` — pdfplumber + fitz PDF parsing; plain text fallback
- `mode_detector.py` — Heuristic mode detection (heading density, line length variance)
- `structure_extractor.py` — Markdown/numbered heading section extraction
- `table_extractor.py` — pdfplumber table extraction with text rendering
- `reference_extractor.py` — Cross-reference extraction via regex
- `chunk_service.py` — Adaptive chunking: page-based (scanned), section-aware (structured), sliding-window (unstructured)
- `embedding_service.py` — Pluggable embedding via LLM provider
- `summary_service.py` — Page and section summaries via LLM
- `graph_builder.py` — TreeGraph (structured), ChunkGraph (unstructured), PageGraph (scanned)
- `ingest_service.py` — Full ingestion orchestration pipeline

### Repositories
- `document_repository.py`, `page_repository.py`, `chunk_repository.py`, `graph_repository.py`, `query_repository.py`

### Concepts used
- Repository pattern for data access separation
- Async SQLAlchemy 2.0 with asyncpg
- pgvector IVFFlat index for approximate nearest-neighbor search
- PostgreSQL FTS GIN index for lexical retrieval
- Mode-adaptive processing (structured → TreeGraph, scanned → PageGraph, unstructured → ChunkGraph)

---

## Phase 3 — LLM Abstraction & Retrieval Pipeline ✅

### What was added
- `app/services/llm/provider.py` — Unified OpenAI/Gemini provider; pluggable via env
- `app/services/storage/file_store.py` — Async file storage with checksum, size guards
- `app/services/retrieval/lexical_retriever.py` — PostgreSQL full-text search
- `app/services/retrieval/semantic_retriever.py` — pgvector cosine similarity
- `app/services/retrieval/structure_retriever.py` — Section title/summary matching
- `app/services/retrieval/hybrid_retriever.py` — Score-fusion merge of all three
- `app/services/retrieval/reranker.py` — Deterministic reranker with query-type bias
- `app/services/retrieval/citation_builder.py` — Deduplicated citation objects

### Concepts used
- Hybrid score fusion (BM25_WEIGHT + SEMANTIC_WEIGHT + STRUCTURE_WEIGHT)
- asyncio.gather for parallel retrieval
- Query-type bias in reranking (tables boosted for table queries, etc.)

---

## Phase 4 — QA Pipeline & Bounded ReAct Agent ✅

### What was added
- `app/services/qa/query_classifier.py` — Pattern-based query type classification
- `app/services/qa/sufficiency_checker.py` — Evidence sufficiency check (volume + coverage + score)
- `app/services/qa/context_builder.py` — Token-budget-aware context assembly
- `app/services/qa/answer_generator.py` — Grounded answer generation via LLM
- `app/services/agent/state.py` — AgentState with deduplicating candidate accumulation
- `app/services/agent/stop_conditions.py` — Max steps, context budget, sufficiency
- `app/services/agent/actions.py` — Registry of allowed retrieval actions
- `app/services/agent/react_loop.py` — Custom bounded ReAct loop (no LangChain/LangGraph)
- `app/services/agent/decision_trace.py` — Safe structured reasoning summary (no raw CoT)

### Concepts used
- Custom ReAct loop: Observe → Think → Act → Update → Check stop
- Deterministic action selection based on sufficiency gap
- Context budget management (token counting per candidate)
- Structured decision trace (not raw chain-of-thought)

---

## Phase 5 — API Endpoints ✅

### What was added
- `app/api/v1/health.py` — GET /api/v1/health
- `app/api/v1/documents.py` — POST upload, GET meta, GET status, GET structure, GET page
- `app/api/v1/queries.py` — POST /api/v1/queries/ask (full QA pipeline)
- `app/api/router.py` — Router aggregation
- `app/schemas/` — document, query, retrieval, agent, common Pydantic models

### Concepts used
- FastAPI dependency injection for session management
- Synchronous ingestion pipeline (background job support ready by separating run_ingestion)
- Query + answer logging on every request

---

## Vulnerable Areas

| Area | Risk | Why |
|------|------|-----|
| File upload | Path traversal | Mitigated by uuid-based dirs; content_type checked |
| Raw SQL in chunk_repo | SQL injection | Parameters bound via SQLAlchemy text() placeholders |
| Embedding column migration | Runtime error if pgvector not installed | Migration adds extension first; graceful skip if not present |
| Agent loop | Infinite loop | Hard-capped at MAX_AGENT_STEPS + MAX_CONTEXT_TOKENS |
| LLM prompts | Prompt injection via doc content | Content is never user-supplied as instructions; all document text goes into user turn |
| Large documents | OOM during ingestion | MAX_UPLOAD_SIZE_MB limits file size; chunking prevents full-text in memory |

---

## Extra Features Added
- Automatic FTS GIN index for zero-config lexical retrieval
- IVFFlat index with 50 lists for fast semantic search
- Decision trace stored per query for debugging (not exposed as raw CoT)
- Conversation context included in answer generation (last 6 turns)
- Section-aware citations with page numbers
