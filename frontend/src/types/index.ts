// ─── Layer types ────────────────────────────────────────────────────────────

export type LayerType = 'system' | 'user' | 'history' | 'knowledge' | 'tools' | 'state'

/** UI state for a context layer (frontend shape). */
export interface ContextLayer {
  id: LayerType
  title: string
  description: string
  enabled: boolean
  content: string
  token_estimate: number
  order: number
  collapsed: boolean
  color: string
  warning?: string      // disabled-state warning from API
  always_on?: boolean   // user layer is always on
}

// ─── Score breakdown — matches /api/context/evaluate breakdown fields ────────

export interface RunScoreBreakdown {
  persona: number
  policy: number
  empathy: number
  context: number
  actionability: number
  personalization: number
  hallucination: number
  completeness: number
}

// ─── Run result (UI shape, adapted from EvaluateResponse) ───────────────────

export interface RunResult {
  run_id: number
  run_number: number          // same as run_id in new API
  quality_score: number       // = EvaluateResponse.score
  score_max: number           // always 40
  score_breakdown: RunScoreBreakdown
  insight: string
  llm_response: string        // = EvaluateResponse.model_response
  latency_ms: number
  total_tokens: number        // = EvaluateResponse.token_budget_used
  active_layers: LayerType[]
  timestamp: string
  provider: string
}

// ─── Run history row (UI shape, adapted from HistoryRow) ────────────────────

export interface RunHistoryItem {
  run_id: number
  run_number: number
  active_layers: LayerType[]
  quality_score: number       // = HistoryRow.score
  score_max: number           // always 40
  total_tokens: number        // = HistoryRow.tokens
  latency_ms: number
}

// ─── Raw API response shapes (what the server actually returns) ──────────────

export interface ApiLayerDTO {
  key: LayerType
  id: number
  name: string
  subtitle: string
  tokens: number
  always_on: boolean
  warning?: string
  content: string
}

export interface ApiContextMeta {
  max_budget: number
  ordered_layers: LayerType[]
  layers: ApiLayerDTO[]
}

export interface ApiScoreBreakdown {
  persona: number
  policy: number
  empathy: number
  context: number
  actionability: number
  personalization: number
  hallucination: number
  completeness: number
}

export interface ApiEvaluateResponse {
  run_id: number
  provider: string
  active_layers: LayerType[]
  active_count: number
  token_budget_used: number
  token_budget_max: number
  assembled_prompt: string
  model_response: string
  breakdown: ApiScoreBreakdown
  score: number
  latency_ms: number
  insight: string
}

export interface ApiAssembleResponse {
  active_layers: LayerType[]
  token_budget_used: number
  token_budget_max: number
  assembled_prompt: string
}

export interface ApiHistoryRow {
  run_id: number
  active_layers: LayerType[]
  score: number
  tokens: number
  latency_ms: number
  provider: string
}
