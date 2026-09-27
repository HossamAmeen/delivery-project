/** Identity endpoints (api-contracts.md § Identity, APPROVED). */
import { apiRequest } from './client'

export type Role = 'CUSTOMER' | 'DRIVER' | 'STORE' | 'ADMIN'

export interface TokenPair {
  access: string
  refresh: string
}

export interface Me {
  id: number
  username: string
  role: Role
  is_staff: boolean
}

export function obtainToken(username: string, password: string): Promise<TokenPair> {
  return apiRequest<TokenPair>('/api/auth/token/', {
    method: 'POST',
    body: { username, password },
    auth: false,
  })
}

export function refreshToken(refresh: string): Promise<{ access: string }> {
  return apiRequest<{ access: string }>('/api/auth/token/refresh/', {
    method: 'POST',
    body: { refresh },
    auth: false,
  })
}

export function fetchMe(): Promise<Me> {
  return apiRequest<Me>('/api/users/me/')
}
