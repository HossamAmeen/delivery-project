<script setup lang="ts">
import { onMounted, ref } from 'vue'

import AppLogo from '@/components/AppLogo.vue'
import EmptyState from '@/components/state/EmptyState.vue'
import ErrorState from '@/components/state/ErrorState.vue'
import LoadingState from '@/components/state/LoadingState.vue'
import UnavailableState from '@/components/state/UnavailableState.vue'
import { getApiStatus } from '@/api/status'
import { isApiError } from '@/api/errors'
import { API_BASE_URL } from '@/config/env'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

type ApiState =
  | { kind: 'loading' }
  | { kind: 'ok' }
  | { kind: 'unexpected'; status: string }
  | { kind: 'unreachable'; detail: string }
  | { kind: 'rate_limited'; retryAfter: number | null }

const auth = useAuthStore()
const apiState = ref<ApiState>({ kind: 'loading' })
const sessionState = ref<'idle' | 'loading' | 'ok' | 'error'>('idle')

async function checkApi(): Promise<void> {
  apiState.value = { kind: 'loading' }
  try {
    const result = await getApiStatus()
    apiState.value =
      result?.status === 'ok'
        ? { kind: 'ok' }
        : { kind: 'unexpected', status: String(result?.status) }
  } catch (error) {
    if (isApiError(error) && error.kind === 'rate_limited') {
      apiState.value = { kind: 'rate_limited', retryAfter: error.retryAfter }
    } else if (isApiError(error) && error.status > 0) {
      apiState.value = {
        kind: 'unreachable',
        detail: t('status.serverError', { httpStatus: error.status }),
      }
    } else {
      apiState.value = { kind: 'unreachable', detail: t('status.unreachableDetail') }
    }
  }
}

async function loadSession(): Promise<void> {
  if (!auth.hasSession) {
    sessionState.value = 'idle'
    return
  }
  sessionState.value = 'loading'
  try {
    await auth.loadMe()
    sessionState.value = auth.me ? 'ok' : 'idle'
  } catch {
    sessionState.value = auth.hasSession ? 'error' : 'idle'
  }
}

function refreshAll(): void {
  void checkApi()
  void loadSession()
}

onMounted(refreshAll)
</script>

<template>
  <div>
    <div class="brand-bar" aria-hidden="true" />
    <main id="main" class="page status-page">
      <AppLogo :width="120" />
      <h1 class="status-title">{{ t('status.title') }}</h1>

      <section class="card" aria-labelledby="api-heading">
        <h2 id="api-heading" class="visually-hidden">{{ t('status.title') }}</h2>
        <dl class="kv">
          <dt>{{ t('status.apiBaseUrl') }}</dt>
          <dd data-testid="api-base-url">
            <code>{{ API_BASE_URL || t('status.notConfigured') }}</code>
          </dd>
        </dl>

        <LoadingState v-if="apiState.kind === 'loading'" :label="t('status.checking')" />
        <div
          v-else-if="apiState.kind === 'ok'"
          class="status-ok"
          role="status"
          data-testid="status-ok"
        >
          <p class="status-ok-title">{{ t('status.reachable') }}</p>
          <p>{{ t('status.reachableDetail') }}</p>
          <button type="button" class="btn btn-secondary" @click="checkApi">
            {{ t('common.retry') }}
          </button>
        </div>
        <UnavailableState
          v-else-if="apiState.kind === 'unexpected'"
          :title="t('status.reachable')"
          :message="t('status.unexpected', { status: apiState.status })"
          retryable
          @retry="checkApi"
        />
        <UnavailableState
          v-else-if="apiState.kind === 'rate_limited'"
          :title="t('status.rateLimited')"
          :message="
            apiState.retryAfter !== null
              ? t('status.rateLimitedSeconds', { seconds: apiState.retryAfter })
              : t('status.rateLimitedDetail')
          "
          retryable
          @retry="checkApi"
        />
        <ErrorState
          v-else
          :title="t('status.unreachable')"
          :message="apiState.detail"
          @retry="checkApi"
        />
      </section>

      <section class="card" aria-labelledby="session-heading">
        <h2 id="session-heading">{{ t('status.sessionTitle') }}</h2>
        <LoadingState v-if="sessionState === 'loading'" />
        <dl v-else-if="sessionState === 'ok' && auth.me" class="kv" data-testid="session-user">
          <dt>{{ t('status.username') }}</dt>
          <dd>{{ auth.me.username }}</dd>
          <dt>{{ t('status.role') }}</dt>
          <dd>{{ t(`roles.${auth.me.role}`) }}</dd>
        </dl>
        <ErrorState
          v-else-if="sessionState === 'error'"
          :title="t('status.sessionError')"
          @retry="loadSession"
        />
        <EmptyState
          v-else
          :title="t('status.notSignedIn')"
          :description="t('status.notSignedInDetail')"
        >
          <RouterLink class="btn btn-primary" :to="{ name: 'login' }">
            {{ t('status.signIn') }}
          </RouterLink>
        </EmptyState>
      </section>

      <p class="status-footer">
        <RouterLink :to="{ name: 'home' }">{{ t('common.goHome') }}</RouterLink>
      </p>
    </main>
  </div>
</template>

<style scoped>
.status-page {
  max-width: 640px;
  display: grid;
  gap: var(--space-4);
}

.status-title {
  text-align: center;
  margin: 0;
}

.kv {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: var(--space-1) var(--space-4);
  margin: 0 0 var(--space-4);
}

.kv dt {
  font-weight: 600;
}

.kv dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.status-ok {
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  background: var(--color-success-bg);
  border-inline-start: 4px solid var(--color-success);
}

.status-ok-title {
  color: var(--color-success);
  font-weight: 700;
  margin-bottom: var(--space-1);
}

.status-footer {
  text-align: center;
}
</style>
