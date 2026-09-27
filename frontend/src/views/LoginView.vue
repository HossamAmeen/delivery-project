<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppLogo from '@/components/AppLogo.vue'
import { isApiError, type FieldErrors } from '@/api/errors'
import { areaRouteName } from '@/app/roles'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ username: '', password: '' })
const clientErrors = reactive<{ username: string | null; password: string | null }>({
  username: null,
  password: null,
})
const serverFieldErrors = ref<FieldErrors>({})
const formError = ref<string | null>(null)
const loading = ref(false)

const sessionExpired = computed(() => route.query.expired === '1')

function fieldError(field: 'username' | 'password'): string | null {
  return clientErrors[field] ?? serverFieldErrors.value[field]?.join(' ') ?? null
}

function validate(): boolean {
  clientErrors.username = form.username.trim() ? null : t('login.usernameRequired')
  clientErrors.password = form.password ? null : t('login.passwordRequired')
  return !clientErrors.username && !clientErrors.password
}

function describeError(error: unknown): string {
  if (!isApiError(error)) return t('login.genericError')
  if (error.kind === 'rate_limited') {
    return error.retryAfter !== null
      ? t('login.rateLimitedSeconds', { seconds: error.retryAfter })
      : t('login.rateLimited')
  }
  if (error.kind === 'network') return t('errors.network')
  if (error.kind === 'server') return t('errors.server')
  if (error.fieldErrors.non_field_errors?.length)
    return error.fieldErrors.non_field_errors.join(' ')
  // INVALID_CREDENTIALS and other API errors: show the API's own message.
  return error.message || t('login.genericError')
}

async function onSubmit(): Promise<void> {
  if (loading.value) return
  formError.value = null
  serverFieldErrors.value = {}
  if (!validate()) return

  loading.value = true
  try {
    const me = await auth.login(form.username.trim(), form.password)
    form.password = ''
    const area = areaRouteName(me.role)
    await router.replace(area ? { name: area } : { name: 'status' })
  } catch (error) {
    form.password = ''
    if (isApiError(error)) serverFieldErrors.value = error.fieldErrors
    formError.value = describeError(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-screen">
    <div class="brand-bar" aria-hidden="true" />
    <main id="main" class="login-main">
      <div class="card login-card">
        <AppLogo :width="180" />
        <h1 class="login-title">{{ t('login.title') }}</h1>
        <p class="login-subtitle">{{ t('login.subtitle') }}</p>

        <p v-if="sessionExpired && !formError" class="notice" role="status">
          {{ t('login.sessionExpired') }}
        </p>
        <p v-if="formError" class="form-error" role="alert" data-testid="form-error">
          {{ formError }}
        </p>

        <form novalidate @submit.prevent="onSubmit">
          <div class="field">
            <label for="login-username">{{ t('login.username') }}</label>
            <input
              id="login-username"
              v-model="form.username"
              name="username"
              type="text"
              autocomplete="username"
              autocapitalize="none"
              spellcheck="false"
              required
              :aria-invalid="fieldError('username') ? 'true' : 'false'"
              :aria-describedby="fieldError('username') ? 'login-username-error' : undefined"
            />
            <p v-if="fieldError('username')" id="login-username-error" class="field-error">
              {{ fieldError('username') }}
            </p>
          </div>

          <div class="field">
            <label for="login-password">{{ t('login.password') }}</label>
            <input
              id="login-password"
              v-model="form.password"
              name="password"
              type="password"
              autocomplete="current-password"
              required
              :aria-invalid="fieldError('password') ? 'true' : 'false'"
              :aria-describedby="fieldError('password') ? 'login-password-error' : undefined"
            />
            <p v-if="fieldError('password')" id="login-password-error" class="field-error">
              {{ fieldError('password') }}
            </p>
          </div>

          <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
            {{ loading ? t('login.submitting') : t('login.submit') }}
          </button>
        </form>

        <p class="login-footer">
          <RouterLink :to="{ name: 'status' }">{{ t('common.statusLink') }}</RouterLink>
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login-screen {
  min-height: 100vh;
  min-height: 100dvh;
}

.login-main {
  display: flex;
  justify-content: center;
  padding: var(--space-4);
}

.login-card {
  width: 100%;
  max-width: 400px;
  margin-top: var(--space-4);
}

@media (min-width: 768px) {
  .login-card {
    margin-top: 8vh;
    padding: var(--space-6);
  }
}

.login-title {
  margin-top: var(--space-4);
  text-align: center;
}

.login-subtitle {
  text-align: center;
  color: var(--color-text-muted);
}

.field {
  margin-bottom: var(--space-4);
}

.field label {
  display: block;
  margin-bottom: var(--space-1);
  font-weight: 600;
}

.field input {
  width: 100%;
  min-height: 44px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font: inherit;
  color: var(--color-text);
  background: var(--color-surface);
}

.field input:focus-visible {
  outline: none;
  border-color: var(--flash-blue);
  box-shadow: var(--focus-ring);
}

.field input[aria-invalid='true'] {
  border-color: var(--color-danger);
}

.field-error {
  margin: var(--space-1) 0 0;
  color: var(--color-danger);
  font-size: 0.875rem;
}

.form-error {
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.notice {
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.login-footer {
  margin: var(--space-4) 0 0;
  text-align: center;
  font-size: 0.875rem;
}
</style>
