import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

import { REFRESH_TOKEN_KEY, useAuthStore } from '../auth'
import { setAuthHooks } from '@/api/client'
import { API, authHeader, fail, mockFetch, ok } from '@/test/http'

const ME = { id: 7, username: 'qa_driver', role: 'DRIVER', is_staff: false }

function bridge(auth: ReturnType<typeof useAuthStore>) {
  setAuthHooks({
    getAccessToken: () => auth.accessToken,
    refreshAccessToken: () => auth.refreshAccessToken(),
    onAuthFailure: () => auth.logout(),
  })
}

beforeEach(() => {
  localStorage.clear()
  setActivePinia(createPinia())
})
afterEach(() => {
  setAuthHooks(null)
  vi.unstubAllGlobals()
})

describe('auth store', () => {
  it('login stores access in memory, refresh in localStorage, and loads me', async () => {
    const spy = mockFetch((url, init) => {
      if (url === `${API}/api/auth/token/`) return ok({ access: 'acc', refresh: 'ref' })
      if (url === `${API}/api/users/me/` && authHeader(init) === 'Bearer acc') return ok(ME)
      return fail(401, 'x', { code: 'NOT_AUTHENTICATED' })
    })
    const auth = useAuthStore()
    bridge(auth)

    await expect(auth.login('qa_driver', 's3cret')).resolves.toEqual(ME)
    expect(auth.accessToken).toBe('acc')
    expect(auth.me).toEqual(ME)
    expect(auth.isAuthenticated).toBe(true)
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe('ref')
    // The access token is never persisted and the password is never stored.
    expect(JSON.stringify(localStorage)).not.toContain('acc"')
    expect(JSON.stringify(localStorage)).not.toContain('s3cret')
    const loginBody = JSON.parse(spy.mock.calls[0]![1].body as string)
    expect(loginBody).toEqual({ username: 'qa_driver', password: 's3cret' })
  })

  it('login propagates INVALID_CREDENTIALS and keeps no session', async () => {
    mockFetch(() => fail(401, 'Invalid username or password.', { code: 'INVALID_CREDENTIALS' }))
    const auth = useAuthStore()
    bridge(auth)
    await expect(auth.login('x', 'y')).rejects.toMatchObject({ code: 'INVALID_CREDENTIALS' })
    expect(auth.hasSession).toBe(false)
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull()
  })

  it('logout clears memory and localStorage', async () => {
    mockFetch((url) =>
      url.endsWith('/api/auth/token/') ? ok({ access: 'acc', refresh: 'ref' }) : ok(ME),
    )
    const auth = useAuthStore()
    bridge(auth)
    await auth.login('qa_driver', 'pw')
    auth.logout()
    expect(auth.accessToken).toBeNull()
    expect(auth.refreshToken).toBeNull()
    expect(auth.me).toBeNull()
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull()
  })

  it('ensureSession restores the session from the stored refresh token', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'ref')
    mockFetch((url, init) => {
      if (url.endsWith('/api/auth/token/refresh/')) return ok({ access: 'fresh' })
      if (url.endsWith('/api/users/me/') && authHeader(init) === 'Bearer fresh') return ok(ME)
      return fail(401, 'x', { code: 'TOKEN_INVALID' })
    })
    const auth = useAuthStore()
    bridge(auth)
    await auth.ensureSession()
    expect(auth.accessToken).toBe('fresh')
    expect(auth.me).toEqual(ME)
  })

  it('ensureSession logs out when the refresh token is rejected', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'expired')
    mockFetch(() => fail(401, 'Token is invalid or expired.', { code: 'TOKEN_INVALID' }))
    const auth = useAuthStore()
    bridge(auth)
    await auth.ensureSession()
    expect(auth.me).toBeNull()
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull()
  })

  it('ensureSession keeps the refresh token when the API is unreachable', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'ref')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    const auth = useAuthStore()
    bridge(auth)
    await auth.ensureSession()
    expect(auth.me).toBeNull()
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBe('ref')
  })

  it('loadMe refreshes on an expired access token (single retry)', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'ref')
    const spy = mockFetch((url, init) => {
      if (url.endsWith('/api/auth/token/refresh/')) return ok({ access: 'new' })
      return authHeader(init) === 'Bearer new' ? ok(ME) : fail(401, 'x', { code: 'TOKEN_INVALID' })
    })
    const auth = useAuthStore()
    bridge(auth)
    auth.accessToken = 'stale'
    await expect(auth.loadMe()).resolves.toEqual(ME)
    expect(spy).toHaveBeenCalledTimes(3)
  })
})
