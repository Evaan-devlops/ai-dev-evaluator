---
name: backend
description: FastAPI backend specialist for ai-dev-evaluator. Use for all work in backend/ — new routes, schema changes, service logic, scoring engine, mock provider, database integration, tests.
---

# AI Dev Evaluator — Backend Agent

## Stack

- Python 3.12 + FastAPI + Pydantic v2 + Uvicorn
- In-memory storage (Phase 1) → PostgreSQL planned (Phase 2)
- Location: `backend/`

## Project Structure

```
backend/
├── main.py                        # FastAPI app + router registration
├── database.py                    # DB placeholder (Phase 2)
├── .env.example                   # APP_ENV, APP_HOST, APP_PORT, CORS_ORIGINS
├── requirements.txt               # ⚠️ MISSING — needs to be created
└── app/
    ├── core/config.py             # Pydantic settings
    ├── schemas/workbench.py       # ALL request/response types (source of truth)
    ├── models/run.py              # ORM model placeholder
    ├── data/seeds.py              # DEFAULT_LAYERS + SEEDED_RUNS
    ├── services/
    │   ├── assembler.py           # Layer → assembled prompt + token estimate
    │   ├── evaluator.py           # Deterministic 8-dimension scoring
    │   └── provider.py            # Mock LLM response generator
    └── api/
        └── workbench.py           # 7 routes (prefix: /api/v1/workbench)
```

## API Routes

| Method | Path | Handler |
|--------|------|---------|
| GET | `/health` | inline in main.py |
| GET | `/api/v1/workbench/defaults` | `get_defaults` |
| POST | `/api/v1/workbench/assemble` | `assemble` |
| POST | `/api/v1/workbench/run` | `run_workbench` |
| GET | `/api/v1/workbench/runs` | `list_runs` |
| GET | `/api/v1/workbench/runs/{id}` | `get_run` |
| POST | `/api/v1/workbench/reset-demo` | `reset_demo` |

## Context Layer IDs

`"system"` | `"user"` | `"history"` | `"knowledge"` | `"tools"` | `"state"`

## Scoring Dimensions (evaluator.py)

Each starts at 1, capped at 5, total max 40:
- `persona_adherence`: +3 system, +1 state
- `policy_accuracy`: +3 knowledge, +1 system
- `empathy_tone`: +2 system, +1 history
- `context_awareness`: +2 history, +1 state, +1 knowledge
- `actionability`: +3 tools, +1 knowledge
- `personalization`: +3 state, +1 system
- `no_hallucination`: +2 knowledge, +1 tools
- `completeness`: +1 per 2 active layers (max +4)

## Key Conventions

- All schemas in `app/schemas/workbench.py` — never duplicate types
- Immutable patterns — services return new objects, never mutate inputs
- Type annotations on all function signatures (PEP 8 + mypy-compatible)
- `from __future__ import annotations` at top of every module
- No hardcoded secrets — use `app/core/config.py` + `.env`

## Dev Commands

```powershell
cd backend
pip install -r requirements.txt    # once created
cp .env.example .env
uvicorn main:app --reload          # http://localhost:8000
# docs at http://localhost:8000/docs
```

## Immediate Tasks

1. **Create `requirements.txt`** — fastapi, uvicorn[standard], pydantic>=2.6, python-dotenv
2. Verify `main.py` exists and registers `workbench.router` + CORS middleware
3. Write pytest unit tests for `evaluator.py` (all 8 dimensions, edge cases)
4. Write pytest unit tests for `assembler.py` (token estimation, empty layers)

## Phase 2 Integration Points

- `provider.py :: generate_mock_response()` → swap with real LLM call
- `data/seeds.py :: KNOWLEDGE_CONTENT` → swap with vector DB retrieval
- `data/seeds.py :: TOOLS_CONTENT` → swap with dynamic tool registry
- `data/seeds.py :: STATE_CONTENT` → swap with live CRM lookup
- `database.py` → SQLAlchemy + alembic migrations
- `workbench.py` in-memory `_run_history/_run_details` → DB repository

## Testing

```bash
pytest --cov=app --cov-report=term-missing
```
Target: 80%+ coverage on `evaluator.py`, `assembler.py`, `provider.py`.
