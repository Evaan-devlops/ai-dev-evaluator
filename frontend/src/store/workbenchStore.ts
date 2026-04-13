import { create } from 'zustand'
import { workbenchApi } from '../api/workbenchApi'
import { FALLBACK_LAYERS, FALLBACK_HISTORY, FALLBACK_BEST_RUN } from '../data/demoFallback'
import type {
  ApiEvaluateResponse,
  ApiHistoryRow,
  ApiLayerDTO,
  ContextLayer,
  LayerType,
  RunHistoryItem,
  RunResult,
} from '../types'

// ─── Layer accent colors (frontend constants) ────────────────────────────────
const LAYER_COLORS: Record<LayerType, string> = {
  system:    '#67C587',
  user:      '#5B8DEF',
  history:   '#8B7CFF',
  knowledge: '#58C4DD',
  tools:     '#F5B14C',
  state:     '#E88AC6',
}

// Layers enabled by default on initial load
const DEFAULT_ENABLED = new Set<LayerType>(['system', 'user', 'history'])

// ─── Adapters ────────────────────────────────────────────────────────────────

function apiLayerToContextLayer(dto: ApiLayerDTO, index: number): ContextLayer {
  return {
    id: dto.key,
    title: dto.name,
    description: dto.subtitle,
    enabled: dto.always_on || DEFAULT_ENABLED.has(dto.key),
    content: dto.content,
    token_estimate: dto.tokens,
    order: index,
    collapsed: index > 1,
    color: LAYER_COLORS[dto.key] ?? '#888',
    warning: dto.warning,
    always_on: dto.always_on,
  }
}

function apiEvalToRunResult(r: ApiEvaluateResponse): RunResult {
  return {
    run_id: r.run_id,
    run_number: r.run_id,
    quality_score: r.score,
    score_max: 40,
    score_breakdown: r.breakdown,
    insight: r.insight,
    llm_response: r.model_response,
    latency_ms: r.latency_ms,
    total_tokens: r.token_budget_used,
    active_layers: r.active_layers,
    timestamp: new Date().toISOString(),
    provider: r.provider,
  }
}

function apiHistoryRowToItem(row: ApiHistoryRow): RunHistoryItem {
  return {
    run_id: row.run_id,
    run_number: row.run_id,
    active_layers: row.active_layers,
    quality_score: row.score,
    score_max: 40,
    total_tokens: row.tokens,
    latency_ms: row.latency_ms,
  }
}

/** Compute per-layer token map from enabled layers' stored estimates. */
function computeTokens(layers: ContextLayer[]): {
  perLayerTokens: Record<string, number>
  totalTokens: number
} {
  const perLayerTokens: Record<string, number> = {}
  let totalTokens = 0
  for (const layer of layers) {
    if (layer.enabled) {
      perLayerTokens[layer.id] = layer.token_estimate
      totalTokens += layer.token_estimate
    }
  }
  return { perLayerTokens, totalTokens }
}

/** Find the best (highest score) history item's run_id. */
function bestRunId(history: RunHistoryItem[]): number | null {
  if (history.length === 0) return null
  return history.reduce((best, item) =>
    item.quality_score > best.quality_score ? item : best,
  ).run_id
}

// ─── Store definition ────────────────────────────────────────────────────────

interface WorkbenchStore {
  // State
  layers: ContextLayer[]
  tokenBudgetMax: number
  assembledPrompt: string
  perLayerTokens: Record<string, number>
  totalTokens: number
  runHistory: RunHistoryItem[]
  selectedRun: RunResult | null
  isRunning: boolean
  isAssembling: boolean
  showAssembledPrompt: boolean
  error: string | null

  // Actions
  toggleLayer: (id: LayerType) => void
  updateLayerContent: (id: LayerType, content: string) => void
  toggleLayerCollapse: (id: LayerType) => void
  setTokenBudgetMax: (max: number) => void
  setShowAssembledPrompt: (show: boolean) => void
  assemble: () => Promise<void>
  run: () => Promise<void>
  selectRun: (runId: number) => Promise<void>
  loadDefaults: () => Promise<void>
  resetDemo: () => Promise<void>
  clearError: () => void
}

// Local cache: full run results keyed by run_id
const _runCache = new Map<number, RunResult>()

export const useWorkbenchStore = create<WorkbenchStore>((set, get) => ({
  layers: [],
  tokenBudgetMax: 4000,
  assembledPrompt: '',
  perLayerTokens: {},
  totalTokens: 0,
  runHistory: [],
  selectedRun: null,
  isRunning: false,
  isAssembling: false,
  showAssembledPrompt: false,
  error: null,

  clearError: () => set({ error: null }),

  toggleLayer: (id) => {
    const layers = get().layers.map((l) =>
      l.id === id && !l.always_on ? { ...l, enabled: !l.enabled } : l,
    )
    const { perLayerTokens, totalTokens } = computeTokens(layers)
    set({ layers, perLayerTokens, totalTokens })
  },

  updateLayerContent: (id, content) => {
    const layers = get().layers.map((l) => (l.id === id ? { ...l, content } : l))
    const { perLayerTokens, totalTokens } = computeTokens(layers)
    set({ layers, perLayerTokens, totalTokens })
  },

  toggleLayerCollapse: (id) => {
    const layers = get().layers.map((l) =>
      l.id === id ? { ...l, collapsed: !l.collapsed } : l,
    )
    set({ layers })
  },

  setTokenBudgetMax: (max) => set({ tokenBudgetMax: max }),

  setShowAssembledPrompt: (show) => set({ showAssembledPrompt: show }),

  assemble: async () => {
    const enabledLayers = get().layers.filter((l) => l.enabled).map((l) => l.id)
    if (enabledLayers.length === 0) {
      set({ assembledPrompt: '' })
      return
    }
    set({ isAssembling: true, error: null })
    try {
      const result = await workbenchApi.assemble(enabledLayers)
      const { perLayerTokens, totalTokens } = computeTokens(get().layers)
      set({
        assembledPrompt: result.assembled_prompt,
        perLayerTokens,
        totalTokens,
        isAssembling: false,
      })
    } catch (err) {
      set({ isAssembling: false, error: (err as Error).message })
    }
  },

  run: async () => {
    const enabledLayers = get().layers.filter((l) => l.enabled).map((l) => l.id)
    if (enabledLayers.length === 0) {
      set({ error: 'Enable at least one layer before running.' })
      return
    }

    set({ isRunning: true, error: null })

    try {
      const evalResult = await workbenchApi.evaluate(enabledLayers)
      const result = apiEvalToRunResult(evalResult)

      _runCache.set(result.run_id, result)

      const historyItem: RunHistoryItem = {
        run_id: result.run_id,
        run_number: result.run_number,
        active_layers: result.active_layers,
        quality_score: result.quality_score,
        score_max: result.score_max,
        total_tokens: result.total_tokens,
        latency_ms: result.latency_ms,
      }

      const { perLayerTokens, totalTokens } = computeTokens(get().layers)

      set((state) => ({
        runHistory: [...state.runHistory, historyItem],
        selectedRun: result,
        assembledPrompt: evalResult.assembled_prompt,
        perLayerTokens,
        totalTokens,
        isRunning: false,
      }))
    } catch (err) {
      set({ isRunning: false, error: (err as Error).message })
    }
  },

  selectRun: async (runId) => {
    // Fast path: already in cache
    const cached = _runCache.get(runId)
    if (cached) {
      set({ selectedRun: cached })
      return
    }
    // Fetch from API (supports seeded runs not yet in cache)
    try {
      const evalResult = await workbenchApi.getRunDetails(runId)
      const result = apiEvalToRunResult(evalResult)
      _runCache.set(runId, result)
      set({ selectedRun: result })
    } catch {
      // Silently ignore — run details unavailable
    }
  },

  loadDefaults: async () => {
    set({ error: null })
    try {
      // Fetch meta + history in parallel
      const [meta, historyRows] = await Promise.all([
        workbenchApi.getMeta(),
        workbenchApi.getHistory(),
      ])

      const layers = meta.layers.map((dto, i) => apiLayerToContextLayer(dto, i))
      const { perLayerTokens, totalTokens } = computeTokens(layers)
      const runHistory = historyRows.map(apiHistoryRowToItem)

      // Find the best run and fetch its full details
      const topId = bestRunId(runHistory)
      let selectedRun: RunResult | null = null

      if (topId !== null) {
        try {
          const evalResult = await workbenchApi.getRunDetails(topId)
          selectedRun = apiEvalToRunResult(evalResult)
          _runCache.set(topId, selectedRun)
        } catch {
          // Best run details unavailable — sidebar stays empty
        }
      }

      set({
        layers,
        tokenBudgetMax: meta.max_budget,
        perLayerTokens,
        totalTokens,
        runHistory,
        selectedRun,
      })
    } catch {
      // ── Fallback: backend unavailable — use client-side demo seed ──
      const layers = FALLBACK_LAYERS
      const { perLayerTokens, totalTokens } = computeTokens(layers)

      _runCache.clear()
      _runCache.set(FALLBACK_BEST_RUN.run_id, FALLBACK_BEST_RUN)

      set({
        layers,
        tokenBudgetMax: 4000,
        perLayerTokens,
        totalTokens,
        runHistory: FALLBACK_HISTORY,
        selectedRun: FALLBACK_BEST_RUN,
        error: null, // don't show error — fallback is seamless
      })
    }
  },

  resetDemo: async () => {
    set({ error: null })
    try {
      await workbenchApi.resetHistory()
      _runCache.clear()
      await get().loadDefaults()
    } catch (err) {
      set({ error: (err as Error).message })
    }
  },
}))
