<script setup lang="ts">
import { t } from '@/i18n'

withDefaults(defineProps<{ title: string; message?: string; retryable?: boolean }>(), {
  message: undefined,
  retryable: true,
})
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="state state-error" role="alert" data-testid="state-error">
    <p class="state-title">{{ title }}</p>
    <p v-if="message" class="state-text">{{ message }}</p>
    <button v-if="retryable" type="button" class="btn btn-secondary" @click="emit('retry')">
      {{ t('common.retry') }}
    </button>
  </div>
</template>

<style scoped>
.state-error {
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  background: var(--color-danger-bg);
  border-inline-start: 4px solid var(--color-danger);
}

.state-title {
  color: var(--color-danger);
  font-weight: 700;
  margin-bottom: var(--space-1);
}
</style>
