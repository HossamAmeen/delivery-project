<script setup lang="ts">
import { t } from '@/i18n'
</script>

<template>
  <main id="main" class="page not-found">
    <div class="card">
      <h1>{{ t('notFound.title') }}</h1>
      <p>{{ t('notFound.detail') }}</p>
      <RouterLink class="btn btn-primary" :to="{ name: 'home' }">
        {{ t('common.goHome') }}
      </RouterLink>
    </div>
  </main>
</template>

<style scoped>
.not-found {
  max-width: 480px;
  padding-top: 15vh;
  text-align: center;
}
</style>
