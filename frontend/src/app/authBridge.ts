/**
 * Connects the API client to the auth store and the router.
 * On an unrecoverable 401 (refresh rejected): logout + redirect to /login.
 */
import type { Router } from 'vue-router'

import { setAuthHooks } from '@/api/client'
import type { useAuthStore } from '@/stores/auth'

export function installAuthBridge(auth: ReturnType<typeof useAuthStore>, router: Router): void {
  setAuthHooks({
    getAccessToken: () => auth.accessToken,
    refreshAccessToken: () => auth.refreshAccessToken(),
    onAuthFailure: () => {
      auth.logout()
      if (router.currentRoute.value.name !== 'login') {
        void router.replace({ name: 'login', query: { expired: '1' } })
      }
    },
  })
}
