/**
 * Role → PWA area routing (ADR-011). Presentation only: the backend decides the role.
 */
import type { Role } from '@/api/auth'

export const ROLE_AREAS: Record<Role, string> = {
  CUSTOMER: 'customer',
  DRIVER: 'driver',
  STORE: 'store',
  ADMIN: 'admin',
}

/** Route name of the user's area, or null for a role this client does not know. */
export function areaRouteName(role: string | null | undefined): string | null {
  if (!role) return null
  return (ROLE_AREAS as Record<string, string>)[role] ?? null
}
