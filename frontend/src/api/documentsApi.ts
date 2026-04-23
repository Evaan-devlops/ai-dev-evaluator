import type { LLMConfig } from '../store/llmConfigStore'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export interface IngestResult {
  ok: boolean
  message: string
  document_id?: string
  ingestion_api_status?: string
  rag_service_status?: string
}

export async function uploadDocument(file: File, config: LLMConfig): Promise<IngestResult> {
  const formData = new FormData()
  formData.append('file', file, file.name)

  const ingestionEndpoint = config.knowledgeApi.ingestion.enabled
    ? config.knowledgeApi.ingestion.endpoint.trim()
    : ''
  const ingestionHeaders = ingestionEndpoint ? config.knowledgeApi.ingestion.headers.trim() : ''
  const ragUrl = config.ragServiceUrl?.trim() ?? ''

  formData.append('ingestion_endpoint', ingestionEndpoint)
  formData.append('ingestion_headers', ingestionHeaders)
  formData.append('rag_service_url', ragUrl)

  const response = await fetch(`${BASE_URL}/api/documents/ingest`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Upload failed (${response.status}): ${text.slice(0, 200)}`)
  }

  return response.json() as Promise<IngestResult>
}

/**
 * Push the configured DB settings to the myRAG service so it uses the same database.
 * Silently ignores errors — myRAG may not be running.
 */
export async function syncDbConfigToRag(config: LLMConfig): Promise<void> {
  const ragUrl = config.ragServiceUrl?.trim()
  if (!ragUrl) return

  const db = config.databaseConfig
  const body = {
    connection_string: db.connectionString.trim(),
    database_port: db.databasePort.trim(),
    database_superuser: db.databaseSuperuser.trim(),
    password: db.password,
    db_name: db.dbName.trim(),
  }

  try {
    await fetch(`${ragUrl.replace(/\/$/, '')}/api/v1/config/db`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    // myRAG service may not be running; silently skip
  }
}
