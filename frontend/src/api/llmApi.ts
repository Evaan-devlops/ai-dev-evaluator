import { post } from './client'
import type { LLMProvider } from '../store/llmConfigStore'

export interface LLMTestBody {
  provider: LLMProvider
  model: string
  api_key: string
}

export interface LLMTestResponse {
  ok: boolean
  provider: LLMProvider
  model: string
  message: string
}

export interface LLMGenerateBody {
  provider: LLMProvider
  model: string
  api_key: string
  input: string
  system_instruction?: string
  max_output_tokens?: number
  temperature?: number
}

export interface LLMGenerateResponse {
  ok: boolean
  provider: LLMProvider
  model: string
  output_text: string
}

export const llmApi = {
  test(body: LLMTestBody): Promise<LLMTestResponse> {
    return post<LLMTestResponse>('/api/llm/test', body, 25_000)
  },

  generate(body: LLMGenerateBody): Promise<LLMGenerateResponse> {
    return post<LLMGenerateResponse>('/api/llm/generate', body, 60_000)
  },
}
