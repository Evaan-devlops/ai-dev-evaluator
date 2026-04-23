import { create } from 'zustand'
import { llmApi } from '../api/llmApi'
import type { LayerType } from '../types'

export type LLMProvider = 'mock' | 'gemini' | 'openai' | 'nvidia'
export type CodingMode = 'vibe' | 'agentic'
export type DataSourceMode = 'mock' | 'manual' | 'actual'
export type ApiRequestMethod = 'GET' | 'POST'
export type ActualLayerType = Exclude<LayerType, 'user'>

export interface EvaluationParameter {
  id: string
  label: string
  description: string
}

export type EvaluationParameters = EvaluationParameter[]

export interface ApiConnectorConfig {
  enabled: boolean
  endpoint: string
  method: ApiRequestMethod
  promptParam: string
  headers: string
  bodyTemplate: string
  responsePath: string
  contentTemplate: string
  fallbackContent: string
  curlCommand: string
}

export interface NamedApiConnectorConfig extends ApiConnectorConfig {
  id: string
  name: string
}

export interface ActualDataIntegration extends ApiConnectorConfig {
  layerId: ActualLayerType
}

export interface KnowledgeApiConfig {
  ingestion: NamedApiConnectorConfig
  search: NamedApiConnectorConfig
}

export interface ToolApiConfig extends NamedApiConnectorConfig {}

export interface ModelResponseApiConfig extends ApiConnectorConfig {
  useSameLlmWhenDisabled: boolean
}

export interface DatabaseConfig {
  connectionString: string
  databasePort: string
  databaseSuperuser: string
  password: string
  dbName: string
  dbAlreadyExists: boolean
}

export interface LLMConfig {
  provider: LLMProvider
  dataSource: DataSourceMode
  prd: string
  prdParameters: EvaluationParameters
  // systemPromptText: direct textbox input for system layer when API is not used
  systemPromptText: string
  actualDataIntegrations: ActualDataIntegration[]
  knowledgeApi: KnowledgeApiConfig
  toolApis: ToolApiConfig[]
  modelResponseApi: ModelResponseApiConfig
  databaseConfig: DatabaseConfig
  ragServiceUrl: string
  ragDocumentId: string
  llmTested: boolean
  llmTestSignature: string
  geminiApiKey: string
  geminiModel: string
  openaiApiKey: string
  openaiModel: string
  nvidiaApiKey: string
  nvidiaModel: string
  temperature: number
  maxOutputTokens: number
  enableLiveProvider: boolean
}

interface LLMConfigStore {
  config: LLMConfig
  isConfigureOpen: boolean
  configureInitialSection: 'llm' | 'data' | 'prd' | 'db' | undefined
  codingMode: CodingMode
  openConfigure: () => void
  openConfigurePrd: () => void
  closeConfigure: () => void
  saveConfig: (config: LLMConfig) => void
  setCodingMode: (mode: CodingMode) => void
}

const STORAGE_KEY = 'ai-response-evaluator:llm-config'
const MODE_KEY = 'ai-response-evaluator:coding-mode'

export function slugifyEvaluationParameterId(value: string): string {
  const normalized = value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')

  return normalized || 'parameter'
}

export const DEFAULT_EVALUATION_PARAMETERS: EvaluationParameters = [
  {
    id: 'persona',
    label: 'Persona Adherence',
    description: 'How well the response follows the intended assistant persona and operating style.',
  },
  {
    id: 'policy',
    label: 'Policy Accuracy',
    description: 'Accuracy against product, support, compliance, or business rules.',
  },
  {
    id: 'empathy',
    label: 'Empathy & Tone',
    description: 'Tone, tact, and emotional fit for the user situation.',
  },
  {
    id: 'context',
    label: 'Context Awareness',
    description: 'Use of the supplied product, user, session, and data context.',
  },
  {
    id: 'actionability',
    label: 'Actionability',
    description: 'Specific next steps, instructions, or resolution path.',
  },
  {
    id: 'personalization',
    label: 'Personalization',
    description: 'Adaptation to the user, account, segment, or scenario.',
  },
  {
    id: 'hallucination',
    label: 'No Hallucination',
    description: 'Avoidance of unsupported claims or invented facts.',
  },
  {
    id: 'completeness',
    label: 'Completeness',
    description: 'Coverage of the required answer without important gaps.',
  },
]

const DEFAULT_CONNECTOR_TEMPLATE: ApiConnectorConfig = {
  enabled: false,
  endpoint: '',
  method: 'POST',
  promptParam: 'prompt',
  headers: '{\n  "Content-Type": "application/json"\n}',
  bodyTemplate: '{\n  "prompt": "{{prompt}}"\n}',
  responsePath: '',
  contentTemplate: '{{text}}',
  fallbackContent: '',
  curlCommand: '',
}

export const DEFAULT_ACTUAL_DATA_INTEGRATIONS: ActualDataIntegration[] = [
  {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    layerId: 'system',
    bodyTemplate: '{\n  "prompt": "{{prompt}}",\n  "channel": "support"\n}',
    responsePath: 'system_prompt',
  },
  {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    layerId: 'history',
    method: 'GET',
    headers: '',
    bodyTemplate: '',
    responsePath: 'conversation',
  },
  {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    layerId: 'knowledge',
    promptParam: 'query',
    bodyTemplate: '{\n  "query": "{{prompt}}",\n  "top_k": 5\n}',
    responsePath: 'results',
  },
  {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    layerId: 'tools',
    method: 'GET',
    headers: '',
    bodyTemplate: '',
    responsePath: 'tools',
  },
  {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    layerId: 'state',
    bodyTemplate: '{\n  "prompt": "{{prompt}}",\n  "include_account": true\n}',
    responsePath: 'profile',
  },
]

export const DEFAULT_MODEL_RESPONSE_API: ModelResponseApiConfig = {
  ...DEFAULT_CONNECTOR_TEMPLATE,
  promptParam: 'user_input',
  bodyTemplate: '{\n  "user_input": "{{prompt}}"\n}',
  responsePath: 'response',
  useSameLlmWhenDisabled: true,
}

export const DEFAULT_KNOWLEDGE_API: KnowledgeApiConfig = {
  ingestion: {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    id: 'knowledge-ingestion',
    name: 'RAG Ingestion API',
    promptParam: 'document',
    bodyTemplate: '{\n  "document": "{{prompt}}",\n  "metadata": {\n    "source": "playground"\n  }\n}',
    responsePath: 'message',
    contentTemplate: '{{text}}',
  },
  search: {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    id: 'knowledge-search',
    name: 'RAG Search API',
    promptParam: 'query',
    bodyTemplate: '{\n  "query": "{{prompt}}",\n  "top_k": 5\n}',
    responsePath: 'results',
  },
}

export const DEFAULT_TOOL_APIS: ToolApiConfig[] = [
  {
    ...DEFAULT_CONNECTOR_TEMPLATE,
    id: 'tool-api-1',
    name: 'Tool Catalog API',
    method: 'GET',
    headers: '',
    bodyTemplate: '',
    responsePath: 'tools',
  },
]

export const DEFAULT_DATABASE_CONFIG: DatabaseConfig = {
  connectionString: '',
  databasePort: '5432',
  databaseSuperuser: 'postgres',
  password: '',
  dbName: '',
  dbAlreadyExists: true,
}

function cloneEvaluationParameters(parameters: EvaluationParameters): EvaluationParameters {
  return parameters.map((parameter) => ({ ...parameter }))
}

function cloneActualDataIntegrations(integrations: ActualDataIntegration[]): ActualDataIntegration[] {
  return integrations.map((integration) => ({ ...integration }))
}

function cloneNamedConnector(config: NamedApiConnectorConfig): NamedApiConnectorConfig {
  return { ...config }
}

function cloneKnowledgeApi(config: KnowledgeApiConfig): KnowledgeApiConfig {
  return {
    ingestion: cloneNamedConnector(config.ingestion),
    search: cloneNamedConnector(config.search),
  }
}

function cloneToolApis(configs: ToolApiConfig[]): ToolApiConfig[] {
  return configs.map((config) => ({ ...config }))
}

function cloneModelResponseApi(config: ModelResponseApiConfig): ModelResponseApiConfig {
  return { ...config }
}

function cloneDatabaseConfig(config: DatabaseConfig): DatabaseConfig {
  return { ...config }
}

function normalizeEvaluationParameters(value: unknown): EvaluationParameters {
  if (Array.isArray(value)) {
    const normalized = value
      .map((entry, index) => {
        if (!entry || typeof entry !== 'object') return null
        const candidate = entry as Partial<EvaluationParameter>
        const label = String(candidate.label ?? '').trim()
        const description = String(candidate.description ?? '').trim()
        const id = slugifyEvaluationParameterId(String(candidate.id ?? (label || `parameter-${index + 1}`)))
        if (!label) return null
        return { id, label, description }
      })
      .filter((entry): entry is EvaluationParameter => entry !== null)

    if (normalized.length > 0) return normalized
  }

  if (value && typeof value === 'object') {
    const fromRecord = Object.entries(value as Record<string, unknown>)
      .map(([id, label]) => {
        const cleanLabel = String(label ?? '').trim()
        if (!cleanLabel) return null
        const fallback = DEFAULT_EVALUATION_PARAMETERS.find((parameter) => parameter.id === id)
        return {
          id: slugifyEvaluationParameterId(id),
          label: cleanLabel,
          description: fallback?.description ?? '',
        }
      })
      .filter((entry): entry is EvaluationParameter => entry !== null)

    if (fromRecord.length > 0) return fromRecord
  }

  return cloneEvaluationParameters(DEFAULT_EVALUATION_PARAMETERS)
}

function normalizeConnector(value: unknown, fallback: ApiConnectorConfig): ApiConnectorConfig {
  const candidate = value && typeof value === 'object' ? value as Partial<ApiConnectorConfig> : {}
  return {
    ...fallback,
    ...candidate,
    enabled: Boolean(candidate.enabled),
    endpoint: String(candidate.endpoint ?? fallback.endpoint),
    method: candidate.method === 'GET' ? 'GET' : 'POST',
    promptParam: String(candidate.promptParam ?? fallback.promptParam),
    headers: String(candidate.headers ?? fallback.headers),
    bodyTemplate: String(candidate.bodyTemplate ?? fallback.bodyTemplate),
    responsePath: String(candidate.responsePath ?? fallback.responsePath),
    contentTemplate: String(candidate.contentTemplate ?? fallback.contentTemplate),
    fallbackContent: String(candidate.fallbackContent ?? fallback.fallbackContent),
    curlCommand: String(candidate.curlCommand ?? fallback.curlCommand),
  }
}

function normalizeNamedConnector(value: unknown, fallback: NamedApiConnectorConfig): NamedApiConnectorConfig {
  const candidate = value && typeof value === 'object' ? value as Partial<NamedApiConnectorConfig> : {}
  return {
    ...normalizeConnector(candidate, fallback),
    id: String(candidate.id ?? fallback.id),
    name: String(candidate.name ?? fallback.name),
  }
}

function normalizeActualDataIntegrations(value: unknown): ActualDataIntegration[] {
  const defaults = new Map(DEFAULT_ACTUAL_DATA_INTEGRATIONS.map((integration) => [integration.layerId, integration]))
  if (!Array.isArray(value)) return cloneActualDataIntegrations(DEFAULT_ACTUAL_DATA_INTEGRATIONS)

  const normalized = new Map<ActualLayerType, ActualDataIntegration>()
  for (const entry of value) {
    if (!entry || typeof entry !== 'object') continue
    const candidate = entry as Partial<ActualDataIntegration>
    const layerId = candidate.layerId
    if (layerId !== 'system' && layerId !== 'history' && layerId !== 'knowledge' && layerId !== 'tools' && layerId !== 'state') {
      continue
    }
    const fallback = defaults.get(layerId) ?? DEFAULT_ACTUAL_DATA_INTEGRATIONS[0]
    normalized.set(layerId, {
      ...normalizeConnector(candidate, fallback),
      layerId,
    })
  }

  return DEFAULT_ACTUAL_DATA_INTEGRATIONS.map((integration) => ({
    ...integration,
    ...(normalized.get(integration.layerId) ?? {}),
  }))
}

function normalizeKnowledgeApi(
  knowledgeApiValue: unknown,
  legacyIntegrations: ActualDataIntegration[],
): KnowledgeApiConfig {
  const candidate = knowledgeApiValue && typeof knowledgeApiValue === 'object'
    ? knowledgeApiValue as Partial<KnowledgeApiConfig>
    : {}
  const legacyKnowledge = legacyIntegrations.find((integration) => integration.layerId === 'knowledge')

  return {
    ingestion: normalizeNamedConnector(candidate.ingestion, DEFAULT_KNOWLEDGE_API.ingestion),
    search: normalizeNamedConnector(candidate.search ?? legacyKnowledge, {
      ...DEFAULT_KNOWLEDGE_API.search,
      ...(legacyKnowledge ?? {}),
    }),
  }
}

function normalizeToolApis(
  toolApisValue: unknown,
  legacyIntegrations: ActualDataIntegration[],
): ToolApiConfig[] {
  if (Array.isArray(toolApisValue)) {
    const normalized = toolApisValue
      .map((entry, index) => normalizeNamedConnector(entry, {
        ...DEFAULT_TOOL_APIS[0],
        id: `tool-api-${index + 1}`,
        name: `Tool API ${index + 1}`,
      }))
      .filter((entry) => entry.name.trim().length > 0)

    if (normalized.length > 0) return normalized
  }

  const legacyTools = legacyIntegrations.find((integration) => integration.layerId === 'tools')
  if (legacyTools) {
    return [
      normalizeNamedConnector(legacyTools, {
        ...DEFAULT_TOOL_APIS[0],
        ...legacyTools,
        id: 'tool-api-1',
        name: 'Tool API 1',
      }),
    ]
  }

  return cloneToolApis(DEFAULT_TOOL_APIS)
}

function normalizeModelResponseApi(value: unknown): ModelResponseApiConfig {
  const candidate = value && typeof value === 'object' ? value as Partial<ModelResponseApiConfig> : {}
  return {
    ...normalizeConnector(candidate, DEFAULT_MODEL_RESPONSE_API),
    useSameLlmWhenDisabled: candidate.useSameLlmWhenDisabled ?? DEFAULT_MODEL_RESPONSE_API.useSameLlmWhenDisabled,
  }
}

function normalizeDatabaseConfig(value: unknown): DatabaseConfig {
  const candidate = value && typeof value === 'object' ? value as Partial<DatabaseConfig> : {}
  return {
    ...DEFAULT_DATABASE_CONFIG,
    ...candidate,
    connectionString: String(candidate.connectionString ?? DEFAULT_DATABASE_CONFIG.connectionString),
    databasePort: String(candidate.databasePort ?? DEFAULT_DATABASE_CONFIG.databasePort),
    databaseSuperuser: String(candidate.databaseSuperuser ?? DEFAULT_DATABASE_CONFIG.databaseSuperuser),
    password: String(candidate.password ?? DEFAULT_DATABASE_CONFIG.password),
    dbName: String(candidate.dbName ?? DEFAULT_DATABASE_CONFIG.dbName),
    dbAlreadyExists: candidate.dbAlreadyExists ?? DEFAULT_DATABASE_CONFIG.dbAlreadyExists,
  }
}

function loadMode(): CodingMode {
  try {
    const raw = localStorage.getItem(MODE_KEY)
    return raw === 'agentic' ? 'agentic' : 'vibe'
  } catch {
    return 'vibe'
  }
}

function saveMode(mode: CodingMode): void {
  try { localStorage.setItem(MODE_KEY, mode) } catch { /* ignore */ }
}

const DEFAULT_CONFIG: LLMConfig = {
  provider: 'mock',
  dataSource: 'mock',
  prd: '',
  prdParameters: cloneEvaluationParameters(DEFAULT_EVALUATION_PARAMETERS),
  systemPromptText: '',
  ragServiceUrl: 'http://localhost:8001',
  ragDocumentId: '',
  actualDataIntegrations: cloneActualDataIntegrations(DEFAULT_ACTUAL_DATA_INTEGRATIONS),
  knowledgeApi: cloneKnowledgeApi(DEFAULT_KNOWLEDGE_API),
  toolApis: cloneToolApis(DEFAULT_TOOL_APIS),
  modelResponseApi: cloneModelResponseApi(DEFAULT_MODEL_RESPONSE_API),
  databaseConfig: cloneDatabaseConfig(DEFAULT_DATABASE_CONFIG),
  llmTested: false,
  llmTestSignature: '',
  geminiApiKey: '',
  geminiModel: 'gemini-2.5-flash',
  openaiApiKey: '',
  openaiModel: 'gpt-4.1-mini',
  nvidiaApiKey: '',
  nvidiaModel: 'meta/llama-3.1-70b-instruct',
  temperature: 0.2,
  maxOutputTokens: 1200,
  enableLiveProvider: false,
}

function loadFromStorage(): LLMConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_CONFIG

    const parsed = JSON.parse(raw) as Omit<Partial<LLMConfig>, 'dataSource'> & { dataSource?: string }
    const rawDataSource = parsed.dataSource
    const dataSource = rawDataSource === 'dummy' ? 'mock' : rawDataSource
    const actualDataIntegrations = normalizeActualDataIntegrations(parsed.actualDataIntegrations)

    return {
      ...DEFAULT_CONFIG,
      ...parsed,
      dataSource: dataSource === 'manual' || dataSource === 'actual' || dataSource === 'mock'
        ? dataSource
        : DEFAULT_CONFIG.dataSource,
      prdParameters: normalizeEvaluationParameters(parsed.prdParameters),
      systemPromptText: String(parsed.systemPromptText ?? DEFAULT_CONFIG.systemPromptText),
      ragServiceUrl: String(parsed.ragServiceUrl ?? DEFAULT_CONFIG.ragServiceUrl),
      ragDocumentId: String(parsed.ragDocumentId ?? DEFAULT_CONFIG.ragDocumentId),
      actualDataIntegrations,
      knowledgeApi: normalizeKnowledgeApi(parsed.knowledgeApi, actualDataIntegrations),
      toolApis: normalizeToolApis(parsed.toolApis, actualDataIntegrations),
      modelResponseApi: normalizeModelResponseApi(parsed.modelResponseApi),
      databaseConfig: normalizeDatabaseConfig(parsed.databaseConfig),
    }
  } catch {
    return DEFAULT_CONFIG
  }
}

function saveToStorage(config: LLMConfig): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
  } catch {
    // ignore storage errors
  }
}

export const useLLMConfigStore = create<LLMConfigStore>((set) => ({
  config: loadFromStorage(),
  isConfigureOpen: false,
  configureInitialSection: undefined,
  codingMode: loadMode(),

  openConfigure: () => set({ isConfigureOpen: true, configureInitialSection: undefined }),
  openConfigurePrd: () => set({ isConfigureOpen: true, configureInitialSection: 'prd' }),
  closeConfigure: () => set({ isConfigureOpen: false, configureInitialSection: undefined }),

  saveConfig: (config) => {
    saveToStorage(config)
    set({ config, isConfigureOpen: false })
    // Sync DB settings to myRAG service (fire-and-forget)
    import('../api/documentsApi').then(({ syncDbConfigToRag }) => {
      void syncDbConfigToRag(config)
    }).catch(() => {/* ignore */})
  },

  setCodingMode: (mode) => {
    saveMode(mode)
    set({ codingMode: mode })
  },
}))

export function getSelectedModel(config: LLMConfig): string {
  if (config.provider === 'gemini') return config.geminiModel
  if (config.provider === 'openai') return config.openaiModel
  if (config.provider === 'nvidia') return config.nvidiaModel
  return 'mock-provider'
}

export function getSelectedApiKey(config: LLMConfig): string {
  if (config.provider === 'gemini') return config.geminiApiKey
  if (config.provider === 'openai') return config.openaiApiKey
  if (config.provider === 'nvidia') return config.nvidiaApiKey
  return ''
}

export async function generateModelResponse(
  config: LLMConfig,
  prompt: string,
  systemInstruction?: string,
): Promise<string> {
  if (!config.enableLiveProvider || config.provider === 'mock') return ''
  const apiKey = getSelectedApiKey(config).trim()
  if (!apiKey) return ''

  const response = await llmApi.generate({
    provider: config.provider,
    model: getSelectedModel(config),
    api_key: apiKey,
    input: prompt,
    system_instruction: systemInstruction ?? '',
    max_output_tokens: config.maxOutputTokens,
    temperature: config.temperature,
  })

  return response.output_text
}

export async function evaluateScoreBreakdown(
  _config: LLMConfig,
  _assembledPrompt: string,
  _response: string,
): Promise<null> {
  return null
}
