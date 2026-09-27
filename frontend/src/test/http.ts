/** Test helpers: a mocked `fetch` that answers with enveloped JSON. No real backend. */
import { vi } from 'vitest'

export interface MockReply {
  status?: number
  body?: unknown
  headers?: Record<string, string>
}

export function jsonResponse({ status = 200, body = null, headers = {} }: MockReply): Response {
  return new Response(body === null ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  })
}

export function ok<T>(data: T, status = 200): MockReply {
  return { status, body: { success: true, message: 'Operation completed successfully.', data } }
}

export function fail(status: number, message: string, errors: unknown, headers = {}): MockReply {
  return { status, body: { success: false, message, errors }, headers }
}

export type Handler = (url: string, init: RequestInit) => MockReply | Promise<MockReply>

/** Installs a fetch mock; returns the spy so tests can inspect calls. */
export function mockFetch(handler: Handler) {
  const spy = vi.fn(async (input: RequestInfo | URL, init: RequestInit) => {
    const url = typeof input === 'string' ? input : input.toString()
    return jsonResponse(await handler(url, init))
  })
  vi.stubGlobal('fetch', spy)
  return spy
}

export function authHeader(init: RequestInit | undefined): string | undefined {
  return (init?.headers as Record<string, string> | undefined)?.Authorization
}

export const API = 'https://api.test.local'
