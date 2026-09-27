/**
 * The one Flash API client (ADR-008, api-contracts.md §1).
 *
 * - base URL from `VITE_API_BASE_URL`
 * - unwraps `{ success, message, data | errors }`
 * - sends `Authorization: Bearer <access>` (no cookies: `credentials: 'omit'`)
 * - on 401 from a Bearer call: one shared refresh, then one retry; a rejected refresh
 *   calls `onAuthFailure` (logout + redirect to /login)
 * - every failure is an `ApiError` (status, kind, code, fieldErrors, retryAfter)
 */
import { apiUrl } from '@/config/env'
import { ApiError, parseRetryAfter, splitErrors } from './errors'

export interface AuthHooks {
  /** Current access token (memory only). */
  getAccessToken(): string | null
  /**
   * Obtain a new access token with the stored refresh token.
   * Resolves to the new token, or `null` when the refresh was rejected / impossible.
   * Rejects with an `ApiError` when the refresh endpoint could not be reached.
   */
  refreshAccessToken(): Promise<string | null>
  /** Called once when the session cannot be recovered (refresh rejected). */
  onAuthFailure(): void
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestOptions {
  method?: HttpMethod
  body?: unknown
  /** Bearer call (default true). Public endpoints (login, refresh, status) pass `false`. */
  auth?: boolean
  headers?: Record<string, string>
  signal?: AbortSignal
}

let hooks: AuthHooks | null = null
let refreshInFlight: Promise<string | null> | null = null

export function setAuthHooks(next: AuthHooks | null): void {
  hooks = next
  refreshInFlight = null
}

/** Concurrent 401s share this single refresh promise. */
function refreshOnce(active: AuthHooks): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = active.refreshAccessToken().finally(() => {
      refreshInFlight = null
    })
  }
  return refreshInFlight
}

interface RawResponse {
  status: number
  ok: boolean
  body: unknown
  retryAfter: number | null
}

async function send(
  path: string,
  options: RequestOptions,
  token: string | null,
): Promise<RawResponse> {
  const headers: Record<string, string> = { Accept: 'application/json', ...options.headers }
  let body: string | undefined
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body)
  }
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(apiUrl(path), {
      method: options.method ?? 'GET',
      headers,
      body,
      credentials: 'omit',
      mode: 'cors',
      signal: options.signal,
    })
  } catch {
    throw new ApiError({ status: 0, kind: 'network', message: 'Network error.' })
  }

  let parsed: unknown = null
  if (response.status !== 204) {
    const text = await response.text().catch(() => '')
    if (text) {
      try {
        parsed = JSON.parse(text)
      } catch {
        parsed = null
      }
    }
  }
  return {
    status: response.status,
    ok: response.ok,
    body: parsed,
    retryAfter: parseRetryAfter(response.headers.get('Retry-After')),
  }
}

function isEnvelope(
  value: unknown,
): value is { success: boolean; message?: unknown; data?: unknown; errors?: unknown } {
  return (
    !!value &&
    typeof value === 'object' &&
    typeof (value as { success?: unknown }).success === 'boolean'
  )
}

function toError(raw: RawResponse): ApiError {
  const envelope = isEnvelope(raw.body) ? raw.body : null
  const { code, fieldErrors } = splitErrors(envelope?.errors)
  const message =
    typeof envelope?.message === 'string' && envelope.message
      ? envelope.message
      : `Request failed (${raw.status}).`
  return new ApiError({
    status: raw.status,
    message,
    code,
    fieldErrors,
    retryAfter: raw.retryAfter,
  })
}

function unwrap<T>(raw: RawResponse): T {
  if (!raw.ok) throw toError(raw)
  if (isEnvelope(raw.body)) {
    if (!raw.body.success) throw toError(raw)
    return raw.body.data as T
  }
  // Raw (non-enveloped) responses, e.g. 204 or OpenAPI; returned as-is.
  return raw.body as T
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const useAuth = options.auth !== false
  const active = useAuth ? hooks : null
  const sentToken = active?.getAccessToken() ?? null

  const first = await send(path, options, sentToken)
  if (first.status !== 401 || !active) return unwrap<T>(first)

  // 401 on a Bearer call. If another request already refreshed, just retry with the new token.
  let token = active.getAccessToken()
  if (!token || token === sentToken) {
    token = await refreshOnce(active)
    if (!token) {
      active.onAuthFailure()
      throw toError(first)
    }
  }

  const retry = await send(path, options, token)
  if (retry.status === 401) {
    active.onAuthFailure()
  }
  return unwrap<T>(retry)
}
