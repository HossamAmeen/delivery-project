import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

import StatusView from '../StatusView.vue'
import { setAuthHooks } from '@/api/client'
import { REFRESH_TOKEN_KEY } from '@/stores/auth'
import { API, authHeader, fail, mockFetch, ok } from '@/test/http'
import { mountView } from '@/test/mountView'

afterEach(() => {
  setAuthHooks(null)
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe('StatusView', () => {
  it('shows "API reachable" and the configured base URL; calls only /api/status/', async () => {
    const spy = mockFetch(() => ok({ status: 'ok' }))
    const { wrapper } = await mountView(StatusView, '/status')
    expect(wrapper.find('[data-testid="status-ok"]').text()).toContain('API reachable')
    expect(wrapper.find('[data-testid="api-base-url"]').text()).toBe(API)
    const urls = spy.mock.calls.map(([url]) => String(url))
    expect(urls).toEqual([`${API}/api/status/`])
    expect(urls.some((url) => url.includes('/api/health'))).toBe(false)
    // Anonymous: the session section shows the empty state.
    expect(wrapper.find('[data-testid="state-empty"]').text()).toContain('Not signed in')
  })

  it('shows "API unreachable" with a retry on a network error, and retries', async () => {
    let online = false
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        if (!online) throw new TypeError('offline')
        return new Response(JSON.stringify({ success: true, message: '', data: { status: 'ok' } }))
      }),
    )
    const { wrapper } = await mountView(StatusView, '/status')
    const error = wrapper.find('[data-testid="state-error"]')
    expect(error.text()).toContain('API unreachable')
    online = true
    await error.find('button').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="status-ok"]').exists()).toBe(true)
  })

  it('shows the HTTP status for a 5xx answer', async () => {
    mockFetch(() => fail(503, 'Service unavailable.', { code: 'SERVER_ERROR' }))
    const { wrapper } = await mountView(StatusView, '/status')
    expect(wrapper.find('[data-testid="state-error"]').text()).toContain('(503)')
  })

  it('shows "Rate-limited" with Retry-After on 429', async () => {
    mockFetch(() =>
      fail(429, 'Request rate limit exceeded.', { code: 'THROTTLED' }, { 'Retry-After': '12' }),
    )
    const { wrapper } = await mountView(StatusView, '/status')
    const state = wrapper.find('[data-testid="state-unavailable"]')
    expect(state.text()).toContain('Rate-limited')
    expect(state.text()).toContain('12 seconds')
    expect(state.find('button').exists()).toBe(true)
  })

  it('shows username and role from /api/users/me/ when logged in', async () => {
    localStorage.setItem(REFRESH_TOKEN_KEY, 'ref')
    mockFetch((url, init) => {
      if (url.endsWith('/api/status/')) return ok({ status: 'ok' })
      if (url.endsWith('/api/auth/token/refresh/')) return ok({ access: 'acc' })
      if (url.endsWith('/api/users/me/') && authHeader(init) === 'Bearer acc')
        return ok({ id: 3, username: 'qa_customer', role: 'CUSTOMER', is_staff: false })
      return fail(401, 'x', { code: 'NOT_AUTHENTICATED' })
    })
    const { wrapper } = await mountView(StatusView, '/status')
    const user = wrapper.find('[data-testid="session-user"]')
    expect(user.text()).toContain('qa_customer')
    expect(user.text()).toContain('Customer')
  })
})
