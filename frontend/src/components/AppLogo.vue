<script setup lang="ts">
import logoUrl from '@/assets/flash-logo.png'
import { APP_NAME } from '@/config/env'
import { t } from '@/i18n'

withDefaults(defineProps<{ width?: number }>(), { width: 200 })
</script>

<template>
  <!-- The lockup image carries the Arabic tagline; UI text stays English until BLK-009. -->
  <img
    class="app-logo"
    :src="logoUrl"
    :alt="t('app.logoAlt', { appName: APP_NAME })"
    :width="width"
    :height="Math.round((width * 424) / 480)"
    decoding="async"
  />
</template>

<style scoped>
.app-logo {
  display: block;
  margin: 0 auto;
}
</style>
