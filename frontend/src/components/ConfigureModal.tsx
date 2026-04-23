import React, { useEffect, useMemo, useRef, useState } from 'react'
import { evaluationApi } from '../api/evaluationApi'
import { integrationApi } from '../api/integrationApi'
import { llmApi } from '../api/llmApi'
import type {
  ActualDataIntegration,
  ActualLayerType,
  ApiConnectorConfig,
  DataSourceMode,
  DatabaseConfig,
  EvaluationParameter,
  KnowledgeApiConfig,
  LLMConfig,
  LLMProvider,
  ModelResponseApiConfig,
  ToolApiConfig,
} from '../store/llmConfigStore'
import {
  DEFAULT_ACTUAL_DATA_INTEGRATIONS,
  DEFAULT_DATABASE_CONFIG,
  DEFAULT_KNOWLEDGE_API,
  DEFAULT_MODEL_RESPONSE_API,
  DEFAULT_TOOL_APIS,
  getSelectedApiKey,
  getSelectedModel,
  slugifyEvaluationParameterId,
} from '../store/llmConfigStore'
import { Modal } from './Modal'
import styles from './ConfigureModal.module.css'

interface Props {
  isOpen: boolean
  config: LLMConfig
  onSave: (config: LLMConfig) => void
  onClose: () => void
  initialSection?: ConfigureSection
}

type ConfigureSection = 'llm' | 'data' | 'prd' | 'db'
type ActualSectionKey = 'system' | 'history' | 'knowledge' | 'tools' | 'state' | 'modelResponse'
type StatusKind = 'success' | 'error'

interface StatusState {
  kind: StatusKind
  message: string
}

const PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: 'mock', label: 'Mock Provider' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'nvidia', label: 'NVIDIA' },
]

const DATA_SOURCES: { value: DataSourceMode; label: string; description: string }[] = [
  { value: 'mock', label: 'Mock', description: 'Use the seeded demo scenario and sample records.' },
  { value: 'manual', label: 'Manual', description: 'Enter or edit scenario data directly for custom runs.' },
  { value: 'actual', label: 'Actual Data', description: 'Fetch non-user layers from your APIs, DB-backed services, or model response endpoint.' },
]

const ACTUAL_LAYER_COPY: Record<ActualLayerType, { title: string; description: string }> = {
  system: { title: 'System Instructions API', description: 'Fetch persona, guardrails, and operating instructions for the current prompt.' },
  history: { title: 'Conversation History API', description: 'Return relevant prior turns or ticket history for continuity.' },
  knowledge: { title: 'RAG / Knowledge APIs', description: 'Configure one API for ingestion and another for search so the knowledge layer can retrieve grounded facts.' },
  tools: { title: 'Tools APIs', description: 'Add one or more tool catalogs or capability endpoints and merge them into the tools layer.' },
  state: { title: 'State & Memory API', description: 'Return account state, preferences, user tier, and session context.' },
}

const DEFAULT_ACTUAL_SECTION_COLLAPSE: Record<ActualSectionKey, boolean> = {
  system: true,
  history: true,
  knowledge: true,
  tools: true,
  state: true,
  modelResponse: true,
}

const GEMINI_MODELS = [
  'gemini-3-pro-preview',
  'gemini-2.5-pro',
  'gemini-2.5-flash',
  'gemini-2.5-flash-lite',
  'gemini-2.5-flash-lite-preview-09-2025',
  'gemini-2.0-flash',
  'gemini-2.0-flash-lite',
  'gemini-1.5-pro',
  'gemini-1.5-flash',
  'gemini-1.5-flash-8b',
]

const OPENAI_MODELS = [
  'gpt-5.2',
  'gpt-5.2-pro',
  'gpt-5.1',
  'gpt-5.1-pro',
  'gpt-5',
  'gpt-5-pro',
  'gpt-5-mini',
  'gpt-5-nano',
  'gpt-4.1',
  'gpt-4.1-mini',
  'gpt-4.1-nano',
  'gpt-4o',
  'gpt-4o-mini',
  'o4-mini',
  'o3',
  'o3-mini',
  'o1',
  'o1-mini',
  'gpt-oss-120b',
  'gpt-oss-20b',
]

const NVIDIA_MODELS = [
  'deepseek-ai/deepseek-r1',
  'meta/llama-4-maverick-17b-128e-instruct',
  'meta/llama-4-scout-17b-16e-instruct',
  'meta/llama-3.3-70b-instruct',
  'meta/llama-3.1-405b-instruct',
  'meta/llama-3.1-70b-instruct',
  'meta/llama-3.1-8b-instruct',
  'nvidia/llama-3.1-nemotron-ultra-253b-v1',
  'nvidia/llama-3.1-nemotron-70b-instruct',
  'nvidia/llama-3.1-nemotron-51b-instruct',
  'nvidia/llama-3.1-nemotron-nano-8b-v1',
  'mistralai/mixtral-8x7b-instruct-v0.1',
  'mistralai/mistral-large',
  'mistralai/mistral-small-24b-instruct',
  'qwen/qwen2.5-coder-32b-instruct',
  'qwen/qwen2.5-72b-instruct',
  'google/gemma-3-27b-it',
  'google/gemma-2-27b-it',
  'openai/gpt-oss-120b',
  'openai/gpt-oss-20b',
]

function keyFingerprint(value: string): string {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = ((hash << 5) - hash + value.charCodeAt(i)) | 0
  }
  return `${value.length}:${hash.toString(36)}`
}

function testSignature(config: LLMConfig): string {
  return `${config.provider}:${getSelectedModel(config)}:${keyFingerprint(getSelectedApiKey(config))}`
}

function cloneConfig(config: LLMConfig): LLMConfig {
  return {
    ...config,
    prdParameters: config.prdParameters.map((parameter) => ({ ...parameter })),
    actualDataIntegrations: config.actualDataIntegrations.map((integration) => ({ ...integration })),
    knowledgeApi: {
      ingestion: { ...config.knowledgeApi.ingestion },
      search: { ...config.knowledgeApi.search },
    },
    toolApis: config.toolApis.map((toolApi) => ({ ...toolApi })),
    modelResponseApi: { ...config.modelResponseApi },
    databaseConfig: { ...config.databaseConfig },
  }
}

function ensureUniqueParameterIds(parameters: EvaluationParameter[]): EvaluationParameter[] {
  const seen = new Map<string, number>()
  return parameters.map((parameter, index) => {
    const baseId = slugifyEvaluationParameterId(parameter.id || parameter.label || `parameter-${index + 1}`)
    const count = seen.get(baseId) ?? 0
    seen.set(baseId, count + 1)
    return {
      ...parameter,
      id: count === 0 ? baseId : `${baseId}-${count + 1}`,
    }
  })
}

function sanitizeParameters(parameters: EvaluationParameter[]): EvaluationParameter[] {
  return ensureUniqueParameterIds(
    parameters
      .map((parameter, index) => ({
        id: slugifyEvaluationParameterId(parameter.id || parameter.label || `parameter-${index + 1}`),
        label: parameter.label.trim(),
        description: parameter.description.trim(),
      }))
      .filter((parameter) => parameter.label.length > 0),
  )
}

function createBlankParameter(index: number): EvaluationParameter {
  return { id: `parameter-${index}`, label: '', description: '' }
}

function createToolApi(index: number): ToolApiConfig {
  return {
    ...DEFAULT_TOOL_APIS[0],
    id: `tool-api-${index}`,
    name: `Tool API ${index}`,
  }
}

function tokenizeCurl(command: string): string[] {
  const tokens: string[] = []
  const pattern = /"([^"\\]*(?:\\.[^"\\]*)*)"|'([^'\\]*(?:\\.[^'\\]*)*)'|`([^`\\]*(?:\\.[^`\\]*)*)`|(\S+)/g
  let match: RegExpExecArray | null
  while ((match = pattern.exec(command)) !== null) {
    tokens.push(match[1] ?? match[2] ?? match[3] ?? match[4])
  }
  return tokens
}

function tryInjectPromptPlaceholder(body: string): { bodyTemplate: string; promptParam: string } {
  const promptKeys = ['prompt', 'query', 'q', 'message', 'user_input', 'input']
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>
    for (const key of promptKeys) {
      if (typeof parsed[key] === 'string') {
        parsed[key] = '{{prompt}}'
        return { bodyTemplate: JSON.stringify(parsed, null, 2), promptParam: key }
      }
    }
    const stringKeys = Object.keys(parsed).filter((key) => typeof parsed[key] === 'string')
    if (stringKeys.length === 1) {
      parsed[stringKeys[0]] = '{{prompt}}'
      return { bodyTemplate: JSON.stringify(parsed, null, 2), promptParam: stringKeys[0] }
    }
  } catch {
    // keep raw body if not JSON
  }
  return { bodyTemplate: body, promptParam: 'prompt' }
}

function parseCurlToConnector(curlCommand: string): Partial<ApiConnectorConfig> {
  const trimmed = curlCommand.trim()
  if (!trimmed) throw new Error('Paste a curl command first.')

  const tokens = tokenizeCurl(trimmed)
  const headers: Record<string, string> = {}
  let endpoint = ''
  let method: 'GET' | 'POST' = 'GET'
  let body = ''

  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i]
    if (token === 'curl') continue
    if (token === '-X' || token === '--request') {
      method = tokens[i + 1]?.toUpperCase() === 'GET' ? 'GET' : 'POST'
      i += 1
      continue
    }
    if (token === '-H' || token === '--header') {
      const header = tokens[i + 1] ?? ''
      const separator = header.indexOf(':')
      if (separator > 0) {
        headers[header.slice(0, separator).trim()] = header.slice(separator + 1).trim()
      }
      i += 1
      continue
    }
    if (token === '-d' || token === '--data' || token === '--data-raw' || token === '--data-binary') {
      body = tokens[i + 1] ?? ''
      method = 'POST'
      i += 1
      continue
    }
    if (!endpoint && /^https?:\/\//i.test(token)) {
      endpoint = token
    }
  }

  if (!endpoint) throw new Error('Could not find an endpoint URL in the curl command.')

  const url = new URL(endpoint)
  let promptParam = 'prompt'
  let normalizedEndpoint = `${url.origin}${url.pathname}`
  if (method === 'GET') {
    const promptKeys = ['prompt', 'query', 'q', 'message', 'user_input', 'input']
    for (const key of promptKeys) {
      if (url.searchParams.has(key)) {
        promptParam = key
        url.searchParams.set(key, '{{promptEncoded}}')
        break
      }
    }
    normalizedEndpoint = `${url.origin}${url.pathname}${url.search}`
  }

  const bodyTemplate = body ? tryInjectPromptPlaceholder(body) : { bodyTemplate: '', promptParam }

  return {
    endpoint: normalizedEndpoint,
    method,
    headers: Object.keys(headers).length > 0 ? JSON.stringify(headers, null, 2) : '',
    bodyTemplate: bodyTemplate.bodyTemplate,
    promptParam: body ? bodyTemplate.promptParam : promptParam,
    curlCommand: curlCommand.trim(),
  }
}

function ApiKeyField({
  label,
  value,
  placeholder,
  helper,
  onChange,
}: {
  label: string
  value: string
  placeholder: string
  helper?: string
  onChange: (v: string) => void
}) {
  const [show, setShow] = useState(false)
  return (
    <div className={styles.field}>
      <label className={styles.label}>{label}</label>
      <div className={styles.inputWrap}>
        <input
          type={show ? 'text' : 'password'}
          className={styles.input}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        <button type="button" className={styles.eyeBtn} onClick={() => setShow((s) => !s)} aria-label={show ? 'Hide key' : 'Show key'}>
          {show ? 'Hide' : 'Show'}
        </button>
      </div>
      {helper && <div className={styles.helper}>{helper}</div>}
    </div>
  )
}

function ModelSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  onChange: (v: string) => void
}) {
  return (
    <div className={styles.field}>
      <label className={styles.label}>{label}</label>
      <select className={styles.select} value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </div>
  )
}

export function ConfigureModal({ isOpen, config, onSave, onClose, initialSection }: Props): React.ReactElement | null {
  const [draft, setDraft] = useState<LLMConfig>(cloneConfig(config))
  const [activeSection, setActiveSection] = useState<ConfigureSection>(initialSection ?? 'llm')
  const [collapsedSections, setCollapsedSections] = useState<Record<ActualSectionKey, boolean>>(DEFAULT_ACTUAL_SECTION_COLLAPSE)
  const [editingParameters, setEditingParameters] = useState<Record<number, boolean>>({})
  const [isPrdInfoOpen, setIsPrdInfoOpen] = useState(false)
  const [isProcessingPrd, setIsProcessingPrd] = useState(false)
  const [isTestingLlm, setIsTestingLlm] = useState(false)
  const [testError, setTestError] = useState('')
  const [allowPrdEditBeforeTest, setAllowPrdEditBeforeTest] = useState(false)
  const [testPrompt, setTestPrompt] = useState('User reports an issue with billing and wants the next best action.')
  const [knowledgeDocumentSample, setKnowledgeDocumentSample] = useState('Paste a product document, support policy, or markdown chunk here to test RAG ingestion.')
  const [statusByKey, setStatusByKey] = useState<Record<string, StatusState | undefined>>({})
  const [loadingByKey, setLoadingByKey] = useState<Record<string, boolean>>({})
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!isOpen) return
    setDraft(cloneConfig(config))
    setTestError('')
    setAllowPrdEditBeforeTest(false)
    setIsProcessingPrd(false)
    setCollapsedSections(DEFAULT_ACTUAL_SECTION_COLLAPSE)
    setEditingParameters({})
    setStatusByKey({})
    setLoadingByKey({})
    if (initialSection) setActiveSection(initialSection)
  }, [config, isOpen, initialSection])

  const update = <K extends keyof LLMConfig>(key: K, value: LLMConfig[K]) => {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  const updateIntegration = (layerId: ActualLayerType, patch: Partial<ActualDataIntegration>) => {
    setDraft((prev) => ({
      ...prev,
      actualDataIntegrations: prev.actualDataIntegrations.map((integration) => (
        integration.layerId === layerId ? { ...integration, ...patch } : integration
      )),
    }))
  }

  const updateModelResponseApi = (patch: Partial<ModelResponseApiConfig>) => {
    setDraft((prev) => ({ ...prev, modelResponseApi: { ...prev.modelResponseApi, ...patch } }))
  }

  const updateKnowledgeConnector = (
    key: keyof KnowledgeApiConfig,
    patch: Partial<ApiConnectorConfig>,
  ) => {
    setDraft((prev) => ({
      ...prev,
      knowledgeApi: {
        ...prev.knowledgeApi,
        [key]: { ...prev.knowledgeApi[key], ...patch },
      },
    }))
  }

  const updateToolApi = (id: string, patch: Partial<ToolApiConfig>) => {
    setDraft((prev) => ({
      ...prev,
      toolApis: prev.toolApis.map((toolApi) => (
        toolApi.id === id ? { ...toolApi, ...patch } : toolApi
      )),
    }))
  }

  const addToolApi = () => {
    setDraft((prev) => ({
      ...prev,
      toolApis: [
        ...prev.toolApis,
        createToolApi(
          prev.toolApis.reduce((maxId, toolApi) => {
            const match = toolApi.id.match(/(\d+)$/)
            const value = match ? parseInt(match[1], 10) : 0
            return Math.max(maxId, value)
          }, 0) + 1,
        ),
      ],
    }))
  }

  const removeToolApi = (id: string) => {
    setDraft((prev) => ({
      ...prev,
      toolApis: prev.toolApis.filter((toolApi) => toolApi.id !== id),
    }))
  }

  const updateDatabaseConfig = (patch: Partial<DatabaseConfig>) => {
    setDraft((prev) => ({ ...prev, databaseConfig: { ...prev.databaseConfig, ...patch } }))
  }

  const updateParameter = (index: number, patch: Partial<EvaluationParameter>) => {
    setDraft((prev) => {
      const next = [...prev.prdParameters]
      const current = next[index]
      if (!current) return prev
      const updated = { ...current, ...patch }
      if (patch.label !== undefined && (!patch.id || patch.id === current.id)) {
        updated.id = slugifyEvaluationParameterId(patch.label || current.id)
      }
      next[index] = updated
      return { ...prev, prdParameters: next }
    })
  }

  const addParameter = () => {
    setDraft((prev) => ({
      ...prev,
      prdParameters: [...prev.prdParameters, createBlankParameter(prev.prdParameters.length + 1)],
    }))
    setEditingParameters((prev) => ({
      ...prev,
      [draft.prdParameters.length]: true,
    }))
  }

  const removeParameter = (index: number) => {
    setDraft((prev) => ({
      ...prev,
      prdParameters: prev.prdParameters.filter((_, parameterIndex) => parameterIndex !== index),
    }))
    setEditingParameters((prev) => {
      const next: Record<number, boolean> = {}
      Object.entries(prev).forEach(([key, value]) => {
        const numericKey = parseInt(key, 10)
        if (!value || numericKey === index) return
        next[numericKey > index ? numericKey - 1 : numericKey] = value
      })
      return next
    })
  }

  const toggleParameterEditing = (index: number) => {
    setEditingParameters((prev) => ({ ...prev, [index]: !prev[index] }))
  }

  const setStatus = (key: string, next?: StatusState) => {
    setStatusByKey((prev) => ({ ...prev, [key]: next }))
  }

  const setLoading = (key: string, next: boolean) => {
    setLoadingByKey((prev) => ({ ...prev, [key]: next }))
  }

  const toggleCollapsedSection = (key: ActualSectionKey) => {
    setCollapsedSections((prev) => {
      const isCurrentlyCollapsed = prev[key]
      if (isCurrentlyCollapsed) {
        return {
          system: true,
          history: true,
          knowledge: true,
          tools: true,
          state: true,
          modelResponse: true,
          [key]: false,
        }
      }

      return {
        ...prev,
        [key]: true,
      }
    })
  }

  const applyCurlToLayer = (layerId: ActualLayerType) => {
    const integration = draft.actualDataIntegrations.find((entry) => entry.layerId === layerId)
    if (!integration) return
    try {
      updateIntegration(layerId, parseCurlToConnector(integration.curlCommand))
      setStatus(`curl:${layerId}`, { kind: 'success', message: 'Curl command parsed and connector fields updated.' })
    } catch (error) {
      setStatus(`curl:${layerId}`, { kind: 'error', message: (error as Error).message })
    }
  }

  const applyCurlToModelResponse = () => {
    try {
      updateModelResponseApi(parseCurlToConnector(draft.modelResponseApi.curlCommand))
      setStatus('curl:model-response', { kind: 'success', message: 'Curl command parsed and model response connector updated.' })
    } catch (error) {
      setStatus('curl:model-response', { kind: 'error', message: (error as Error).message })
    }
  }

  const applyCurlToKnowledge = (key: keyof KnowledgeApiConfig) => {
    try {
      updateKnowledgeConnector(key, parseCurlToConnector(draft.knowledgeApi[key].curlCommand))
      setStatus(`curl:knowledge:${key}`, { kind: 'success', message: `${draft.knowledgeApi[key].name} curl parsed successfully.` })
    } catch (error) {
      setStatus(`curl:knowledge:${key}`, { kind: 'error', message: (error as Error).message })
    }
  }

  const applyCurlToToolApi = (id: string) => {
    const toolApi = draft.toolApis.find((entry) => entry.id === id)
    if (!toolApi) return
    try {
      updateToolApi(id, parseCurlToConnector(toolApi.curlCommand))
      setStatus(`curl:tool:${id}`, { kind: 'success', message: `${toolApi.name} curl parsed successfully.` })
    } catch (error) {
      setStatus(`curl:tool:${id}`, { kind: 'error', message: (error as Error).message })
    }
  }

  const testConnector = async (key: string, connector: ApiConnectorConfig, promptOverride?: string) => {
    setLoading(key, true)
    setStatus(key, undefined)
    try {
      const result = await integrationApi.executeConnector({ prompt: promptOverride ?? testPrompt, connector })
      setStatus(key, { kind: 'success', message: `HTTP ${result.status_code}. Extracted ${Math.max(result.extracted_text.length, 1)} characters from ${result.request_method} ${result.request_url}.` })
    } catch (error) {
      setStatus(key, { kind: 'error', message: (error as Error).message })
    } finally {
      setLoading(key, false)
    }
  }

  const testDatabase = async () => {
    setLoading('db:test', true)
    setStatus('db:test', undefined)
    try {
      const result = await integrationApi.configureDatabase(draft.databaseConfig)
      updateDatabaseConfig({ connectionString: result.normalized_connection_string })
      setStatus('db:test', { kind: 'success', message: result.message })
    } catch (error) {
      setStatus('db:test', { kind: 'error', message: (error as Error).message })
    } finally {
      setLoading('db:test', false)
    }
  }

  const handleSave = () => {
    onSave({
      ...draft,
      prdParameters: sanitizeParameters(draft.prdParameters),
      actualDataIntegrations: DEFAULT_ACTUAL_DATA_INTEGRATIONS.map((defaults) => ({
        ...defaults,
        ...(draft.actualDataIntegrations.find((integration) => integration.layerId === defaults.layerId) ?? {}),
      })),
      knowledgeApi: {
        ingestion: {
          ...DEFAULT_KNOWLEDGE_API.ingestion,
          ...draft.knowledgeApi.ingestion,
        },
        search: {
          ...DEFAULT_KNOWLEDGE_API.search,
          ...draft.knowledgeApi.search,
        },
      },
      toolApis: (draft.toolApis.length > 0 ? draft.toolApis : DEFAULT_TOOL_APIS).map((toolApi, index) => ({
        ...DEFAULT_TOOL_APIS[0],
        ...toolApi,
        id: toolApi.id || `tool-api-${index + 1}`,
        name: toolApi.name.trim() || `Tool API ${index + 1}`,
      })),
      modelResponseApi: {
        ...DEFAULT_MODEL_RESPONSE_API,
        ...draft.modelResponseApi,
      },
      databaseConfig: {
        ...DEFAULT_DATABASE_CONFIG,
        ...draft.databaseConfig,
      },
    })
  }

  const currentTestSignature = useMemo(() => testSignature(draft), [draft])
  const isLlmTestCurrent = draft.llmTested && draft.llmTestSignature === currentTestSignature
  const canTestLlm = draft.provider === 'mock' || getSelectedApiKey(draft).trim().length > 0
  const prdApplicable = draft.dataSource !== 'mock'
  const canEditPrd = prdApplicable && (isLlmTestCurrent || allowPrdEditBeforeTest)

  const handleTestLlm = async () => {
    const signatureAtStart = currentTestSignature
    setIsTestingLlm(true)
    setTestError('')
    try {
      await llmApi.test({
        provider: draft.provider,
        model: getSelectedModel(draft),
        api_key: getSelectedApiKey(draft),
      })
      setDraft((prev) => ({ ...prev, llmTested: true, llmTestSignature: signatureAtStart }))
    } catch (error) {
      setDraft((prev) => ({ ...prev, llmTested: false, llmTestSignature: '' }))
      setTestError((error as Error).message)
    } finally {
      setIsTestingLlm(false)
    }
  }

  const handlePrdUpload = (file: File | undefined) => {
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => update('prd', String(reader.result ?? ''))
    reader.readAsText(file)
  }

  const handleProcessPrd = async () => {
    if (!draft.prd.trim()) {
      setStatus('prd:process', { kind: 'error', message: 'Enter or upload a PRD first.' })
      return
    }

    if (draft.provider === 'mock' || !getSelectedApiKey(draft).trim()) {
      setStatus('prd:process', { kind: 'error', message: 'Configure and test a live LLM provider before processing the PRD.' })
      return
    }

    setIsProcessingPrd(true)
    setStatus('prd:process', undefined)

    try {
      const response = await evaluationApi.processPrd(
        draft.prd,
        draft.prdParameters,
        {
          provider: draft.provider,
          model: getSelectedModel(draft),
          api_key: getSelectedApiKey(draft),
          temperature: draft.temperature,
          max_output_tokens: draft.maxOutputTokens,
        },
      )

      setDraft((prev) => ({
        ...prev,
        prdParameters: ensureUniqueParameterIds(response.parameters),
      }))
      setEditingParameters({})
      setStatus('prd:process', { kind: 'success', message: response.rationale || 'PRD processed and evaluation parameters updated.' })
    } catch (error) {
      setStatus('prd:process', { kind: 'error', message: (error as Error).message })
    } finally {
      setIsProcessingPrd(false)
    }
  }

  const renderStatus = (key: string) => {
    const status = statusByKey[key]
    if (!status) return null
    return (
      <div className={status.kind === 'success' ? styles.inlineSuccess : styles.inlineError}>
        {status.message}
      </div>
    )
  }

  const renderActualSection = (
    sectionKey: ActualSectionKey,
    title: string,
    description: string,
    children: React.ReactNode,
    badge?: string,
  ) => {
    const collapsed = collapsedSections[sectionKey]
    return (
      <section className={styles.actualSection}>
        <button
          type="button"
          className={styles.actualSectionHeader}
          onClick={() => toggleCollapsedSection(sectionKey)}
          aria-expanded={!collapsed}
        >
          <div className={styles.actualSectionHeaderMain}>
            <div className={styles.actualSectionTitleRow}>
              <span className={styles.actualSectionTitle}>{title}</span>
              {badge && <span className={styles.actualSectionBadge}>{badge}</span>}
            </div>
            <div className={styles.actualSectionDescription}>{description}</div>
          </div>
          <span className={`${styles.actualSectionChevron}${collapsed ? '' : ` ${styles.actualSectionChevronOpen}`}`}>
            ^
          </span>
        </button>
        {!collapsed && <div className={styles.actualSectionBody}>{children}</div>}
      </section>
    )
  }

  const renderConnectorFields = (
    title: string,
    description: string,
    key: string,
    connector: ApiConnectorConfig,
    onUpdate: (patch: Partial<ApiConnectorConfig>) => void,
    onApplyCurl: () => void,
    options?: {
      curlStatusKey?: string
      testPromptOverride?: string
      beforeGrid?: React.ReactNode
      afterGrid?: React.ReactNode
      footerActions?: React.ReactNode
    },
  ) => (
    <div className={styles.subConnectorCard}>
      <div className={styles.subConnectorHeader}>
        <div>
          <div className={styles.subConnectorTitle}>{title}</div>
          <div className={styles.subConnectorDescription}>{description}</div>
        </div>
        <label className={styles.connectorToggle}>
          <input type="checkbox" checked={connector.enabled} onChange={(e) => onUpdate({ enabled: e.target.checked })} />
          <span>{connector.enabled ? 'Enabled' : 'Disabled'}</span>
        </label>
      </div>

      <div className={styles.integrationActions}>
        {options?.footerActions}
        <button type="button" className={styles.secondaryBtn} onClick={onApplyCurl}>
          Apply Curl
        </button>
        <button
          type="button"
          className={styles.testBtn}
          disabled={loadingByKey[key]}
          onClick={() => void testConnector(key, connector, options?.testPromptOverride)}
        >
          {loadingByKey[key] ? 'Testing...' : 'Test API'}
        </button>
      </div>
      {renderStatus(key)}
      {renderStatus(options?.curlStatusKey ?? `curl:${key.replace('connector:', '')}`)}
      {options?.beforeGrid}

      <div className={styles.integrationGrid}>
        <div className={styles.field}>
          <label className={styles.label}>Paste Curl</label>
          <textarea
            className={styles.codeArea}
            value={connector.curlCommand}
            onChange={(e) => onUpdate({ curlCommand: e.target.value })}
            placeholder={`curl -X POST "https://api.example.com" -H "Authorization: Bearer token" -d '{"prompt":"{{prompt}}"}'`}
            spellCheck={false}
          />
          <div className={styles.helper}>You can wire the API by curl only. Use <code>{'{{prompt}}'}</code> in the body or a prompt query param in the URL.</div>
        </div>

        <div className={styles.field}>
          <label className={styles.label}>Endpoint URL</label>
          <input className={styles.input} value={connector.endpoint} onChange={(e) => onUpdate({ endpoint: e.target.value })} spellCheck={false} />
          <div className={styles.helper}>Supports placeholders like <code>{'{{prompt}}'}</code> and <code>{'{{promptEncoded}}'}</code>.</div>
        </div>

        <div className={styles.twoCol}>
          <div className={styles.field}>
            <label className={styles.label}>Method</label>
            <select className={styles.select} value={connector.method} onChange={(e) => onUpdate({ method: e.target.value === 'GET' ? 'GET' : 'POST' })}>
              <option value="GET">GET</option>
              <option value="POST">POST</option>
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Prompt Field</label>
            <input className={styles.input} value={connector.promptParam} onChange={(e) => onUpdate({ promptParam: e.target.value })} spellCheck={false} />
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.label}>Headers JSON</label>
          <textarea className={styles.codeArea} value={connector.headers} onChange={(e) => onUpdate({ headers: e.target.value })} spellCheck={false} />
        </div>

        <div className={styles.field}>
          <label className={styles.label}>POST Body Template</label>
          <textarea className={styles.codeArea} value={connector.bodyTemplate} onChange={(e) => onUpdate({ bodyTemplate: e.target.value })} spellCheck={false} />
        </div>

        <div className={styles.twoCol}>
          <div className={styles.field}>
            <label className={styles.label}>Response Path</label>
            <input className={styles.input} value={connector.responsePath} onChange={(e) => onUpdate({ responsePath: e.target.value })} spellCheck={false} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Content Template</label>
            <input className={styles.input} value={connector.contentTemplate} onChange={(e) => onUpdate({ contentTemplate: e.target.value })} spellCheck={false} />
            <div className={styles.helper}>Use <code>{'{{text}}'}</code> or <code>{'{{json}}'}</code> when shaping the extracted payload.</div>
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.label}>Fallback Content</label>
          <textarea className={styles.prdInput} value={connector.fallbackContent} onChange={(e) => onUpdate({ fallbackContent: e.target.value })} spellCheck />
        </div>
      </div>
      {options?.afterGrid}
    </div>
  )

  const renderLlmSection = () => (
    <>
      <div className={styles.section}>
        <div className={styles.sectionLabel}>Provider</div>
        <div className={styles.providerRow}>
          {PROVIDERS.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              className={`${styles.providerBtn}${draft.provider === value ? ` ${styles.providerBtnActive}` : ''}`}
              onClick={() => update('provider', value)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className={styles.statusLine}>
          Currently using: <strong>{PROVIDERS.find((entry) => entry.value === draft.provider)?.label ?? draft.provider}</strong>
          {draft.enableLiveProvider && draft.provider !== 'mock' && <span className={styles.liveChip}>live</span>}
        </div>
      </div>

      {draft.provider === 'gemini' && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Gemini Configuration</div>
          <ApiKeyField label="Gemini API Key" value={draft.geminiApiKey} placeholder="Enter Gemini API key" helper="Used for layer rephrasing and default model response generation." onChange={(v) => update('geminiApiKey', v)} />
          <ModelSelect label="Model" value={draft.geminiModel} options={GEMINI_MODELS} onChange={(v) => update('geminiModel', v)} />
        </div>
      )}

      {draft.provider === 'openai' && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>OpenAI Configuration</div>
          <ApiKeyField label="OpenAI API Key" value={draft.openaiApiKey} placeholder="sk-..." helper="Used for layer rephrasing and default model response generation." onChange={(v) => update('openaiApiKey', v)} />
          <ModelSelect label="Model" value={draft.openaiModel} options={OPENAI_MODELS} onChange={(v) => update('openaiModel', v)} />
        </div>
      )}

      {draft.provider === 'nvidia' && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>NVIDIA Configuration</div>
          <ApiKeyField label="NVIDIA API Key" value={draft.nvidiaApiKey} placeholder="Enter NVIDIA API key" helper="Used for layer rephrasing and default model response generation." onChange={(v) => update('nvidiaApiKey', v)} />
          <ModelSelect label="Model" value={draft.nvidiaModel} options={NVIDIA_MODELS} onChange={(v) => update('nvidiaModel', v)} />
        </div>
      )}

      <div className={styles.section}>
        <div className={styles.sectionLabel}>Generation Settings</div>
        <div className={styles.twoCol}>
          <div className={styles.field}>
            <label className={styles.label}>Temperature</label>
            <input type="number" className={styles.input} value={draft.temperature} min={0} max={2} step={0.1} onChange={(e) => update('temperature', parseFloat(e.target.value) || 0)} />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Max Output Tokens</label>
            <input type="number" className={styles.input} value={draft.maxOutputTokens} min={100} max={8000} step={100} onChange={(e) => update('maxOutputTokens', parseInt(e.target.value, 10) || 1200)} />
          </div>
        </div>

        <div className={styles.testRow}>
          <div>
            <div className={styles.toggleLabel}>Connection test</div>
            <div className={styles.toggleHelper}>Sends a short request to confirm the selected provider and model work.</div>
          </div>
          <div className={styles.testActions}>
            {isLlmTestCurrent && <span className={styles.testStatusOk}>Verified</span>}
            <button className={styles.testBtn} type="button" onClick={() => void handleTestLlm()} disabled={!canTestLlm || isTestingLlm}>
              {isTestingLlm ? 'Testing...' : 'Test LLM'}
            </button>
          </div>
        </div>
        {testError && <div className={styles.testError}>{testError}</div>}

        <div className={styles.toggleRow}>
          <div>
            <div className={styles.toggleLabel}>Enable live provider use</div>
            <div className={styles.toggleHelper}>When enabled, fetched context can be rephrased through the configured LLM and the same LLM can drive model response generation.</div>
          </div>
          <label className={styles.toggle}>
            <input type="checkbox" checked={draft.enableLiveProvider} onChange={(e) => update('enableLiveProvider', e.target.checked)} />
            <span className={`${styles.toggleTrack}${draft.enableLiveProvider ? ` ${styles.toggleOn}` : ''}`}>
              <span className={styles.toggleThumb} />
            </span>
          </label>
        </div>
      </div>
    </>
  )

  const renderDataSection = () => (
    <>
      <div className={styles.section}>
        <div className={styles.sectionLabel}>Data Source</div>
        <div className={styles.dataOptions}>
          {DATA_SOURCES.map(({ value, label, description }) => (
            <button
              key={value}
              type="button"
              className={`${styles.dataOption}${draft.dataSource === value ? ` ${styles.dataOptionActive}` : ''}`}
              onClick={() => update('dataSource', value)}
              aria-pressed={draft.dataSource === value}
            >
              <span className={styles.dataOptionTitle}>{label}</span>
              <span className={styles.dataOptionText}>{description}</span>
            </button>
          ))}
        </div>
      </div>

      {draft.dataSource === 'manual' && (
        <div className={styles.notice}>
          <span className={styles.noticeIcon}>i</span>
          <span className={styles.noticeText}>Manual mode keeps all layers editable in the workbench. Actual Data mode proxies external connectors through the backend so you can safely test them here.</span>
        </div>
      )}

      {draft.dataSource === 'actual' && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Actual Data Setup</div>
          <div className={styles.integrationIntro}>
            <div className={styles.integrationTitle}>Configure APIs, curl, and response shaping here</div>
            <div className={styles.integrationText}>
              Every non-user layer is populated from the current workbench <strong>User Input</strong>. The backend proxies the request, extracts the payload, and the configured LLM can further rephrase it into the clean context-layer format used by the mock demo.
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>Test Prompt</label>
            <textarea className={styles.prdInput} value={testPrompt} onChange={(e) => setTestPrompt(e.target.value)} spellCheck />
            <div className={styles.helper}>Used by all Test API buttons in this section.</div>
          </div>

          <div className={styles.docsCard}>
            <div className={styles.docsTitle}>API Shape Guidance</div>
            <div className={styles.docsText}>
              You can configure by individual fields or paste a curl command. For best results, return JSON and set a <code>response path</code> such as <code>results[0].content</code> or <code>data.answer</code>. If your endpoint returns raw text, leave response path empty.
            </div>
          </div>

          <div className={styles.integrationList}>
            {(['system', 'history', 'state'] as const).map((layerId) => {
              const integration = draft.actualDataIntegrations.find((entry) => entry.layerId === layerId)
              if (!integration) return null

              return (
                <React.Fragment key={layerId}>
                  {renderActualSection(
                    layerId,
                    ACTUAL_LAYER_COPY[layerId].title,
                    ACTUAL_LAYER_COPY[layerId].description,
                    <>
                      {/* System layer: direct textbox option when API disabled */}
                      {layerId === 'system' && (
                        <div className={styles.subConnectorCard}>
                          <div className={styles.subConnectorHeader}>
                            <div>
                              <div className={styles.subConnectorTitle}>System Prompt Textbox</div>
                              <div className={styles.subConnectorDescription}>
                                Enter the system prompt directly. Used when the API above is disabled.
                              </div>
                            </div>
                          </div>
                          <div className={styles.field}>
                            <label className={styles.label}>System Prompt</label>
                            <textarea
                              className={styles.prdInput}
                              value={draft.systemPromptText}
                              onChange={(e) => update('systemPromptText', e.target.value)}
                              placeholder="You are a helpful assistant. Follow the policies..."
                              spellCheck
                              rows={5}
                            />
                            <div className={styles.helper}>
                              Saved and used as the system layer when the API connector above is disabled.
                            </div>
                          </div>
                        </div>
                      )}
                      {renderConnectorFields(
                        ACTUAL_LAYER_COPY[layerId].title,
                        ACTUAL_LAYER_COPY[layerId].description,
                        `connector:${layerId}`,
                        integration,
                        (patch) => updateIntegration(layerId, patch as Partial<ActualDataIntegration>),
                        () => applyCurlToLayer(layerId),
                      )}
                    </>,
                  )}
                </React.Fragment>
              )
            })}

            {renderActualSection(
              'knowledge',
              ACTUAL_LAYER_COPY.knowledge.title,
              ACTUAL_LAYER_COPY.knowledge.description,
              <>
                <div className={styles.subConnectorCard}>
                  <div className={styles.subConnectorHeader}>
                    <div>
                      <div className={styles.subConnectorTitle}>Built-in RAG Service URL</div>
                      <div className={styles.subConnectorDescription}>
                        Point to a running instance of the bundled RAG backend (<code>rag_service/</code>). When set, it is used for knowledge retrieval during evaluation instead of the Search API below.
                      </div>
                    </div>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>RAG Service Base URL</label>
                    <input
                      className={styles.input}
                      value={draft.ragServiceUrl ?? ''}
                      onChange={(e) => update('ragServiceUrl', e.target.value)}
                      placeholder="http://localhost:8001"
                      spellCheck={false}
                    />
                    <div className={styles.helper}>
                      Leave blank to use the Search API connector below instead.
                    </div>
                  </div>
                </div>
                {renderConnectorFields(
                  'RAG Ingestion API',
                  'Use this to push documents or chunks into your retrieval system. This is for indexing, not prompt-time retrieval.',
                  'connector:knowledge:ingestion',
                  draft.knowledgeApi.ingestion,
                  (patch) => updateKnowledgeConnector('ingestion', patch),
                  () => applyCurlToKnowledge('ingestion'),
                  {
                    curlStatusKey: 'curl:knowledge:ingestion',
                    testPromptOverride: knowledgeDocumentSample,
                    beforeGrid: (
                      <div className={styles.field}>
                        <label className={styles.label}>Document Sample For Test</label>
                        <textarea className={styles.prdInput} value={knowledgeDocumentSample} onChange={(e) => setKnowledgeDocumentSample(e.target.value)} spellCheck />
                        <div className={styles.helper}>This sample text is sent when you click Test API on the ingestion connector.</div>
                      </div>
                    ),
                  },
                )}
                {renderConnectorFields(
                  'RAG Search API',
                  'This connector receives the current user input and should return the retrieved answer, snippets, or supporting documents for the knowledge layer.',
                  'connector:knowledge:search',
                  draft.knowledgeApi.search,
                  (patch) => updateKnowledgeConnector('search', patch),
                  () => applyCurlToKnowledge('search'),
                  {
                    curlStatusKey: 'curl:knowledge:search',
                  },
                )}
              </>,
              draft.knowledgeApi.search.enabled ? 'search on' : undefined,
            )}

            {renderActualSection(
              'tools',
              ACTUAL_LAYER_COPY.tools.title,
              ACTUAL_LAYER_COPY.tools.description,
              <>
                <div className={styles.actualSectionToolbar}>
                  <button type="button" className={styles.secondaryBtn} onClick={addToolApi}>
                    Add Tool API
                  </button>
                </div>
                <div className={styles.toolApiList}>
                  {draft.toolApis.map((toolApi, index) => (
                    <div key={toolApi.id} className={styles.toolApiShell}>
                      {renderConnectorFields(
                        toolApi.name || `Tool API ${index + 1}`,
                        'Each enabled tool API contributes to the combined tool-definition layer.',
                        `connector:tool:${toolApi.id}`,
                        toolApi,
                        (patch) => updateToolApi(toolApi.id, patch as Partial<ToolApiConfig>),
                        () => applyCurlToToolApi(toolApi.id),
                        {
                          curlStatusKey: `curl:tool:${toolApi.id}`,
                          beforeGrid: (
                            <div className={styles.field}>
                              <label className={styles.label}>Tool API Name</label>
                              <input className={styles.input} value={toolApi.name} onChange={(e) => updateToolApi(toolApi.id, { name: e.target.value })} placeholder={`Tool API ${index + 1}`} />
                            </div>
                          ),
                          footerActions: draft.toolApis.length > 1 ? (
                            <button type="button" className={styles.removeSubCardBtn} onClick={() => removeToolApi(toolApi.id)}>
                              Remove
                            </button>
                          ) : undefined,
                        },
                      )}
                    </div>
                  ))}
                </div>
              </>,
              `${draft.toolApis.filter((toolApi) => toolApi.enabled).length} enabled`,
            )}

            {renderActualSection(
              'modelResponse',
              'Model Response API',
              'Send the current user input to a dedicated response-generation API and publish the reply in the Model Response panel. If disabled, the same configured LLM can be used instead.',
              <>
                {renderConnectorFields(
                  'Model Response API',
                  'Use this when your app already has its own response-generation endpoint and you want this playground to display that output directly.',
                  'connector:model-response',
                  draft.modelResponseApi,
                  (patch) => updateModelResponseApi(patch),
                  applyCurlToModelResponse,
                  {
                    curlStatusKey: 'curl:model-response',
                  },
                )}
                <div className={styles.toggleRow}>
                  <div>
                    <div className={styles.toggleLabel}>Fallback to same LLM</div>
                    <div className={styles.toggleHelper}>If the model response API is disabled, use the configured provider/model to generate the response shown in the Model Response section.</div>
                  </div>
                  <label className={styles.toggle}>
                    <input type="checkbox" checked={draft.modelResponseApi.useSameLlmWhenDisabled} onChange={(e) => updateModelResponseApi({ useSameLlmWhenDisabled: e.target.checked })} />
                    <span className={`${styles.toggleTrack}${draft.modelResponseApi.useSameLlmWhenDisabled ? ` ${styles.toggleOn}` : ''}`}>
                      <span className={styles.toggleThumb} />
                    </span>
                  </label>
                </div>
              </>,
              draft.modelResponseApi.enabled ? 'live' : undefined,
            )}
          </div>
        </div>
      )}
    </>
  )

  const renderPrdSection = () => (
    <div className={styles.section}>
      <div className={styles.prdBlock}>
        <div className={styles.prdHeader}>
          <div>
            <div className={styles.prdTitleRow}>
              <span className={styles.prdTitle}>PRD</span>
              <button className={styles.infoBtn} type="button" onClick={() => setIsPrdInfoOpen(true)} aria-label="What is a PRD?" title="What is a PRD?">
                i
              </button>
            </div>
            <div className={styles.prdApplicability}>Applicable for Manual and Actual Data.</div>
          </div>
          {prdApplicable && (
            <>
              <input ref={fileInputRef} type="file" className={styles.fileInput} accept=".txt,.md,.markdown,.json,.csv,.prd" onChange={(e) => handlePrdUpload(e.target.files?.[0])} />
              <button type="button" className={styles.uploadBtn} onClick={() => fileInputRef.current?.click()} disabled={!canEditPrd} title="Upload PRD" aria-label="Upload PRD">
                +
              </button>
            </>
          )}
        </div>

        {!prdApplicable ? (
          <div className={styles.prdEmptyState}>PRD setup is available when Configure Data is set to Manual or Actual Data.</div>
        ) : (
          <>
            {!canEditPrd && (
              <div className={styles.lockedNotice}>
                <span>Test the selected LLM to unlock PRD-assisted editing, or continue without the test if you only need local configuration.</span>
                <button type="button" className={styles.unlockBtn} onClick={() => setAllowPrdEditBeforeTest(true)}>
                  Edit PRD Anyway
                </button>
              </div>
            )}

            <textarea className={styles.prdInput} value={draft.prd} onChange={(e) => update('prd', e.target.value)} placeholder="Paste or write the product requirements document for the evaluation context." spellCheck disabled={!canEditPrd} />

            <div className={styles.parameterToolbar}>
              <button
                type="button"
                className={styles.processBtn}
                onClick={() => void handleProcessPrd()}
                disabled={!canEditPrd || isProcessingPrd || !draft.prd.trim()}
              >
                {isProcessingPrd ? 'Processing PRD...' : 'Process PRD'}
              </button>
            </div>
            {renderStatus('prd:process')}

            <div className={styles.parameterHeader}>
              <div>
                <div className={styles.parameterTitle}>Evaluation Parameters</div>
                <div className={styles.parameterSubtitle}>Add, remove, rename, or describe the dimensions you want the evaluator to score.</div>
              </div>
              <button type="button" className={styles.iconBtn} onClick={addParameter} disabled={!canEditPrd} aria-label="Add parameter" title="Add parameter">
                +
              </button>
            </div>

            {draft.prdParameters.length === 0 ? (
              <div className={styles.prdEmptyState}>No evaluation parameters yet. Add at least one dimension so the evaluator knows what to score.</div>
            ) : (
              <div className={styles.parameterList}>
                {draft.prdParameters.map((parameter, index) => {
                  const isEditing = Boolean(editingParameters[index]) && canEditPrd
                  return (
                    <div key={`${parameter.id}-${index}`} className={styles.parameterCard}>
                      <div className={styles.parameterCardHeader}>
                        <span className={styles.parameterCardTitle}>Parameter {index + 1}</span>
                        <div className={styles.parameterActions}>
                          <button
                            type="button"
                            className={`${styles.iconBtn}${isEditing ? ` ${styles.iconBtnActive}` : ''}`}
                            onClick={() => toggleParameterEditing(index)}
                            disabled={!canEditPrd}
                            aria-label={isEditing ? 'Close parameter editor' : 'Edit parameter'}
                            title={isEditing ? 'Close parameter editor' : 'Edit parameter'}
                          >
                            {'\u270E'}
                          </button>
                          <button
                            type="button"
                            className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                            onClick={() => removeParameter(index)}
                            disabled={!canEditPrd}
                            aria-label="Remove parameter"
                            title="Remove parameter"
                          >
                            -
                          </button>
                        </div>
                      </div>

                      {isEditing ? (
                        <div className={styles.parameterEditor}>
                          <div className={styles.field}>
                            <label className={styles.label}>Label</label>
                            <input className={styles.parameterInput} value={parameter.label} placeholder="Response Accuracy" onChange={(e) => updateParameter(index, { label: e.target.value })} />
                          </div>

                          <div className={styles.field}>
                            <label className={styles.label}>Identifier</label>
                            <input className={styles.parameterInput} value={parameter.id} placeholder="response-accuracy" onChange={(e) => updateParameter(index, { id: e.target.value })} spellCheck={false} />
                          </div>

                          <div className={styles.field}>
                            <label className={styles.label}>Description</label>
                            <textarea className={styles.parameterDescription} value={parameter.description} placeholder="Explain what a strong answer should demonstrate for this dimension." onChange={(e) => updateParameter(index, { description: e.target.value })} spellCheck />
                          </div>
                        </div>
                      ) : (
                        <div className={styles.parameterSummary}>
                          <div className={styles.field}>
                            <label className={styles.label}>Identifier</label>
                            <div className={`${styles.readonlyValue} ${styles.readonlyValueMono}`}>{parameter.id || 'No identifier set'}</div>
                          </div>

                          <div className={styles.field}>
                            <label className={styles.label}>Description</label>
                            <div className={styles.readonlyValue}>{parameter.description || 'No description set'}</div>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )

  const renderDbSection = () => (
    <div className={styles.section}>
      <div className={styles.sectionLabel}>Configure DB</div>
      <div className={styles.docsCard}>
        <div className={styles.docsTitle}>PostgreSQL Setup</div>
        <div className={styles.docsText}>
          Use either a full connection string or enter the fields separately. The backend uses local PostgreSQL CLI tools to test the connection and can create the database when <strong>DB already exists</strong> is turned off.
        </div>
      </div>

      <div className={styles.field}>
        <label className={styles.label}>Connection String</label>
        <textarea
          className={styles.codeArea}
          value={draft.databaseConfig.connectionString}
          onChange={(e) => updateDatabaseConfig({ connectionString: e.target.value })}
          placeholder="DATABASE_URL=postgresql://postgres:Bharat%40123@localhost:5433/createDB or postgresql://postgres:password@localhost:5433/createDB"
          spellCheck={false}
        />
      </div>

      <div className={styles.twoCol}>
        <div className={styles.field}>
          <label className={styles.label}>Database Port</label>
          <input className={styles.input} value={draft.databaseConfig.databasePort} onChange={(e) => updateDatabaseConfig({ databasePort: e.target.value })} spellCheck={false} />
        </div>
        <div className={styles.field}>
          <label className={styles.label}>Database Superuser</label>
          <input className={styles.input} value={draft.databaseConfig.databaseSuperuser} onChange={(e) => updateDatabaseConfig({ databaseSuperuser: e.target.value })} spellCheck={false} />
        </div>
      </div>

      <div className={styles.twoCol}>
        <div className={styles.field}>
          <label className={styles.label}>Password</label>
          <input type="password" className={styles.input} value={draft.databaseConfig.password} onChange={(e) => updateDatabaseConfig({ password: e.target.value })} spellCheck={false} />
        </div>
        <div className={styles.field}>
          <label className={styles.label}>DB Name</label>
          <input className={styles.input} value={draft.databaseConfig.dbName} onChange={(e) => updateDatabaseConfig({ dbName: e.target.value })} spellCheck={false} />
        </div>
      </div>

      <div className={styles.toggleRow}>
        <div>
          <div className={styles.toggleLabel}>DB already exists</div>
          <div className={styles.toggleHelper}>Turn this off to let the backend create the target database if it is missing.</div>
        </div>
        <label className={styles.toggle}>
          <input type="checkbox" checked={draft.databaseConfig.dbAlreadyExists} onChange={(e) => updateDatabaseConfig({ dbAlreadyExists: e.target.checked })} />
          <span className={`${styles.toggleTrack}${draft.databaseConfig.dbAlreadyExists ? ` ${styles.toggleOn}` : ''}`}>
            <span className={styles.toggleThumb} />
          </span>
        </label>
      </div>

      <div className={styles.integrationActions}>
        <button type="button" className={styles.testBtn} disabled={loadingByKey['db:test']} onClick={() => void testDatabase()}>
          {loadingByKey['db:test'] ? (draft.databaseConfig.dbAlreadyExists ? 'Testing...' : 'Creating...') : (draft.databaseConfig.dbAlreadyExists ? 'Test DB' : 'Create / Connect DB')}
        </button>
      </div>
      {renderStatus('db:test')}
    </div>
  )

  return (
    <>
      <Modal isOpen={isOpen} onClose={onClose} width="840px">
        <div className={styles.header}>
          <div>
            <div className={styles.titleTabs} role="tablist" aria-label="Configuration sections">
              <button type="button" role="tab" aria-selected={activeSection === 'llm'} className={`${styles.titleTab}${activeSection === 'llm' ? ` ${styles.titleTabActive}` : ''}`} onClick={() => setActiveSection('llm')}>
                Configure LLM
              </button>
              <button type="button" role="tab" aria-selected={activeSection === 'data'} className={`${styles.titleTab}${activeSection === 'data' ? ` ${styles.titleTabActive}` : ''}`} onClick={() => setActiveSection('data')}>
                Configure Data
              </button>
              <button type="button" role="tab" aria-selected={activeSection === 'prd'} className={`${styles.titleTab}${activeSection === 'prd' ? ` ${styles.titleTabActive}` : ''}`} onClick={() => setActiveSection('prd')}>
                PRD
              </button>
              <button type="button" role="tab" aria-selected={activeSection === 'db'} className={`${styles.titleTab}${activeSection === 'db' ? ` ${styles.titleTabActive}` : ''}`} onClick={() => setActiveSection('db')}>
                Configure DB
              </button>
            </div>
            <div className={styles.subtitle}>
              {activeSection === 'llm' && 'Set API keys, choose a provider, and verify the selected model.'}
              {activeSection === 'data' && 'Configure context-layer APIs, curl-based integrations, and a dedicated model response endpoint.'}
              {activeSection === 'prd' && 'Define product requirements and the score dimensions for Manual or Actual Data.'}
              {activeSection === 'db' && 'Configure PostgreSQL connectivity and optionally create the target database from here.'}
            </div>
          </div>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close">x</button>
        </div>

        <div className={styles.body}>
          {activeSection === 'llm' && renderLlmSection()}
          {activeSection === 'data' && renderDataSection()}
          {activeSection === 'prd' && renderPrdSection()}
          {activeSection === 'db' && renderDbSection()}
        </div>

        <div className={styles.footer}>
          <button className={styles.cancelBtn} onClick={onClose} type="button">Cancel</button>
          <button className={styles.saveBtn} onClick={handleSave} type="button">Save Settings</button>
        </div>
      </Modal>

      <Modal isOpen={isPrdInfoOpen} onClose={() => setIsPrdInfoOpen(false)} width="720px">
        <div className={styles.prdModalHeader}>
          <div>
            <div className={styles.prdModalTitle}>Product Requirements Document (PRD)</div>
            <div className={styles.prdModalSubtitle}>Functional context for Manual, Actual Data, and mock setup review.</div>
          </div>
          <button className={styles.closeBtn} onClick={() => setIsPrdInfoOpen(false)} aria-label="Close">x</button>
        </div>
        <div className={styles.prdModalBody}>
          <p>
            A Product Requirements Document (PRD) is a foundational document created by product managers to define the
            purpose, features, functionality, and behavior of a product or feature. It acts as a single source of truth
            for engineering, design, and stakeholders, detailing the what and why behind the build.
          </p>
          <div className={styles.prdModalGrid}>
            <section>
              <h4>Key Components</h4>
              <ul>
                <li><strong>Purpose & Goal:</strong> problem, why, and success metrics.</li>
                <li><strong>Target Audience:</strong> user personas who benefit.</li>
                <li><strong>Features & Functionality:</strong> requirements, user stories, and acceptance criteria.</li>
                <li><strong>User Experience:</strong> wireframes, user flows, or design notes.</li>
              </ul>
            </section>
            <section>
              <h4>Usage Examples</h4>
              <ul>
                <li><strong>Aligning Teams:</strong> shared scope for engineering, design, and marketing.</li>
                <li><strong>Prioritization:</strong> MoSCoW or MVP scoping.</li>
                <li><strong>Development Guide:</strong> reference for builders and testers.</li>
                <li><strong>Scope Management:</strong> baseline to reduce scope creep.</li>
              </ul>
            </section>
          </div>
        </div>
        <div className={styles.prdModalFooter}>
          <button className={styles.cancelBtn} onClick={() => setIsPrdInfoOpen(false)} type="button">Close</button>
        </div>
      </Modal>
    </>
  )
}
