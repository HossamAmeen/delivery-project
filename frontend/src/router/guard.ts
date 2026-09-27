import type { RouteLocationNormalized, RouteLocationRaw } from 'vue-router'

import { areaRouteName } from '@/app/roles'
import type { Role } from '@/api/auth'

export interface GuardAuth {
  me: { role: Role | string } | null
  ensureSession(): Promise<void>
}

declare module 'vue-router' {
  interface RouteMeta {
    /** Route of a role area; only that role may enter. */
    role?: Role
    /** Login page: a signed-in user is sent to their area. */
    guestOnly?: boolean
    /** Reachable by everyone (status, not-found). */
    public?: boolean
  }
}

/**
 * Navigation rules (TASK-007):
 * - `/` → own area when signed in, else `/login`
 * - `/login` → own area when already signed in
 * - role areas: anonymous → `/login`; other role → own area
 */
export async function resolveNavigation(
  to: RouteLocationNormalized,
  auth: GuardAuth,
): Promise<true | RouteLocationRaw> {
  await auth.ensureSession()
  const area = auth.me ? areaRouteName(auth.me.role) : null
  const ownArea: RouteLocationRaw | null = area ? { name: area } : null

  if (to.name === 'home') {
    if (ownArea) return ownArea
    return auth.me ? { name: 'status' } : { name: 'login' }
  }
  if (to.meta.guestOnly) return ownArea ?? true
  if (to.meta.role) {
    if (!auth.me) return { name: 'login' }
    if (auth.me.role !== to.meta.role) return ownArea ?? { name: 'status' }
    return true
  }
  return true
}
