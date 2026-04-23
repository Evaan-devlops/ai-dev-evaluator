import { post } from './client'
import type {
  ActualDataIntegration,
  DatabaseConfig,
  EvaluationParameter,
  KnowledgeApiConfig,
  LLMConfig,
  ToolApiConfig,
} from '../store/llmConfigStore'
import type { ContextLayer } from '../types'

interface ProviderConfigBody {
  provider: LLMConfig['provider']
  model: string
  api_key: string
  temperature: number
  max_output_tokens: number
}

export interface ProcessPrdResponse {
  ok: boolean
  parameters: EvaluationParameter[]
  rationale: string
}

export interface EvaluateModelResponseResponse {
  ok: boolean
  score_breakdown: Record<string, number>
  quality_score: number
  score_max: number
  insight: string
  suggestions: string[]
  evaluation_provider: string
  reference_response: string
  selected_layers: Array<ContextLayer['id']>
  used_context: Record<string, string>
  latency_ms: number
}

function mapConnector(connector: ActualDataIntegration | ToolApiConfig | KnowledgeApiConfig['ingestion'] | KnowledgeApiConfig['search']) {
  return {
    id: 'id' in connector ? connector.id : ('layerId' in connector ? connector.layerId : ''),
    name: 'name' in connector ? connector.name : ('layerId' in connector ? connector.layerId : ''),
    enabled: connector.enabled,
    endpoint: connector.endpoint,
    method: connector.method,
    prompt_param: connector.promptParam,
    headers: connector.headers,
    body_template: connector.bodyTemplate,
    response_path: connector.responsePath,
    content_template: connector.contentTemplate,
    fallback_content: connector.fallbackContent,
    curl_command: connector.curlCommand,
  }
}

function mapDatabase(config: DatabaseConfig) {
  return {
    connection_string: config.connectionString,
    database_port: config.databasePort,
    database_superuser: config.databaseSuperuser,
    password: config.password,
    db_name: config.dbName,
    db_already_exists: config.dbAlreadyExists,
  }
}

export const evaluationApi = {
  processPrd(
    prd: string,
    parameters: EvaluationParameter[],
    providerConfig: ProviderConfigBody,
  ): Promise<ProcessPrdResponse> {
    return post<ProcessPrdResponse>(
      '/api/evaluation/process-prd',
      {
        prd,
        existing_parameters: parameters,
        provider_config: providerConfig,
      },
      90_000,
    )
  },

  evaluateModelResponse(
    config: LLMConfig,
    layers: ContextLayer[],
    userPrompt: string,
    modelResponse: string,
    providerConfig: ProviderConfigBody,
  ): Promise<EvaluateModelResponseResponse> {
    return post<EvaluateModelResponseResponse>(
      '/api/evaluation/evaluate-model-response',
      {
        prd: config.prd,
        evaluation_parameters: config.prdParameters,
        user_prompt: userPrompt,
        model_response: modelResponse,
        provider_config: providerConfig,
        data_source: config.dataSource,
        manual_layers: layers.map((layer) => ({
          id: layer.id,
          enabled: layer.enabled,
          content: layer.content,
        })),
        actual_data_integrations: config.actualDataIntegrations.map(mapConnector),
        knowledge_api: {
          ingestion: mapConnector(config.knowledgeApi.ingestion),
          search: mapConnector(config.knowledgeApi.search),
        },
        tool_apis: config.toolApis.map(mapConnector),
        database_config: mapDatabase(config.databaseConfig),
        system_prompt_text: config.systemPromptText ?? '',
        rag_service_url: config.ragServiceUrl ?? '',
        rag_document_id: config.ragDocumentId ?? '',
      },
      180_000,
    )
  },
}
