import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia, type Pinia } from 'pinia'
import { createMemoryHistory, createRouter, type Router } from 'vue-router'
import type { Component } from 'vue'

import { routes } from '@/router'
import { installAuthBridge } from '@/app/authBridge'
import { useAuthStore } from '@/stores/auth'

/** Mounts a view with a real Pinia + memory router (no guard, no backend). */
export async function mountView(view: Component, path: string) {
  const pinia: Pinia = createPinia()
  setActivePinia(pinia)
  const router: Router = createRouter({ history: createMemoryHistory(), routes })
  installAuthBridge(useAuthStore(pinia), router)
  await router.push(path)
  await router.isReady()
  const wrapper = mount(view, { global: { plugins: [pinia, router] } })
  await flushPromises()
  return { wrapper, router, auth: useAuthStore(pinia) }
}
