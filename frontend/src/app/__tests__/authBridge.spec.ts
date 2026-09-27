import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

import { apiRequest, setAuthHooks } from '@/api/client'
import { REFRESH_TOKEN_KEY } from '@/stores/auth'
import { fail, mockFetch } from '@/test/http'
import { mountView } from '@/test/mountView'
import StatusView from '@/views/StatusView.vue'

afterEach(() => {
  setAuthHooks(null)
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe('installAuthBridge', () => {
  it('logs out and redirects to /login when the refresh is rejected', async () => {
    mockFetch(() => fail(401, 'Token is invalid or expired.', { code: 'TOKEN_INVALID' }))
    const { router, auth } = await mountView(StatusView, '/status')
    auth.accessToken = 'stale'
    auth.refreshToken = 'expired'
    localStorage.setItem(REFRESH_TOKEN_KEY, 'expired')

    await expect(apiRequest('/api/users/me/')).rejects.toMatchObject({ status: 401 })
    await flushPromises()

    expect(auth.accessToken).toBeNull()
    expect(localStorage.getItem(REFRESH_TOKEN_KEY)).toBeNull()
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('login'))
    expect(router.currentRoute.value.query.expired).toBe('1')
  })
})
