import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { installAuthBridge } from './app/authBridge'
import { createAppRouter } from './router'
import { useAuthStore } from './stores/auth'
import './styles/main.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

const router = createAppRouter()
installAuthBridge(useAuthStore(pinia), router)
app.use(router)

app.mount('#app')
