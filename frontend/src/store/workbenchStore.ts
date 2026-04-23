import { create } from 'zustand'
import { workbenchApi } from '../api/workbenchApi'
import { FALLBACK_BEST_RUN, FALLBACK_HISTORY, FALLBACK_LAYERS } from '../data/demoFallback'
import { useLLMConfigStore } from './llmConfigStore'
import type { DataSourceMode } from './llmConfigStore'
import type {
  ApiEvaluateResponse,
  ContextLayer,
  LayerType,
  RunHistoryItem,
  RunResult,
} from '../types'
import {
  assembleLayersLocally,
  buildPreviewRunResult,
  canRunPrdEvaluation,
  computeLayerTokenUsage,
  evaluateModelResponseWithPrd,
  estimateTokens,
  generateModelResponseFromConfig,
  hydrateActualDataLayers,
} from '../utils/contextRuntime'

const DEFAULT_ENABLED = new Set<LayerType>(['system', 'user', 'history'])

function apiEvalToRunResult(r: ApiEvaluateResponse): RunResult {
  return {
    run_id: r.run_id,
    run_number: r.run_id,
    quality_score: r.score,
    score_max: 100,
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

function cloneMockLayers(): ContextLayer[] {
  return FALLBACK_LAYERS.map((layer) => ({ ...layer }))
}

function createManualLayers(): ContextLayer[] {
  return FALLBACK_LAYERS.map((layer) => ({
    ...layer,
    enabled: layer.always_on || DEFAULT_ENABLED.has(layer.id),
    content: '',
    token_estimate: 0,
    warning: undefined,
  }))
}

function getUserPrompt(layers: ContextLayer[]): string {
  return layers.find((layer) => layer.id === 'user')?.content.trim() ?? ''
}

interface WorkbenchStore {
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
  dataSource: DataSourceMode

  toggleLayer: (id: LayerType) => void
  updateLayerContent: (id: LayerType, content: string) => void
  toggleLayerCollapse: (id: LayerType) => void
  setTokenBudgetMax: (max: number) => void
  setShowAssembledPrompt: (show: boolean) => void
  assemble: () => Promise<void>
  run: () => Promise<void>
  selectRun: (runId: number) => Promise<void>
  loadDefaults: (dataSource?: DataSourceMode) => Promise<void>
  resetDemo: () => Promise<void>
  clearError: () => void
}

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
  dataSource: 'mock',

  clearError: () => set({ error: null }),

  toggleLayer: (id) => {
    const layers = get().layers.map((layer) =>
      layer.id === id && !layer.always_on ? { ...layer, enabled: !layer.enabled } : layer,
    )
    const { perLayerTokens, totalTokens } = computeLayerTokenUsage(layers)
    set({ layers, perLayerTokens, totalTokens })
  },

  updateLayerContent: (id, content) => {
    const layers = get().layers.map((layer) =>
      layer.id === id ? { ...layer, content, token_estimate: estimateTokens(content), warning: undefined } : layer,
    )
    const { perLayerTokens, totalTokens } = computeLayerTokenUsage(layers)
    set({ layers, perLayerTokens, totalTokens })
  },

  toggleLayerCollapse: (id) => {
    const layers = get().layers.map((layer) =>
      layer.id === id ? { ...layer, collapsed: !layer.collapsed } : layer,
    )
    set({ layers })
  },

  setTokenBudgetMax: (max) => set({ tokenBudgetMax: max }),

  setShowAssembledPrompt: (show) => set({ showAssembledPrompt: show }),

  assemble: async () => {
    const { dataSource, layers } = get()
    const enabledLayers = layers.filter((layer) => layer.enabled).map((layer) => layer.id)

    if (enabledLayers.length === 0) {
      set({ assembledPrompt: '', error: 'Enable at least one layer before assembling.' })
      return
    }

    if (dataSource === 'actual' && !getUserPrompt(layers)) {
      set({ error: 'Enter a user prompt before assembling actual data connectors.' })
      return
    }

    if (dataSource !== 'mock') {
      set({ isAssembling: true, error: null })
      try {
        const config = useLLMConfigStore.getState().config
        const nextLayers = dataSource === 'actual'
          ? await hydrateActualDataLayers(layers, config)
          : layers.map((layer) => ({
              ...layer,
              token_estimate: estimateTokens(layer.content),
            }))

        const { assembledPrompt, perLayerTokens, totalTokens } = assembleLayersLocally(nextLayers)
        set({
          layers: nextLayers,
          assembledPrompt,
          perLayerTokens,
          totalTokens,
          isAssembling: false,
          error: null,
        })
      } catch (err) {
        set({ isAssembling: false, error: (err as Error).message })
      }
      return
    }

    set({ isAssembling: true, error: null })
    try {
      const result = await workbenchApi.assemble(enabledLayers)
      const { perLayerTokens, totalTokens } = computeLayerTokenUsage(get().layers)
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
    const { dataSource, layers, runHistory } = get()
    const enabledLayers = layers.filter((layer) => layer.enabled).map((layer) => layer.id)

    if (enabledLayers.length === 0) {
      set({ error: 'Enable at least one layer before running.' })
      return
    }

    if (dataSource === 'actual' && !getUserPrompt(layers)) {
      set({ error: 'Enter a user prompt before running actual data connectors.' })
      return
    }

    if (dataSource !== 'mock') {
      set({ isRunning: true, error: null })

      try {
        const config = useLLMConfigStore.getState().config
        const nextLayers = dataSource === 'actual'
          ? await hydrateActualDataLayers(layers, config)
          : layers.map((layer) => ({
              ...layer,
              token_estimate: estimateTokens(layer.content),
            }))
        const { assembledPrompt, perLayerTokens, totalTokens } = assembleLayersLocally(nextLayers)
        const modelResponse = await generateModelResponseFromConfig(getUserPrompt(nextLayers), config, assembledPrompt)
        const evaluation = canRunPrdEvaluation(config)
          ? await evaluateModelResponseWithPrd(config, nextLayers, getUserPrompt(nextLayers), modelResponse.text)
          : undefined
        const previewRun = buildPreviewRunResult(
          nextLayers,
          config,
          assembledPrompt,
          runHistory.length + 1,
          modelResponse.text,
          modelResponse.provider,
          modelResponse.latencyMs,
          evaluation,
        )

        _runCache.set(previewRun.run_id, previewRun)

        const historyItem: RunHistoryItem = {
          run_id: previewRun.run_id,
          run_number: previewRun.run_number,
          active_layers: previewRun.active_layers,
          quality_score: previewRun.quality_score,
          score_max: previewRun.score_max,
          total_tokens: previewRun.total_tokens,
          latency_ms: previewRun.latency_ms,
        }

        set((state) => ({
          layers: nextLayers,
          assembledPrompt,
          perLayerTokens,
          totalTokens,
          runHistory: [...state.runHistory, historyItem],
          selectedRun: previewRun,
          isRunning: false,
          error: null,
        }))
      } catch (err) {
        set({ isRunning: false, error: (err as Error).message })
      }

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

      const { perLayerTokens, totalTokens } = computeLayerTokenUsage(get().layers)

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
    const cached = _runCache.get(runId)
    if (cached) {
      set({ selectedRun: cached })
      return
    }

    if (get().dataSource !== 'mock') return

    try {
      const evalResult = await workbenchApi.getRunDetails(runId)
      const result = apiEvalToRunResult(evalResult)
      _runCache.set(runId, result)
      set({ selectedRun: result })
    } catch {
      // Run details unavailable.
    }
  },

  loadDefaults: async (dataSource = 'mock') => {
    set({ error: null, dataSource })

    if (dataSource !== 'mock') {
      _runCache.clear()
      set({
        layers: createManualLayers(),
        tokenBudgetMax: 4000,
        assembledPrompt: '',
        perLayerTokens: {},
        totalTokens: 0,
        runHistory: [],
        selectedRun: null,
        showAssembledPrompt: false,
        isRunning: false,
        isAssembling: false,
      })
      return
    }

    const layers = cloneMockLayers()
    const { perLayerTokens, totalTokens } = computeLayerTokenUsage(layers)

    _runCache.clear()
    _runCache.set(FALLBACK_BEST_RUN.run_id, FALLBACK_BEST_RUN)

    set({
      layers,
      tokenBudgetMax: 4000,
      assembledPrompt: '',
      perLayerTokens,
      totalTokens,
      runHistory: FALLBACK_HISTORY,
      selectedRun: FALLBACK_BEST_RUN,
      showAssembledPrompt: false,
      isRunning: false,
      isAssembling: false,
      error: null,
    })
  },

  resetDemo: async () => {
    _runCache.clear()
    await get().loadDefaults(get().dataSource)
  },
}))
