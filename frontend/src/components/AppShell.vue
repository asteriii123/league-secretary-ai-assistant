<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Bell, House, MagicStick, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  roleLabel: string
  activeLabel: string
}>()

const router = useRouter()
const authStore = useAuthStore()

function logout() {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark"><MagicStick /></span>
        <span>
          <strong>团支书 AI 助手</strong>
          <small>团务工作台</small>
        </span>
      </div>

      <nav class="side-nav" aria-label="主导航">
        <button class="nav-item is-active" type="button">
          <House />
          <span>{{ activeLabel }}</span>
        </button>
        <button class="nav-item" type="button" disabled>
          <Bell />
          <span>更多功能（待开发）</span>
        </button>
      </nav>

      <div class="sidebar-note">
        <span>当前版本</span>
        <strong>基础框架 V0.1</strong>
        <p>先让前后端稳定跑起来，再逐步加入业务功能。</p>
      </div>
    </aside>

    <div class="main-area">
      <header class="topbar">
        <div>
          <span class="eyebrow">{{ authStore.className }}</span>
          <strong>{{ roleLabel }} · {{ authStore.displayName }}</strong>
        </div>
        <button class="logout-button" type="button" @click="logout">
          <SwitchButton />
          重新选择
        </button>
      </header>

      <main class="page-content">
        <slot />
      </main>
    </div>
  </div>
</template>
