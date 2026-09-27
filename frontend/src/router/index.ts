import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { resolveNavigation } from './guard'

export const routes: RouteRecordRaw[] = [
  // Never rendered: the guard redirects `/` to the user's area or to /login.
  { path: '/', name: 'home', component: () => import('@/views/NotFoundView.vue') },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/status',
    name: 'status',
    component: () => import('@/views/StatusView.vue'),
    meta: { public: true },
  },
  // Role areas are code-split so a user only downloads their own area (ADR-011).
  {
    path: '/customer',
    name: 'customer',
    component: () => import('@/views/areas/CustomerAreaView.vue'),
    meta: { role: 'CUSTOMER' },
  },
  {
    path: '/driver',
    name: 'driver',
    component: () => import('@/views/areas/DriverAreaView.vue'),
    meta: { role: 'DRIVER' },
  },
  {
    path: '/store',
    name: 'store',
    component: () => import('@/views/areas/StoreAreaView.vue'),
    meta: { role: 'STORE' },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/areas/AdminAreaView.vue'),
    meta: { role: 'ADMIN' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { public: true },
  },
]

export function createAppRouter() {
  const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
    scrollBehavior: () => ({ top: 0 }),
  })
  router.beforeEach((to) => resolveNavigation(to, useAuthStore()))
  return router
}
