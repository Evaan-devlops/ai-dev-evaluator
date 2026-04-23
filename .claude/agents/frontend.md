---
name: frontend
description: React/TypeScript frontend specialist for ai-dev-evaluator. Use for all work in frontend/src — components, store, API client, styling, types. The UI is not yet built; this agent drives Phase 1 frontend completion.
---

# AI Dev Evaluator — Frontend Agent

## Stack

- React 18 + TypeScript 5 + Vite 5
- Zustand 4 (state management)
- No component library — custom CSS
- Location: `frontend/`

## Current State

Scaffolded only. What exists:
- `src/main.tsx` — React entry, renders `<App />`
- `src/utils/tokenEstimate.ts` — token estimation utility
- `src/styles/global.css` — imported in main.tsx (create if missing)
- **`src/App.tsx` — DOES NOT EXIST yet**
- No API client, no store, no components

## Target Structure (Phase 1)

```
frontend/src/
├── main.tsx                        ✅ exists
├── App.tsx                         ❌ build this
├── styles/
│   └── global.css                  (create if missing)
├── api/
│   └── workbench.ts                ❌ typed fetch client
├── store/
│   └── workbenchStore.ts           ❌ Zustand store
├── types/
│   └── workbench.ts                ❌ mirrored from backend schemas
├── components/
│   ├── LayerCard.tsx               ❌ toggle + content + token count
│   ├── PromptPreview.tsx           ❌ assembled prompt + total tokens
│   ├── RunResultPanel.tsx          ❌ LLM response + score breakdown
│   └── RunHistory.tsx              ❌ past runs list
└── utils/
    └── tokenEstimate.ts            ✅ exists
```

## API Contract (from backend schemas)

Base URL: `VITE_API_BASE_URL` (default `http://localhost:8000`)

### Types to mirror in `src/types/workbench.ts`

```typescript
type LayerType = 'system' | 'user' | 'history' | 'knowledge' | 'tools' | 'state'

interface ContextLayer {
  id: LayerType
  title: string
  description: string
  enabled: boolean
  content: string
  token_estimate: number
  order: number
  collapsed: boolean
  color: string
}

interface ScoreBreakdown {
  persona_adherence: number   // 0-5
  policy_accuracy: number
  empathy_tone: number
  context_awareness: number
  actionability: number
  personalization: number
  no_hallucination: number
  completeness: number
}

interface RunResult {
  run_id: string
  run_number: number
  quality_score: number       // 0-40
  score_max: number           // 40
  score_breakdown: ScoreBreakdown
  insight: string
  llm_response: string
  latency_ms: number
  total_tokens: number
  active_layers: LayerType[]
  timestamp: string
}

interface RunHistoryItem {
  run_id: string
  run_number: number
  active_layers: LayerType[]
  quality_score: number
  score_max: number
  total_tokens: number
  latency_ms: number
}

interface DefaultsResponse {
  layers: ContextLayer[]
  token_budget_max: number    // 4000
  run_history: RunHistoryItem[]
  initial_result: RunResult | null
}
```

### API Endpoints

```typescript
GET  /api/v1/workbench/defaults         → DefaultsResponse
POST /api/v1/workbench/assemble         → { assembled_prompt, per_layer_tokens, total_tokens }
POST /api/v1/workbench/run              → RunResult
GET  /api/v1/workbench/runs             → RunHistoryItem[]
GET  /api/v1/workbench/runs/:id         → RunResult
POST /api/v1/workbench/reset-demo       → { message, run_history_cleared }
```

## Zustand Store Shape

```typescript
interface WorkbenchStore {
  // state
  layers: ContextLayer[]
  tokenBudgetMax: number
  assembledPrompt: string
  perLayerTokens: Record<string, number>
  totalTokens: number
  runHistory: RunHistoryItem[]
  currentResult: RunResult | null
  isRunning: boolean
  error: string | null

  // actions
  loadDefaults: () => Promise<void>
  toggleLayer: (id: LayerType) => void
  updateLayerContent: (id: LayerType, content: string) => void
  assemble: () => Promise<void>
  run: () => Promise<void>
  selectRun: (runId: string) => Promise<void>
  resetDemo: () => Promise<void>
}
```

## Component Specs

### `LayerCard`
- Toggle enabled/disabled
- Display title, description, color badge
- Show token estimate
- Collapsible content editor (textarea)
- Disabled state styled distinctly

### `PromptPreview`
- Shows `assembledPrompt` content (read-only, monospace)
- Total token counter with budget bar (`totalTokens / tokenBudgetMax`)
- "Assemble" button → calls `store.assemble()`

### `RunResultPanel`
- LLM response text block
- Quality score: `quality_score/40`
- Score breakdown: 8 labeled bars (0–5 each)
- Insight text
- Latency + token count
- "Run" button → calls `store.run()`

### `RunHistory`
- List of past runs (newest first)
- Each item: run number, active layer badges, score, tokens
- Click → calls `store.selectRun(runId)`
- "Reset Demo" button

## Key Conventions

- TypeScript strict mode — no `any`
- Immutable state in Zustand — always return new objects via `set()`
- All API calls in `src/api/workbench.ts` only — never fetch inside components
- Error messages surfaced in UI — never silently swallowed
- Use `VITE_API_BASE_URL` env var for base URL

## Dev Commands

```powershell
cd frontend
npm install
cp .env.example .env
npm run dev           # http://localhost:5173
npm run build         # type-check + build
```

## Build First

Before implementing any component:
1. Create `src/types/workbench.ts` — all types mirrored from backend
2. Create `src/api/workbench.ts` — all endpoint functions
3. Create `src/store/workbenchStore.ts` — Zustand store
4. Then build components bottom-up: LayerCard → PromptPreview → RunResultPanel → RunHistory → App
