const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const DEFAULT_TIMEOUT_MS = 30_000

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// Hook point for future auth header injection
function getAuthHeaders(): Record<string, string> {
  return {}
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
  }

  const init: RequestInit = {
    method,
    headers,
    signal: controller.signal,
  }

  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }

  let response: Response

  try {
    response = await fetch(`${BASE_URL}${path}`, init)
  } catch (err) {
    if ((err as Error).name === 'AbortError') {
      throw new ApiError(408, `Request timed out after ${timeoutMs}ms`)
    }
    throw new ApiError(0, `Network error: ${(err as Error).message}`)
  } finally {
    clearTimeout(timer)
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const json = await response.json() as { detail?: string }
      if (json.detail) detail = String(json.detail)
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, detail)
  }

  return response.json() as Promise<T>
}

export function get<T>(path: string, timeoutMs?: number): Promise<T> {
  return request<T>('GET', path, undefined, timeoutMs)
}

export function post<T>(path: string, body: unknown, timeoutMs?: number): Promise<T> {
  return request<T>('POST', path, body, timeoutMs)
}

export function del<T>(path: string, timeoutMs?: number): Promise<T> {
  return request<T>('DELETE', path, undefined, timeoutMs)
}
