/**
 * Typed API errors (api-contracts.md §1.2, §1.4, § Error codes).
 * Clients branch on `kind` / `code`, never on `message`.
 */
export type ApiErrorKind =
  | 'validation' // 400
  | 'unauthorized' // 401
  | 'forbidden' // 403
  | 'not_found' // 404
  | 'conflict' // 409
  | 'rate_limited' // 429
  | 'server' // 5xx
  | 'network' // no HTTP response (offline, DNS, CORS, aborted)
  | 'unknown' // any other status or an unreadable body

export type FieldErrors = Record<string, string[]>

export interface ApiErrorInit {
  status: number
  message: string
  code?: string | null
  fieldErrors?: FieldErrors
  retryAfter?: number | null
  kind?: ApiErrorKind
}

export class ApiError extends Error {
  readonly status: number
  readonly kind: ApiErrorKind
  /** `errors.code` from the envelope, e.g. `INVALID_CREDENTIALS`, `THROTTLED`. */
  readonly code: string | null
  /** Field errors from `errors.<field>` (includes `non_field_errors`; excludes `code`). */
  readonly fieldErrors: FieldErrors
  /** Seconds from the `Retry-After` header (429), when the browser can read it. */
  readonly retryAfter: number | null

  constructor(init: ApiErrorInit) {
    super(init.message)
    this.name = 'ApiError'
    this.status = init.status
    this.kind = init.kind ?? kindForStatus(init.status)
    this.code = init.code ?? null
    this.fieldErrors = init.fieldErrors ?? {}
    this.retryAfter = init.retryAfter ?? null
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError
}

export function kindForStatus(status: number): ApiErrorKind {
  if (status === 0) return 'network'
  if (status === 400) return 'validation'
  if (status === 401) return 'unauthorized'
  if (status === 403) return 'forbidden'
  if (status === 404) return 'not_found'
  if (status === 409) return 'conflict'
  if (status === 429) return 'rate_limited'
  if (status >= 500) return 'server'
  return 'unknown'
}

/** `Retry-After` is either delta-seconds or an HTTP date. Returns whole seconds ≥ 0. */
export function parseRetryAfter(header: string | null, now: number = Date.now()): number | null {
  if (header === null) return null
  const value = header.trim()
  if (value === '') return null
  if (/^\d+$/.test(value)) return Number.parseInt(value, 10)
  const date = Date.parse(value)
  if (Number.isNaN(date)) return null
  return Math.max(0, Math.ceil((date - now) / 1000))
}

/** Splits the envelope `errors` object into `code` and string-array field errors. */
export function splitErrors(errors: unknown): { code: string | null; fieldErrors: FieldErrors } {
  const fieldErrors: FieldErrors = {}
  let code: string | null = null
  if (!errors || typeof errors !== 'object' || Array.isArray(errors)) {
    return { code, fieldErrors }
  }
  for (const [key, value] of Object.entries(errors as Record<string, unknown>)) {
    if (key === 'code') {
      code = typeof value === 'string' ? value : null
    } else if (Array.isArray(value)) {
      fieldErrors[key] = value.map((item) => String(item))
    } else if (typeof value === 'string') {
      fieldErrors[key] = [value]
    }
    // Nested objects (e.g. readiness `checks`) are not field errors; ignored here.
  }
  return { code, fieldErrors }
}
