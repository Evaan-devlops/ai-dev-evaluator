# Task List
# AI Dev Evaluator v2 + myRAG

**Legend:** 🔴 Blocked | 🟡 Ready | 🟢 Done | ⚪ Backlog

---

## Track A — ai-dev-evaluator Backend Fixes (start here)

| # | Task | Status | Notes |
|---|------|--------|-------|
| A1 | Create `backend/requirements.txt` | 🟡 | fastapi, uvicorn[standard], pydantic>=2.6, python-dotenv, sqlalchemy, alembic, psycopg2-binary, cryptography, httpx |
| A2 | Verify/create `backend/main.py` — FastAPI app + CORS + router registration | 🟡 | |
| A3 | Write pytest unit tests for `evaluator.py` | 🟡 | All 8 dimensions, edge cases |
| A4 | Write pytest unit tests for `assembler.py` | 🟡 | |

---

## Track B — Frontend Phase 1 Completion

| # | Task | Status | Notes |
|---|------|--------|-------|
| B1 | `src/types/workbench.ts` — mirror all backend schemas | 🟡 | Do this first |
| B2 | `src/api/workbench.ts` — typed fetch client for all 7 endpoints | 🔴 B1 | |
| B3 | `src/store/workbenchStore.ts` — Zustand store | 🔴 B2 | |
| B4 | `src/components/LayerCard.tsx` | 🔴 B3 | Toggle, content, token count, collapse |
| B5 | `src/components/PromptPreview.tsx` | 🔴 B3 | Assembled prompt + budget bar |
| B6 | `src/components/RunResultPanel.tsx` | 🔴 B3 | Score bars, insight, LLM response |
| B7 | `src/components/RunHistory.tsx` | 🔴 B3 | Run list, reset demo |
| B8 | `src/App.tsx` — layout wiring, load defaults on mount | 🔴 B4–B7 | |
| B9 | `src/styles/global.css` — base styles | 🟡 | |

---

## Track C — Phase 2A: Configure LLM + Actual Data

### Backend
| # | Task | Status | Notes |
|---|------|--------|-------|
| C1 | Alembic setup + initial migration | 🔴 A1 | |
| C2 | `models/config.py` — LLMConfig, ActualDataConfig ORM | 🔴 C1 | |
| C3 | `schemas/config.py` — Pydantic schemas | 🟡 | |
| C4 | `services/llm_client.py` — call OpenAI/Anthropic/Gemini via provider pattern | 🟡 | |
| C5 | `services/actual_data.py` — fetch from user-configured APIs via httpx | 🟡 | |
| C6 | `api/config.py` — POST /config/llm, POST /config/actual-data, GET both | 🔴 C2–C3 | |
| C7 | Update `/run` route to use real LLM when configured | 🔴 C4,C6 | Falls back to mock if not configured |
| C8 | Update `/assemble` to pull from Actual Data APIs when mode=actual | 🔴 C5,C6 | |

### Frontend
| # | Task | Status | Notes |
|---|------|--------|-------|
| C9 | `ConfigureLLM` panel component | 🔴 B8 | |
| C10 | `ActualDataConfig` panel — per-layer API config form | 🔴 B8 | |
| C11 | Mode toggle (Mock ↔ Actual Data) in store + UI | 🔴 B8 | |
| C12 | System prompt: textarea OR API endpoint selector | 🔴 C10 | |

---

## Track D — Phase 2B: PRD + Evaluation Parameters

| # | Task | Status | Notes |
|---|------|--------|-------|
| D1 | myRAG service Phase 1 complete (see Track E below) | 🔴 E7 | |
| D2 | `services/myrag_client.py` — HTTP client wrapping myRAG APIs | 🔴 D1 | |
| D3 | `models/prd.py`, `models/eval_param.py` ORM + migration | 🔴 C1 | |
| D4 | `schemas/prd.py` — PRD upload + eval parameter schemas | 🟡 | |
| D5 | `api/prd.py` — POST /prd/upload, POST /prd/process | 🔴 D2,D3 | |
| D6 | `PRDSection` frontend component — upload/paste + Process button | 🔴 B8,D5 | |
| D7 | `EvalParameterEditor` frontend component — editable param list with weights | 🔴 D6 | |

---

## Track E — myRAG Service (parallel, independent)

### Phase 1: Bootstrap
| # | Task | Status | Notes |
|---|------|--------|-------|
| E1 | Scaffold project structure (`myrag/app/` per spec) | 🟡 | |
| E2 | `core/config.py` — all env vars from .env.example | 🟡 | |
| E3 | `db/` — SQLAlchemy base, session, Alembic setup | 🟡 | |
| E4 | DB models: Document, Page, Chunk, GraphNode, GraphEdge, QueryLog, AnswerLog | 🔴 E3 | |
| E5 | Alembic initial migration | 🔴 E4 | |
| E6 | `GET /api/v1/health` endpoint | 🟡 | |
| E7 | `POST /api/v1/documents/upload` + `GET /api/v1/documents/{id}` | 🔴 E4 | |

### Phase 2: Ingestion
| # | Task | Status | Notes |
|---|------|--------|-------|
| E8 | `parser_service.py` — PDF (PyMuPDF) + plain text | 🔴 E7 | |
| E9 | `mode_detector.py` — heuristic classifier | 🔴 E8 | |
| E10 | `structure_extractor.py` — headings, sections, tables, refs | 🔴 E9 | |
| E11 | `chunk_service.py` — 3 strategies (section/sliding/page) | 🔴 E9 | |
| E12 | `embedding_service.py` — pluggable provider adapter | 🔴 E4 | |
| E13 | `graph_builder.py` — TreeGraph / ChunkGraph / PageGraph | 🔴 E10,E11 | |
| E14 | `summary_service.py` — page + section summaries via LLM | 🔴 E12 | |
| E15 | `GET /api/v1/documents/{id}/structure` + `/pages/{n}` | 🔴 E13 | |

### Phase 3: Retrieval
| # | Task | Status | Notes |
|---|------|--------|-------|
| E16 | `lexical_retriever.py` — PostgreSQL full-text (BM25 heuristic) | 🔴 E4 | |
| E17 | `semantic_retriever.py` — pgvector top-k | 🔴 E12 | |
| E18 | `structure_retriever.py` — section/heading/table match | 🔴 E13 | |
| E19 | `hybrid_retriever.py` — merge, deduplicate, normalize scores | 🔴 E16–E18 | |
| E20 | `reranker.py` — deterministic multi-signal reranking | 🔴 E19 | |
| E21 | `query_classifier.py` — classify query type (8 types) | 🟡 | |
| E22 | `answer_generator.py` — grounded answer + citations via LLM | 🔴 E20 | |
| E23 | `citation_builder.py` — structured citation per chunk/node | 🔴 E20 | |
| E24 | `context_builder.py` — assemble evidence context within token budget | 🔴 E20 | |

### Phase 4: Agent Loop
| # | Task | Status | Notes |
|---|------|--------|-------|
| E25 | `sufficiency_checker.py` — sufficient/missing/suggested actions | 🔴 E20 | |
| E26 | `agent/state.py` — AgentState, working memory | 🔴 E25 | |
| E27 | `agent/actions.py` — 10 allowed retrieval actions | 🔴 E26 | |
| E28 | `agent/stop_conditions.py` — step/token/evidence bounds | 🔴 E26 | |
| E29 | `agent/react_loop.py` — bounded ReAct orchestration | 🔴 E25–E28 | |
| E30 | `agent/decision_trace.py` — structured reasoning summaries | 🔴 E29 | |
| E31 | `POST /api/v1/queries/ask` — full pipeline wired | 🔴 E22,E29 | |
| E32 | Persist QueryLog + AnswerLog | 🔴 E31 | |

### Phase 5: Tests + Polish
| # | Task | Status | Notes |
|---|------|--------|-------|
| E33 | Unit tests: mode_detector, chunk_service, graph_builder | 🔴 E13 | |
| E34 | Unit tests: hybrid_retriever, sufficiency_checker, stop_conditions | 🔴 E25 | |
| E35 | Integration tests: upload → index → ask → answer with citations | 🔴 E31 | |
| E36 | Integration test: insufficient evidence scenario | 🔴 E31 | |
| E37 | `myrag/README.md` | 🔴 E31 | Per spec: arch, why no LC, flows, API examples |
| E38 | `myrag/progress.md` — running log per spec | 🟡 | Start now, update as built |

---

## Track F — Phase 2C: Evaluation Agent

| # | Task | Status | Notes |
|---|------|--------|-------|
| F1 | `services/eval_agent.py` — evaluation context assembly | 🔴 D2,C5 | From scratch, no frameworks |
| F2 | Reference response generation via configured LLM | 🔴 F1,C4 | Not stored or displayed |
| F3 | Per-parameter scoring with reasoning | 🔴 F1,D7 | Returns score + insight per param |
| F4 | `api/evaluate.py` — POST /evaluate/run | 🔴 F3 | |
| F5 | `RunResultPanel` update — dynamic eval parameters | 🔴 F4,B6 | |
| F6 | Score bar hover → insight card component | 🔴 F5 | Shows why + improvement suggestion |
| F7 | Conversation history local store (PostgreSQL) + summarize last 5 | 🔴 C1 | |

---

## Track G — Phase 3: Polish

| # | Task | Status | Notes |
|---|------|--------|-------|
| G1 | Replace in-memory run storage with PostgreSQL | 🔴 C1 | |
| G2 | Run history: include mode + LLM metadata | 🔴 G1 | |
| G3 | Side-by-side run comparison view | ⚪ | |
| G4 | Export runs as JSON/CSV | ⚪ | |

---

## Immediate Next Steps (start here)

1. **A1** — `backend/requirements.txt`
2. **A2** — verify `backend/main.py`
3. **B1 → B8** — complete Phase 1 frontend
4. **E1 → E7** — myRAG bootstrap (can run in parallel with B track)
