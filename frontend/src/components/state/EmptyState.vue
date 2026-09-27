<script setup lang="ts">
defineProps<{ title: string; description?: string }>()
</script>

<template>
  <div class="state state-empty" data-testid="state-empty">
    <p class="state-title">{{ title }}</p>
    <p v-if="description" class="state-text">{{ description }}</p>
    <div v-if="$slots.default" class="state-actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.state-empty {
  padding: var(--space-4);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-sm);
  text-align: center;
}

.state-title {
  font-weight: 600;
  margin-bottom: var(--space-1);
}

.state-text {
  color: var(--color-text-muted);
}

.state-actions {
  margin-top: var(--space-3);
}
</style>
