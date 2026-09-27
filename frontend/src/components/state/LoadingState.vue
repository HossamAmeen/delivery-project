<script setup lang="ts">
import { t } from '@/i18n'

withDefaults(defineProps<{ label?: string }>(), { label: undefined })
</script>

<template>
  <div class="state state-loading" role="status" aria-live="polite" data-testid="state-loading">
    <span class="spinner" aria-hidden="true" />
    <span>{{ label ?? t('common.loading') }}</span>
  </div>
</template>

<style scoped>
.state-loading {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  color: var(--color-text-muted);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid var(--color-border);
  border-top-color: var(--flash-orange);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
}
</style>
