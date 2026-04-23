import { integrationApi } from '../api/integrationApi'
import { evaluationApi } from '../api/evaluationApi'
import type {
  ActualDataIntegration,
  ApiConnectorConfig,
  EvaluationParameter,
  LLMConfig,
} from '../store/llmConfigStore'
import {
  generateModelResponse,
  getSelectedApiKey,
  getSelectedModel,
} from '../store/llmConfigStore'
import type {
  ContextLayer,
  LayerType,
  RunResult,
} from '../types'

const SECTION_LABELS: Record<LayerType, string> = {
  system: '=== SYSTEM INSTRUCTIONS ===',
  user: '=== USER INPUT ===',
  history: '=== CONVERSATION HISTORY ===',
  knowledge: '=== RETRIEVED KNOWLEDGE ===',
  tools: '=== TOOL DEFINITIONS ===',
  state: '=== STATE & MEMORY ===',
}

const KEYWORD_HINTS: Array<{ pattern: RegExp; layers: LayerType[] }> = [
  { pattern: /(persona|tone|style|guardrail|instruction|policy|compliance)/i, layers: ['system'] },
  { pattern: /(history|conversation|continuity|context|grounding)/i, layers: ['history', 'knowledge'] },
  { pattern: /(retrieval|knowledge|accuracy|fact|citation|hallucination)/i, layers: ['knowledge'] },
  { pattern: /(tool|workflow|action|actionability|resolution|automation)/i, layers: ['tools'] },
  { pattern: /(state|memory|profile|personal|account|segment|tier)/i, layers: ['state', 'history'] },
  { pattern: /(empathy|frustration|customer|support)/i, layers: ['system', 'history', 'state'] },
]

const LAYER_FORMAT_GUIDANCE: Record<Exclude<LayerType, 'user'>, string> = {
  system: 'Rewrite this into clear operating instructions and guardrails for the model. Keep it factual and concise.',
  history: 'Rewrite this into chronological prior turns or notable session events. Preserve sequence and important facts.',
  knowledge: 'Rewrite this into grounded reference knowledge, policies, docs, or facts. Use bullets if helpful.',
  tools: 'Rewrite this into tool definitions, callable actions, parameters, or operational capabilities.',
  state: 'Rewrite this into durable user/account/session state such as tier, profile, risk flags, and preferences.',
}

function normalizeLayer(layer: ContextLayer, content: string, warning?: string): ContextLayer {
  return {
    ...layer,
    content,
    token_estimate: estimateTokens(content),
    warning,
  }
}

function scoreParameterCoverage(parameter: EvaluationParameter, active: Set<LayerType>): number {
  const searchable = `${parameter.id} ${parameter.label} ${parameter.description}`.toLowerCase()
  let score = 2 + Math.min(4, active.size)

  for (const hint of KEYWORD_HINTS) {
    if (!hint.pattern.test(searchable)) continue
    if (hint.layers.some((layer) => active.has(layer))) score += 2
    if (hint.layers.every((layer) => active.has(layer))) score += 2
  }

  if (parameter.description.trim().length > 24) score += 1

  return Math.max(1, Math.min(10, score))
}

async function formatLayerContentWithLlm(
  rawContent: string,
  layerId: Exclude<LayerType, 'user'>,
  config: LLMConfig,
): Promise<string> {
  const trimmed = rawContent.trim()
  if (!trimmed) return ''

  if (!config.enableLiveProvider || config.provider === 'mock' || !getSelectedApiKey(config).trim()) {
    return trimmed
  }

  const prompt = [
    `Layer: ${layerId}`,
    'Task: reshape the payload into context-layer content that a downstream LLM can consume directly.',
    'Constraints: keep only supported facts, preserve meaning, use plain text, and do not invent data.',
    '',
    'Payload:',
    trimmed,
  ].join('\n')

  const systemInstruction = LAYER_FORMAT_GUIDANCE[layerId]
  try {
    const output = await generateModelResponse(config, prompt, systemInstruction)
    return output.trim() || trimmed
  } catch {
    return trimmed
  }
}

async function executeConnector(
  prompt: string,
  connector: ApiConnectorConfig,
): Promise<string> {
  const response = await integrationApi.executeConnector({
    prompt,
    connector,
  })

  return response.extracted_text.trim() || connector.fallbackContent.trim()
}

function buildCombinedWarning(messages: string[]): string | undefined {
  const filtered = messages.map((message) => message.trim()).filter(Boolean)
  return filtered.length > 0 ? filtered.join(' ') : undefined
}

async function hydrateSingleLayer(
  layer: ContextLayer,
  connector: ApiConnectorConfig | undefined,
  prompt: string,
  config: LLMConfig,
): Promise<ContextLayer> {
  if (!connector?.enabled) {
    return normalizeLayer(layer, layer.content)
  }

  if (!connector.endpoint.trim()) {
    return normalizeLayer(
      layer,
      connector.fallbackContent.trim() || layer.content,
      'Connector enabled but endpoint is empty. Using fallback/manual content.',
    )
  }

  try {
    const fetched = await executeConnector(prompt, connector)
    const formatted = await formatLayerContentWithLlm(
      fetched.trim() || connector.fallbackContent.trim() || layer.content,
      layer.id as Exclude<LayerType, 'user'>,
      config,
    )

    return normalizeLayer(layer, formatted)
  } catch (error) {
    const fallback = connector.fallbackContent.trim() || layer.content
    return normalizeLayer(
      layer,
      fallback,
      `API sync failed: ${(error as Error).message}`,
    )
  }
}

async function hydrateToolsLayer(
  layer: ContextLayer,
  prompt: string,
  config: LLMConfig,
): Promise<ContextLayer> {
  const enabledApis = config.toolApis.filter((toolApi) => toolApi.enabled)
  if (enabledApis.length === 0) {
    return normalizeLayer(layer, layer.content)
  }

  const results = await Promise.all(enabledApis.map(async (toolApi) => {
    if (!toolApi.endpoint.trim()) {
      return {
        title: toolApi.name,
        content: toolApi.fallbackContent.trim(),
        warning: `${toolApi.name}: endpoint is empty. Using fallback content.`,
      }
    }

    try {
      const fetched = await executeConnector(prompt, toolApi)
      return {
        title: toolApi.name,
        content: fetched.trim() || toolApi.fallbackContent.trim(),
        warning: '',
      }
    } catch (error) {
      return {
        title: toolApi.name,
        content: toolApi.fallbackContent.trim(),
        warning: `${toolApi.name}: ${(error as Error).message}`,
      }
    }
  }))

  const combinedContent = results
    .filter((result) => result.content.trim().length > 0)
    .map((result) => `${result.title}\n${result.content.trim()}`)
    .join('\n\n')

  const formatted = await formatLayerContentWithLlm(
    combinedContent || layer.content,
    'tools',
    config,
  )

  return normalizeLayer(
    layer,
    formatted || layer.content,
    buildCombinedWarning(results.map((result) => result.warning)),
  )
}

async function hydrateKnowledgeLayer(
  layer: ContextLayer,
  prompt: string,
  config: LLMConfig,
): Promise<ContextLayer> {
  // Try RAG service first if configured
  const ragUrl = config.ragServiceUrl?.trim()
  const ragDocumentId = config.ragDocumentId?.trim()
  if (ragUrl && ragDocumentId) {
    // RAG search connector is configured — use it
    try {
      const response = await fetch(`${ragUrl.replace(/\/$/, '')}/api/v1/queries/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: ragDocumentId,
          query: prompt,
          top_k: 6,
          allow_agent: true,
        }),
      })
      if (!response.ok) {
        throw new Error(`myRAG search failed (${response.status})`)
      }
      const data = await response.json() as { answer?: string; evidence?: Array<{ text?: string }> }
      const evidence = Array.isArray(data.evidence)
        ? data.evidence.map((item) => item.text).filter(Boolean).join('\n\n')
        : ''
      const content = [data.answer, evidence].filter(Boolean).join('\n\n')
      if (content.trim()) {
        return normalizeLayer(layer, content.trim())
      }
    } catch (error) {
      if (!config.knowledgeApi.search.enabled) {
        return normalizeLayer(layer, layer.content, (error as Error).message)
      }
    }
  }

  // Fallback to direct search connector
  return hydrateSingleLayer(layer, config.knowledgeApi.search, prompt, config)
}

export async function generateModelResponseFromConfig(
  prompt: string,
  config: LLMConfig,
  assembledPrompt: string,
): Promise<{ text: string; provider: string; latencyMs: number }> {
  const startedAt = performance.now()

  if (config.modelResponseApi.enabled && config.modelResponseApi.endpoint.trim()) {
    const text = await executeConnector(prompt, config.modelResponseApi)
    return {
      text: text || 'Model response API returned no content.',
      provider: 'custom-response-api',
      latencyMs: Math.round(performance.now() - startedAt),
    }
  }

  if (config.modelResponseApi.useSameLlmWhenDisabled) {
    const generated = await generateModelResponse(config, assembledPrompt)
    if (generated.trim()) {
      return {
        text: generated.trim(),
        provider: `${config.provider}:${getSelectedModel(config)}`,
        latencyMs: Math.round(performance.now() - startedAt),
      }
    }
  }

  return {
    text: 'Context preview ready. Configure a dedicated model response API or enable a live provider to populate this section.',
    provider: `${config.dataSource}-preview`,
    latencyMs: Math.round(performance.now() - startedAt),
  }
}

export function buildEvaluationProviderConfig(config: LLMConfig): {
  provider: LLMConfig['provider']
  model: string
  api_key: string
  temperature: number
  max_output_tokens: number
} {
  return {
    provider: config.provider,
    model: getSelectedModel(config),
    api_key: getSelectedApiKey(config).trim(),
    temperature: config.temperature,
    max_output_tokens: config.maxOutputTokens,
  }
}

export function canRunPrdEvaluation(config: LLMConfig): boolean {
  return config.provider !== 'mock'
    && config.enableLiveProvider
    && getSelectedApiKey(config).trim().length > 0
    && config.prd.trim().length > 0
    && config.prdParameters.length > 0
}

export async function evaluateModelResponseWithPrd(
  config: LLMConfig,
  layers: ContextLayer[],
  userPrompt: string,
  modelResponse: string,
): Promise<{
  scoreBreakdown: Record<string, number>
  qualityScore: number
  scoreMax: number
  insight: string
  suggestions: string[]
  evaluationProvider: string
  referenceResponse: string
  selectedLayers: LayerType[]
  usedContext: Record<string, string>
  latencyMs: number
}> {
  const response = await evaluationApi.evaluateModelResponse(
    config,
    layers,
    userPrompt,
    modelResponse,
    buildEvaluationProviderConfig(config),
  )

  return {
    scoreBreakdown: response.score_breakdown,
    qualityScore: response.quality_score,
    scoreMax: response.score_max,
    insight: response.insight,
    suggestions: response.suggestions,
    evaluationProvider: response.evaluation_provider,
    referenceResponse: response.reference_response,
    selectedLayers: response.selected_layers,
    usedContext: response.used_context,
    latencyMs: response.latency_ms,
  }
}

export function estimateTokens(text: string): number {
  const trimmed = text.trim()
  if (!trimmed) return 0
  return Math.max(1, Math.ceil(trimmed.length / 4))
}

export function computeLayerTokenUsage(layers: ContextLayer[]): {
  perLayerTokens: Record<string, number>
  totalTokens: number
} {
  const perLayerTokens: Record<string, number> = {}
  let totalTokens = 0

  for (const layer of layers) {
    if (!layer.enabled) continue
    const tokens = layer.token_estimate > 0 ? layer.token_estimate : estimateTokens(layer.content)
    if (tokens <= 0) continue
    perLayerTokens[layer.id] = tokens
    totalTokens += tokens
  }

  return { perLayerTokens, totalTokens }
}

export function assembleLayersLocally(layers: ContextLayer[]): {
  assembledPrompt: string
  perLayerTokens: Record<string, number>
  totalTokens: number
} {
  const ordered = [...layers].sort((a, b) => a.order - b.order)
  const normalized = ordered.map((layer) => normalizeLayer(layer, layer.content, layer.warning))
  const enabled = normalized.filter((layer) => layer.enabled && layer.content.trim())

  const assembledPrompt = enabled
    .map((layer) => `${SECTION_LABELS[layer.id] ?? `=== ${layer.id.toUpperCase()} ===`}\n${layer.content}`)
    .join('\n\n')

  const { perLayerTokens, totalTokens } = computeLayerTokenUsage(normalized)
  return { assembledPrompt, perLayerTokens, totalTokens }
}

export async function hydrateActualDataLayers(
  layers: ContextLayer[],
  config: LLMConfig,
): Promise<ContextLayer[]> {
  const prompt = layers.find((layer) => layer.id === 'user')?.content.trim() ?? ''
  if (!prompt) {
    return layers.map((layer) => normalizeLayer(layer, layer.content, layer.warning))
  }

  const integrations = new Map(config.actualDataIntegrations.map((integration) => [integration.layerId, integration]))
  const nextLayers = await Promise.all(layers.map(async (layer) => {
    if (layer.id === 'user') {
      return normalizeLayer(layer, layer.content)
    }

    // System layer: use textbox content when API is disabled and text is provided
    if (layer.id === 'system') {
      const sysIntegration = integrations.get('system')
      if (!sysIntegration?.enabled && config.systemPromptText?.trim()) {
        return normalizeLayer(layer, config.systemPromptText.trim())
      }
      return hydrateSingleLayer(layer, sysIntegration, prompt, config)
    }

    if (layer.id === 'knowledge') {
      return hydrateKnowledgeLayer(layer, prompt, config)
    }

    if (layer.id === 'tools') {
      return hydrateToolsLayer(layer, prompt, config)
    }

    const integration = integrations.get(layer.id) as ActualDataIntegration | undefined
    return hydrateSingleLayer(layer, integration, prompt, config)
  }))

  return nextLayers
}

export function buildPreviewRunResult(
  layers: ContextLayer[],
  config: LLMConfig,
  assembledPrompt: string,
  runId: number,
  modelResponse: string,
  providerLabel: string,
  latencyMs: number,
  evaluation?: {
    scoreBreakdown: Record<string, number>
    qualityScore: number
    scoreMax: number
    insight: string
    suggestions: string[]
    referenceResponse: string
    selectedLayers: LayerType[]
    usedContext: Record<string, string>
  },
): RunResult {
  const activeLayers = layers.filter((layer) => layer.enabled && layer.content.trim())
  const activeSet = new Set(activeLayers.map((layer) => layer.id))
  const localScoreBreakdown = Object.fromEntries(
    config.prdParameters.map((parameter) => [parameter.id, scoreParameterCoverage(parameter, activeSet)]),
  )
  const scoreBreakdown = evaluation?.scoreBreakdown ?? localScoreBreakdown
  const scoreValues = Object.values(scoreBreakdown)
  const scoreTotal = evaluation?.qualityScore ?? (
    scoreValues.length > 0
      ? Math.round((scoreValues.reduce((sum, value) => sum + value, 0) / (scoreValues.length * 10)) * 100)
      : 0
  )
  const scoreMax = evaluation?.scoreMax ?? 100
  const tokenTotal = activeLayers.reduce((sum, layer) => sum + estimateTokens(layer.content), 0)
  const syncedLayers = activeLayers.filter((layer) => layer.id !== 'user' && layer.content.trim()).length

  return {
    run_id: runId,
    run_number: runId,
    quality_score: scoreTotal,
    score_max: scoreMax,
    score_breakdown: scoreBreakdown,
    insight: evaluation?.insight ?? [
      `${config.dataSource === 'actual' ? 'Actual-data connectors' : 'Manual context'} filled ${syncedLayers}/${Math.max(activeLayers.length - 1, 0)} non-user layers.`,
      assembledPrompt
        ? 'The assembled prompt is ready and the model response section has been populated from the configured response path.'
        : 'Add content to more layers to strengthen the assembled prompt.',
      'Result scoring is a 100-point preview based on layer coverage and parameter definitions until PRD evaluation is available.',
    ].join(' '),
    llm_response: modelResponse,
    reference_response: evaluation?.referenceResponse,
    suggestions: evaluation?.suggestions,
    evaluation_context_layers: evaluation?.selectedLayers,
    evaluation_context_summary: evaluation?.usedContext,
    latency_ms: latencyMs,
    total_tokens: tokenTotal,
    active_layers: activeLayers.map((layer) => layer.id),
    timestamp: new Date().toISOString(),
    provider: providerLabel,
  }
}
