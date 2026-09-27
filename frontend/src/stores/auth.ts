/**
 * Auth store (ADR-008 token storage for sprint-01):
 * - access token in memory only
 * - refresh token in localStorage (known limitation; revisit with httpOnly cookies)
 * The password is never stored or logged.
 */
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchMe, obtainToken, refreshToken as refreshTokenApi, type Me } from '@/api/auth'
import { isApiError } from '@/api/errors'

export const REFRESH_TOKEN_KEY = 'flash.refreshToken'

function readStoredRefresh(): string | null {
  try {
    return window.localStorage.getItem(REFRESH_TOKEN_KEY)
  } catch {
    return null
  }
}

function writeStoredRefresh(value: string | null): void {
  try {
    if (value) window.localStorage.setItem(REFRESH_TOKEN_KEY, value)
    else window.localStorage.removeItem(REFRESH_TOKEN_KEY)
  } catch {
    // Storage unavailable (private mode): the session simply does not survive a reload.
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(readStoredRefresh())
  const me = ref<Me | null>(null)
  let restoring: Promise<void> | null = null

  const isAuthenticated = computed(() => me.value !== null && accessToken.value !== null)
  const hasSession = computed(() => accessToken.value !== null || refreshToken.value !== null)

  function setTokens(access: string | null, refresh?: string | null): void {
    accessToken.value = access
    if (refresh !== undefined) {
      refreshToken.value = refresh
      writeStoredRefresh(refresh)
    }
  }

  async function loadMe(): Promise<Me> {
    const user = await fetchMe()
    me.value = user
    return user
  }

  async function login(username: string, password: string): Promise<Me> {
    const tokens = await obtainToken(username, password)
    setTokens(tokens.access, tokens.refresh)
    restoring = null
    try {
      return await loadMe()
    } catch (error) {
      logout()
      throw error
    }
  }

  function logout(): void {
    // No logout/blacklist endpoint in the approved contract: the session is cleared client-side.
    accessToken.value = null
    me.value = null
    restoring = null
    setTokens(null, null)
  }

  /**
   * Used by the API client on a 401. Returns the new access token, or null when the
   * refresh token is missing or was rejected (400/401). Network/5xx/429 errors are re-thrown
   * so a temporary outage does not destroy the session.
   */
  async function refreshAccessToken(): Promise<string | null> {
    const stored = refreshToken.value
    if (!stored) return null
    try {
      const { access } = await refreshTokenApi(stored)
      accessToken.value = access
      return access
    } catch (error) {
      if (isApiError(error) && (error.status === 400 || error.status === 401)) return null
      throw error
    }
  }

  /**
   * Restores the session after a page load (refresh token → access → /me). Runs once;
   * route guards await it. A rejected refresh logs out; an unreachable API keeps the
   * refresh token so a later reload can recover.
   */
  function ensureSession(): Promise<void> {
    if (me.value && accessToken.value) return Promise.resolve()
    if (!refreshToken.value && !accessToken.value) return Promise.resolve()
    if (!restoring) {
      restoring = (async () => {
        try {
          if (!accessToken.value) {
            const access = await refreshAccessToken()
            if (!access) {
              logout()
              return
            }
          }
          await loadMe()
        } catch (error) {
          if (isApiError(error) && error.status === 401) logout()
          else restoring = null
        }
      })()
    }
    return restoring
  }

  return {
    accessToken,
    refreshToken,
    me,
    isAuthenticated,
    hasSession,
    login,
    logout,
    loadMe,
    refreshAccessToken,
    ensureSession,
  }
})
