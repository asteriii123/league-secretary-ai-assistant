<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown, Bell, ChatDotRound, Document, DocumentChecked, FolderOpened, House, MagicStick, Menu, SwitchButton } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

defineProps<{ roleLabel: string; activeLabel: string }>()
const route = useRoute(); const router = useRouter(); const authStore = useAuthStore()
const mobileNavOpen = ref(false); const role = computed(() => authStore.role as 'secretary' | 'student')
const dashboardPath = computed(() => role.value === 'secretary' ? '/secretary' : '/student')
const aiPath = computed(() => `${dashboardPath.value}/ai`); const storageKey = computed(() => `workspace-nav-expanded:${role.value}`)
const featureLinks = computed(() => role.value === 'secretary' ? [
  { label: '通知管理', path: '/secretary/notices', icon: Bell }, { label: '信息收集', path: '/secretary/collections', icon: Document },
  { label: '知识资料', path: '/secretary/knowledge', icon: FolderOpened }, { label: '会议文档', path: '/secretary/meeting-documents', icon: DocumentChecked },
] : [{ label: '本班通知', path: '/student/notices', icon: Bell }, { label: '信息收集', path: '/student/collections', icon: Document }])
const workspaceExpanded = ref(true)
const isFeaturePage = computed(() => featureLinks.value.some(item => item.path === route.path))
function toggleWorkspace() { workspaceExpanded.value = !workspaceExpanded.value; sessionStorage.setItem(storageKey.value, String(workspaceExpanded.value)) }
function logout() { authStore.logout(); router.push('/') }
onMounted(() => { const saved = sessionStorage.getItem(storageKey.value); workspaceExpanded.value = isFeaturePage.value || saved !== 'false' })
watch(() => route.path, () => { mobileNavOpen.value = false; if (isFeaturePage.value) { workspaceExpanded.value = true; sessionStorage.setItem(storageKey.value, 'true') } })
</script>

<template>
  <div :class="['app-shell', { 'ai-shell': route.path === aiPath }]">
    <aside :class="['sidebar', { 'mobile-open': mobileNavOpen }]">
      <div class="brand"><span class="brand-mark"><MagicStick /></span><span><strong>团支书 AI 助手</strong></span><button class="sidebar-menu-button" type="button" :aria-expanded="mobileNavOpen" aria-label="打开或关闭导航" @click="mobileNavOpen = !mobileNavOpen"><Menu /></button></div>
      <nav class="side-nav" aria-label="主导航">
        <div class="workspace-nav">
          <div class="workspace-nav-row"><RouterLink :to="dashboardPath" :class="['nav-item', { 'is-active': route.path === dashboardPath }]"><House /><span>{{ role === 'secretary' ? '班级工作台' : '我的工作台' }}</span></RouterLink><button class="workspace-toggle" type="button" :aria-expanded="workspaceExpanded" aria-label="展开或收起工作台功能" @click="toggleWorkspace"><ArrowDown :class="{ rotated: !workspaceExpanded }" /></button></div>
          <div v-show="workspaceExpanded" class="sub-nav"><RouterLink v-for="item in featureLinks" :key="item.path" :to="item.path" :class="['sub-nav-item', { 'is-active': route.path === item.path }]"><component :is="item.icon" /><span>{{ item.label }}</span></RouterLink></div>
        </div>
        <RouterLink :to="aiPath" :class="['nav-item', 'ai-nav-item', { 'is-active': route.path === aiPath }]"><ChatDotRound /><span>AI 对话</span></RouterLink>
        <button class="nav-item" type="button" disabled><Bell /><span>更多功能（待开发）</span></button>
      </nav>
      <div class="sidebar-note"><span>当前版本</span><strong>本地开发版</strong><p>业务数据、对话与知识资料均保存在本机。</p></div>
    </aside>
    <button v-if="mobileNavOpen" class="sidebar-backdrop" aria-label="关闭导航" @click="mobileNavOpen = false"></button>
    <div class="main-area"><header class="topbar"><button class="topbar-menu-button" type="button" aria-label="打开导航" @click="mobileNavOpen = true"><Menu /></button><div><span class="eyebrow">{{ authStore.className }}</span><strong>{{ roleLabel }} · {{ authStore.displayName }}</strong></div><button class="logout-button" type="button" @click="logout"><SwitchButton />重新选择</button></header><main class="page-content"><slot /></main></div>
  </div>
</template>
