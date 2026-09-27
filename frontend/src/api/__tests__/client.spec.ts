import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { apiRequest, setAuthHooks, type AuthHooks } from '../client'
import { ApiError } from '../errors'
import { API, authHeader, fail, mockFetch, ok } from '@/test/http'

function makeHooks(initial: string | null, refreshResult: () => Promise<string | null>) {
  let token = initial
  const hooks = {
    getAccessToken: vi.fn(() => token),
    refreshAccessToken: vi.fn(async () => {
      const next = await refreshResult()
      if (next) token = next
      return next
    }),
    onAuthFailure: vi.fn(),
  } satisfies AuthHooks
  setAuthHooks(hooks)
  return hooks
}

beforeEach(() => setAuthHooks(null))
afterEach(() => vi.unstubAllGlobals())

describe('apiRequest — envelope and transport', () => {
  it('unwraps data from the success envelope and uses the configured base URL', async () => {
    const spy = mockFetch(() => ok({ status: 'ok' }))
    await expect(apiRequest('/api/status/', { auth: false })).resolves.toEqual({ status: 'ok' })
    const [url, init] = spy.mock.calls[0]!
    expect(url).toBe(`${API}/api/status/`)
    expect(init.credentials).toBe('omit')
    expect(authHeader(init)).toBeUndefined()
  })

  it('sends JSON bodies and the Bearer token', async () => {
    makeHooks('access-1', async () => null)
    const spy = mockFetch(() => ok({ id: 1 }))
    await apiRequest('/api/x/', { method: 'POST', body: { a: 1 } })
    const init = spy.mock.calls[0]![1]
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{"a":1}')
    expect(authHeader(init)).toBe('Bearer access-1')
  })

  it('treats success:false in a 200 as an error', async () => {
    mockFetch(() => ({ status: 200, body: { success: false, message: 'Nope', errors: {} } }))
    await expect(apiRequest('/api/x/', { auth: false })).rejects.toMatchObject({ message: 'Nope' })
  })
})

describe('apiRequest — error mapping', () => {
  it('maps 400 field errors', async () => {
    mockFetch(() => fail(400, 'Validation failed.', { username: ['This field is required.'] }))
    const error = (await apiRequest('/api/x/', { auth: false }).catch((e) => e)) as ApiError
    expect(error).toBeInstanceOf(ApiError)
    expect(error.kind).toBe('validation')
    expect(error.code).toBeNull()
    expect(error.fieldErrors).toEqual({ username: ['This field is required.'] })
  })

  it.each([
    [403, 'PERMISSION_DENIED', 'forbidden'],
    [404, 'NOT_FOUND', 'not_found'],
    [500, 'SERVER_ERROR', 'server'],
  ])('maps %i %s', async (status, code, kind) => {
    mockFetch(() => fail(status, 'msg', { code }))
    await expect(apiRequest('/api/x/', { auth: false })).rejects.toMatchObject({
      status,
      code,
      kind,
    })
  })

  it('maps 429 with Retry-After', async () => {
    mockFetch(() =>
      fail(429, 'Request rate limit exceeded.', { code: 'THROTTLED' }, { 'Retry-After': '42' }),
    )
    await expect(apiRequest('/api/status/', { auth: false })).rejects.toMatchObject({
      status: 429,
      kind: 'rate_limited',
      code: 'THROTTLED',
      retryAfter: 42,
      message: 'Request rate limit exceeded.',
    })
  })

  it('maps a network failure to kind "network"', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(apiRequest('/api/status/', { auth: false })).rejects.toMatchObject({
      status: 0,
      kind: 'network',
    })
  })

  it('handles a non-JSON error body', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('<html>bad gateway</html>', { status: 502 })),
    )
    await expect(apiRequest('/api/status/', { auth: false })).rejects.toMatchObject({
      status: 502,
      kind: 'server',
      code: null,
    })
  })
})

describe('apiRequest — 401 refresh', () => {
  it('refreshes once and retries with the new token', async () => {
    const hooks = makeHooks('old', async () => 'new')
    const spy = mockFetch((_url, init) =>
      authHeader(init) === 'Bearer new'
        ? ok({ id: 1 })
        : fail(401, 'Token is invalid or expired.', { code: 'TOKEN_INVALID' }),
    )
    await expect(apiRequest('/api/users/me/')).resolves.toEqual({ id: 1 })
    expect(hooks.refreshAccessToken).toHaveBeenCalledTimes(1)
    expect(spy).toHaveBeenCalledTimes(2)
    expect(hooks.onAuthFailure).not.toHaveBeenCalled()
  })

  it('shares one refresh between concurrent 401s', async () => {
    let release!: (value: string) => void
    const pending = new Promise<string>((resolve) => (release = resolve))
    const hooks = makeHooks('old', () => pending)
    mockFetch((_url, init) =>
      authHeader(init) === 'Bearer new'
        ? ok({ ok: true })
        : fail(401, 'x', { code: 'TOKEN_INVALID' }),
    )
    const calls = [apiRequest('/api/a/'), apiRequest('/api/b/'), apiRequest('/api/c/')]
    await vi.waitFor(() => expect(hooks.refreshAccessToken).toHaveBeenCalledTimes(1))
    release('new')
    await expect(Promise.all(calls)).resolves.toEqual([{ ok: true }, { ok: true }, { ok: true }])
    expect(hooks.refreshAccessToken).toHaveBeenCalledTimes(1)
  })

  it('calls onAuthFailure (logout) when the refresh is rejected', async () => {
    const hooks = makeHooks('old', async () => null)
    mockFetch(() => fail(401, 'Token is invalid or expired.', { code: 'TOKEN_INVALID' }))
    await expect(apiRequest('/api/users/me/')).rejects.toMatchObject({
      status: 401,
      code: 'TOKEN_INVALID',
    })
    expect(hooks.onAuthFailure).toHaveBeenCalledTimes(1)
  })

  it('calls onAuthFailure when the retried call is still 401', async () => {
    const hooks = makeHooks('old', async () => 'new')
    const spy = mockFetch(() => fail(401, 'x', { code: 'TOKEN_INVALID' }))
    await expect(apiRequest('/api/users/me/')).rejects.toMatchObject({ status: 401 })
    expect(spy).toHaveBeenCalledTimes(2)
    expect(hooks.refreshAccessToken).toHaveBeenCalledTimes(1)
    expect(hooks.onAuthFailure).toHaveBeenCalledTimes(1)
  })

  it('does not log out when the refresh endpoint is unreachable', async () => {
    const hooks = makeHooks('old', async () => {
      throw new ApiError({ status: 0, message: 'Network error.' })
    })
    mockFetch(() => fail(401, 'x', { code: 'TOKEN_INVALID' }))
    await expect(apiRequest('/api/users/me/')).rejects.toMatchObject({ kind: 'network' })
    expect(hooks.onAuthFailure).not.toHaveBeenCalled()
  })

  it('never refreshes for public calls (auth: false)', async () => {
    const hooks = makeHooks('old', async () => 'new')
    mockFetch(() => fail(401, 'Invalid username or password.', { code: 'INVALID_CREDENTIALS' }))
    await expect(
      apiRequest('/api/auth/token/', { method: 'POST', auth: false }),
    ).rejects.toMatchObject({
      code: 'INVALID_CREDENTIALS',
    })
    expect(hooks.refreshAccessToken).not.toHaveBeenCalled()
    expect(hooks.onAuthFailure).not.toHaveBeenCalled()
  })
})
