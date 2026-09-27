/**
 * Build-time configuration (ADR-008). Values come from `VITE_*` environment variables;
 * nothing is hardcoded. `vite.config.ts` refuses a production build without the API URL.
 */
export const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? '')
  .trim()
  .replace(/\/+$/, '')

export const APP_NAME: string = import.meta.env.VITE_APP_NAME?.trim() || 'Flash'

/** Joins the configured API origin with a contract path such as `/api/status/`. */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}
