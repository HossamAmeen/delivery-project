import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

// Brand colours sampled from 06_brand/flash_initial_logo.png.
const THEME_COLOR = '#0C214F' // navy wordmark
const BACKGROUND_COLOR = '#FFFFFF'

/**
 * Build contract (TASK-007 / TASK-013): a production build needs VITE_API_BASE_URL
 * in the environment (or a local .env file). It is never hardcoded.
 */
function assertApiBaseUrl(value: string | undefined): void {
  if (!value || !value.trim()) {
    throw new Error(
      '[flash] VITE_API_BASE_URL is not set. A production build needs the API origin, e.g.\n' +
        '  VITE_API_BASE_URL=https://api.example.com npm run build\n' +
        'See frontend/.env.example.',
    )
  }
  if (!/^https?:\/\/[^/\s]+/.test(value.trim())) {
    throw new Error(
      `[flash] VITE_API_BASE_URL must be an absolute http(s) URL, got "${value}".`,
    )
  }
}

function escapeHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
}

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  if (command === 'build' && mode === 'production') {
    assertApiBaseUrl(env.VITE_API_BASE_URL)
  }
  const appName = env.VITE_APP_NAME?.trim() || 'Flash'

  return {
    base: '/',
    plugins: [
      vue(),
      {
        name: 'flash-html-app-name',
        transformIndexHtml: (html: string) => html.replaceAll('__APP_NAME__', escapeHtml(appName)),
      },
      VitePWA({
        registerType: 'autoUpdate',
        injectRegister: 'auto',
        includeAssets: ['favicon.ico', 'icons/apple-touch-icon-180.png'],
        manifest: {
          name: appName,
          short_name: appName,
          description: `${appName} delivery`,
          start_url: '/',
          scope: '/',
          display: 'standalone',
          orientation: 'portrait',
          theme_color: THEME_COLOR,
          background_color: BACKGROUND_COLOR,
          icons: [
            { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
            { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
            {
              src: '/icons/maskable-512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
        },
        workbox: {
          // App shell only. API responses are never cached (no runtimeCaching entries).
          globPatterns: ['**/*.{js,css,html,ico,png,svg,webmanifest}'],
          navigateFallback: '/index.html',
          navigateFallbackDenylist: [/^\/api\//],
          runtimeCaching: [],
          cleanupOutdatedCaches: true,
        },
        devOptions: { enabled: false },
      }),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
