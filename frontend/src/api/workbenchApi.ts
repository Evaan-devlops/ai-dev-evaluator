import { get, post, del } from './client'
import type {
  ApiContextMeta,
  ApiEvaluateResponse,
  ApiAssembleResponse,
  ApiHistoryRow,
  LayerType,
} from '../types'

const BASE = '/api/context'

export interface AssembleBody {
  provider: string
  active_layers: LayerType[]
}

export interface EvaluateBody {
  provider: string
  active_layers: LayerType[]
  run_id?: number
}

export const workbenchApi = {
  /** GET /api/context/meta — all layer definitions + token counts + warnings */
  getMeta(): Promise<ApiContextMeta> {
    return get<ApiContextMeta>(`${BASE}/meta`)
  },

  /** GET /api/context/history — compact run history list */
  getHistory(): Promise<ApiHistoryRow[]> {
    return get<ApiHistoryRow[]>(`${BASE}/history`)
  },

  /** GET /api/context/history/:runId — full run result by id */
  getRunDetails(runId: number): Promise<ApiEvaluateResponse> {
    return get<ApiEvaluateResponse>(`${BASE}/history/${runId}`)
  },

  /** POST /api/context/assemble — assemble prompt from active layer keys */
  assemble(active_layers: LayerType[], provider = 'mock-provider'): Promise<ApiAssembleResponse> {
    const body: AssembleBody = { provider, active_layers }
    return post<ApiAssembleResponse>(`${BASE}/assemble`, body)
  },

  /** POST /api/context/evaluate — run evaluation, get score + response */
  evaluate(active_layers: LayerType[], provider = 'mock-provider', run_id?: number): Promise<ApiEvaluateResponse> {
    const body: EvaluateBody = { provider, active_layers, run_id }
    return post<ApiEvaluateResponse>(`${BASE}/evaluate`, body)
  },

  /** DELETE /api/context/history — reset all runs to seeded state */
  resetHistory(): Promise<{ message: string; cleared: boolean }> {
    return del(`${BASE}/history`)
  },
}
