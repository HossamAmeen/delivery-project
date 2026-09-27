<script setup lang="ts">
import { useRouter } from 'vue-router'

import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

defineProps<{ title: string }>()

const auth = useAuthStore()
const router = useRouter()

function onLogout(): void {
  auth.logout()
  void router.replace({ name: 'login' })
}
</script>

<template>
  <div class="area">
    <div class="brand-bar" aria-hidden="true" />
    <header class="area-header">
      <div class="page area-header-inner">
        <div>
          <h1>{{ title }}</h1>
          <p v-if="auth.me" class="area-user">
            {{ t('areas.signedInAs', { username: auth.me.username }) }}
          </p>
        </div>
        <button type="button" class="btn btn-secondary" data-testid="logout" @click="onLogout">
          {{ t('common.logout') }}
        </button>
      </div>
    </header>
    <main id="main" class="page">
      <section class="card">
        <p>{{ t('areas.placeholder') }}</p>
        <RouterLink :to="{ name: 'status' }">{{ t('common.statusLink') }}</RouterLink>
      </section>
    </main>
  </div>
</template>

<style scoped>
.area-header {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.area-header-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.area-header h1 {
  margin: 0;
}

.area-user {
  margin: 0;
  color: var(--color-text-muted);
}
</style>
