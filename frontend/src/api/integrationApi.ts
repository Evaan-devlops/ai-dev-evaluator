import { post } from './client'
import type { ApiConnectorConfig, DatabaseConfig } from '../store/llmConfigStore'

export interface ConnectorExecuteBody {
  prompt: string
  connector: ApiConnectorConfig
  timeout_ms?: number
}

export interface ConnectorExecuteResponse {
  ok: boolean
  status_code: number
  request_url: string
  request_method: string
  extracted_text: string
  raw_preview: string
}

export interface DatabaseConfigureResponse {
  ok: boolean
  normalized_connection_string: string
  message: string
}

export const integrationApi = {
  executeConnector(body: ConnectorExecuteBody): Promise<ConnectorExecuteResponse> {
    return post<ConnectorExecuteResponse>(
      '/api/integrations/http/execute',
      {
        prompt: body.prompt,
        timeout_ms: body.timeout_ms,
        connector: {
          endpoint: body.connector.endpoint,
          method: body.connector.method,
          prompt_param: body.connector.promptParam,
          headers: body.connector.headers,
          body_template: body.connector.bodyTemplate,
          response_path: body.connector.responsePath,
          content_template: body.connector.contentTemplate,
          fallback_content: body.connector.fallbackContent,
          curl_command: body.connector.curlCommand,
        },
      },
      45_000,
    )
  },

  configureDatabase(config: DatabaseConfig): Promise<DatabaseConfigureResponse> {
    return post<DatabaseConfigureResponse>(
      '/api/integrations/db/configure',
      {
        connection_string: config.connectionString,
        database_port: config.databasePort,
        database_superuser: config.databaseSuperuser,
        password: config.password,
        db_name: config.dbName,
        db_already_exists: config.dbAlreadyExists,
      },
      45_000,
    )
  },
}
