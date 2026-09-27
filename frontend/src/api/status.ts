/**
 * Public, browser-safe status endpoint (ADR-019). The PWA never calls `/api/health/`
 * and never holds a health token.
 */
import { apiRequest } from './client'

export interface ApiStatus {
  status: string
}

export function getApiStatus(): Promise<ApiStatus> {
  return apiRequest<ApiStatus>('/api/status/', { auth: false })
}
