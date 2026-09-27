<script setup lang="ts">
import { t } from '@/i18n'
</script>

<template>
  <a class="skip-link" href="#main">{{ t('app.skipToContent') }}</a>
  <RouterView />
</template>
