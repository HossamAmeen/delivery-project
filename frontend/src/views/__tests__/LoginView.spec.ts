import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

import LoginView from '../LoginView.vue'
import { setAuthHooks } from '@/api/client'
import { API, fail, mockFetch, ok } from '@/test/http'
import { mountView } from '@/test/mountView'

afterEach(() => {
  setAuthHooks(null)
  vi.unstubAllGlobals()
  localStorage.clear()
})

async function fillAndSubmit(
  wrapper: Awaited<ReturnType<typeof mountView>>['wrapper'],
  u: string,
  p: string,
) {
  await wrapper.find('#login-username').setValue(u)
  await wrapper.find('#login-password').setValue(p)
  await wrapper.find('form').trigger('submit')
}

describe('LoginView', () => {
  it('has labelled username and password fields', async () => {
    mockFetch(() => ok({}))
    const { wrapper } = await mountView(LoginView, '/login')
    expect(wrapper.find('label[for="login-username"]').text()).toBe('Username')
    expect(wrapper.find('label[for="login-password"]').text()).toBe('Password')
    expect(wrapper.find('#login-password').attributes('type')).toBe('password')
  })

  it('validates required fields without calling the API', async () => {
    const spy = mockFetch(() => ok({}))
    const { wrapper } = await mountView(LoginView, '/login')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.text()).toContain('Username is required.')
    expect(wrapper.text()).toContain('Password is required.')
    expect(wrapper.find('#login-username').attributes('aria-invalid')).toBe('true')
    expect(spy).not.toHaveBeenCalled()
  })

  it('shows the API message for INVALID_CREDENTIALS and clears the password', async () => {
    mockFetch(() => fail(401, 'Invalid username or password.', { code: 'INVALID_CREDENTIALS' }))
    const { wrapper } = await mountView(LoginView, '/login')
    await fillAndSubmit(wrapper, 'someone', 'wrong')
    await flushPromises()
    expect(wrapper.find('[data-testid="form-error"]').text()).toBe('Invalid username or password.')
    expect((wrapper.find('#login-password').element as HTMLInputElement).value).toBe('')
  })

  it('shows a rate-limit message with Retry-After on 429', async () => {
    mockFetch(() =>
      fail(429, 'Request rate limit exceeded.', { code: 'THROTTLED' }, { 'Retry-After': '30' }),
    )
    const { wrapper } = await mountView(LoginView, '/login')
    await fillAndSubmit(wrapper, 'someone', 'pw')
    await flushPromises()
    expect(wrapper.find('[data-testid="form-error"]').text()).toBe(
      'Too many sign-in attempts. Please try again in 30 seconds.',
    )
  })

  it('shows backend field errors under the fields', async () => {
    mockFetch(() => fail(400, 'Validation failed.', { password: ['This field may not be blank.'] }))
    const { wrapper } = await mountView(LoginView, '/login')
    await fillAndSubmit(wrapper, 'someone', 'pw')
    await flushPromises()
    expect(wrapper.find('#login-password-error').text()).toBe('This field may not be blank.')
  })

  it('disables submit while loading, then routes to the role area', async () => {
    let release!: () => void
    const gate = new Promise<void>((resolve) => (release = resolve))
    mockFetch(async (url) => {
      if (url === `${API}/api/auth/token/`) {
        await gate
        return ok({ access: 'acc', refresh: 'ref' })
      }
      return ok({ id: 1, username: 'qa_store', role: 'STORE', is_staff: false })
    })
    const logSpy = vi.spyOn(console, 'log')
    const { wrapper, router } = await mountView(LoginView, '/login')
    await fillAndSubmit(wrapper, 'qa_store', 'pw-123')
    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
    expect(wrapper.find('button[type="submit"]').text()).toBe('Signing in…')
    release()
    // The lazy role-area chunk resolves asynchronously.
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('store'))
    // The password never reaches the console.
    expect(JSON.stringify(logSpy.mock.calls)).not.toContain('pw-123')
  })

  it('shows a network error message when the API is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    const { wrapper } = await mountView(LoginView, '/login')
    await fillAndSubmit(wrapper, 'someone', 'pw')
    await flushPromises()
    expect(wrapper.find('[data-testid="form-error"]').text()).toContain('Cannot reach the server')
  })
})
