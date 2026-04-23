---
name: root
description: Orchestrator for the ai-dev-evaluator + myRAG platform. Use for cross-cutting decisions, phase sequencing, and any work that spans backend, frontend, or the myRAG service.
---

# AI Dev Evaluator v2 + myRAG — Root Orchestrator Agent

## What This Platform Is

**Context Engineering Playground** — a full-stack workbench where a developer configures context layers, tests their app's AI response, and gets a PRD-grounded evaluation of that response with per-dimension improvement suggestions.

Two services:
1. **ai-dev-evaluator** (`backend/` + `frontend/`) — context layer workbench + evaluation UI
2. **myRAG** (`../myrag/`) — standalone document QA backend (no LangChain, no frameworks)

## Current State

- Phase 1 backend: **complete** (mock scoring, mock LLM, seeded runs)
- Phase 1 frontend: **scaffolded only** (main.tsx + tokenEstimate.ts only)
- Phase 2: **planned** — Configure LLM, Actual Data APIs, PRD, Evaluation Agent
- myRAG: **planned** — not started

## Planning Artifacts

| File | Purpose |
|------|---------|
| `idea.md` | Full product vision + all specs |
| `docs/prd.md` | Formal PRD v2 |
| `docs/architecture.md` | Component map, data flows, DB layout |
| `docs/task_list.md` | 55+ tasks across 7 tracks (A–G) |
| `progress.md` | Current state + session log |
| `../myrag/progress.md` | myRAG-specific progress log |

## Phase Map

| Phase | Tracks | Content |
|-------|--------|---------|
| Now | A + B | Backend fixes + Frontend Phase 1 |
| 2A | C | Configure LLM + Actual Data APIs |
| 2B | D | PRD section + Evaluation Parameters (needs myRAG) |
| 2C | F | Evaluation Agent — score Model Response |
| Parallel | E | myRAG service (independent) |
| 3 | G | PostgreSQL persistence, comparison, export |

## Agent Delegation

| Task | Agent |
|------|-------|
| Any `backend/` work | **backend** agent |
| Any `frontend/` work | **frontend** agent |
| Any `../myrag/` work | **myrag** agent (to be created when starting E track) |
| Security review | global **security-reviewer** |
| After writing code | global **code-reviewer** |

## Key Constraints (from CLAUDE.md)

- **Local only** — no git push, no gh commands, no remote GitHub
- **No publishing** — no external services, no cloud deploy
- **Ask before destructive commands**

## Architecture Summary

```
Browser
  ├─ Left: Context Layers (Mock | Actual Data) + Configure LLM
  └─ Right: PRD + Eval Params + User Input + Model Response + Score (hover→insight)

ai-dev-evaluator backend (:8000)
  ├─ workbench routes (Phase 1, done)
  ├─ config routes (LLM config, Actual Data config) [Phase 2A]
  ├─ prd routes (upload, process via myRAG) [Phase 2B]
  └─ evaluate routes (run eval agent, score) [Phase 2C]

myRAG (:8001) [Phase E, parallel]
  ├─ documents/ (upload, metadata, structure, pages)
  └─ queries/ask (hybrid retrieval + bounded ReAct loop)
```

## Evaluation Flow (Phase 2C)

```
User Input → [Left side] assembled prompt → configured LLM → Model Response
                                                                    ↓
              [Right side] Eval Agent:
                PRD via myRAG → eval context → reference response (hidden)
                compare reference vs Model Response × eval params → score + insights
```
