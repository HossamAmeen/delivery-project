import { describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, type RouteLocationNormalized } from 'vue-router'

import { resolveNavigation, type GuardAuth } from '../guard'
import { routes } from '../index'

function authWith(role: string | null): GuardAuth {
  return {
    me: role ? { role } : null,
    ensureSession: vi.fn().mockResolvedValue(undefined),
  }
}

const router = createRouter({ history: createMemoryHistory(), routes })
const to = (path: string): RouteLocationNormalized =>
  router.resolve(path) as RouteLocationNormalized

describe('resolveNavigation', () => {
  it('sends anonymous users from / and role areas to /login', async () => {
    const auth = authWith(null)
    expect(await resolveNavigation(to('/'), auth)).toEqual({ name: 'login' })
    for (const path of ['/customer', '/driver', '/store', '/admin']) {
      expect(await resolveNavigation(to(path), auth)).toEqual({ name: 'login' })
    }
    expect(auth.ensureSession).toHaveBeenCalled()
  })

  it('lets anonymous users reach /login, /status and unknown routes', async () => {
    const auth = authWith(null)
    expect(await resolveNavigation(to('/login'), auth)).toBe(true)
    expect(await resolveNavigation(to('/status'), auth)).toBe(true)
    const unknown = to('/does/not/exist')
    expect(unknown.name).toBe('not-found')
    expect(await resolveNavigation(unknown, auth)).toBe(true)
  })

  it.each([
    ['CUSTOMER', 'customer'],
    ['DRIVER', 'driver'],
    ['STORE', 'store'],
    ['ADMIN', 'admin'],
  ])('sends a %s user from / and /login to their area', async (role, area) => {
    const auth = authWith(role)
    expect(await resolveNavigation(to('/'), auth)).toEqual({ name: area })
    expect(await resolveNavigation(to('/login'), auth)).toEqual({ name: area })
    expect(await resolveNavigation(to(`/${area}`), auth)).toBe(true)
  })

  it("redirects a user away from another role's area", async () => {
    const auth = authWith('DRIVER')
    expect(await resolveNavigation(to('/admin'), auth)).toEqual({ name: 'driver' })
    expect(await resolveNavigation(to('/customer'), auth)).toEqual({ name: 'driver' })
  })

  it('lets a signed-in user open /status', async () => {
    expect(await resolveNavigation(to('/status'), authWith('STORE'))).toBe(true)
  })

  it('sends a user with an unknown role to /status instead of an area', async () => {
    const auth = authWith('UNKNOWN')
    expect(await resolveNavigation(to('/'), auth)).toEqual({ name: 'status' })
    expect(await resolveNavigation(to('/customer'), auth)).toEqual({ name: 'status' })
  })
})
