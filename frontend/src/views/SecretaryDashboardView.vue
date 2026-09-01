<script setup lang="ts">
import { ref } from 'vue'
import { Bell, ChatDotRound, Document, FolderOpened, Microphone, Refresh } from '@element-plus/icons-vue'
import AppShell from '@/components/AppShell.vue'
import { fetchWelcome } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const backendMessage = ref('还没有连接后端')
const checking = ref(false)
const connected = ref(false)

const modules = [
  { title: '通知管理', description: '发布和查看本班团务通知', icon: Bell, tone: 'coral' },
  { title: '信息收集', description: '创建个人信息和材料收集任务', icon: Document, tone: 'blue' },
  { title: '会议助手', description: '粘贴会议文字稿并使用 DeepSeek 整理纪要', icon: Microphone, tone: 'green', route: '/secretary/meeting-summary' },
  { title: '知识资料', description: '未来管理本地团务知识文件', icon: FolderOpened, tone: 'purple' },
]

async function checkBackend() {
  checking.value = true
  try {
    const data = await fetchWelcome('secretary')
    backendMessage.value = data.message
    connected.value = true
  } catch {
    backendMessage.value = '连接失败，请确认 FastAPI 已在 8000 端口启动'
    connected.value = false
  } finally {
    checking.value = false
  }
}
</script>

<template>
  <AppShell role-label="团支书端" active-label="班级工作台">
    <section class="welcome-row">
      <div>
        <p class="eyebrow">{{ authStore.className }}</p>
        <h1>团支书工作台</h1>
        <p>管理本班的通知、信息收集和会议材料。</p>
      </div>
      <div class="date-card">
        <span>当前身份</span>
        <strong>班级团支书</strong>
      </div>
    </section>

    <section class="connection-card">
      <div>
        <span :class="['connection-dot', { online: connected }]"></span>
        <span>{{ backendMessage }}</span>
      </div>
      <el-button :loading="checking" @click="checkBackend">
        <el-icon><Refresh /></el-icon>
        测试后端连接
      </el-button>
    </section>

    <section class="section-block">
      <div class="section-heading">
        <div><span class="eyebrow">功能规划</span><h2>班级管理</h2></div>
        <span class="coming-badge">页面占位</span>
      </div>
      <div class="module-grid">
        <component :is="item.route ? 'RouterLink' : 'article'" v-for="item in modules" :key="item.title" :to="item.route" :class="['module-card', { 'module-card-link': item.route }]">
          <span :class="['module-icon', item.tone]"><component :is="item.icon" /></span>
          <h3>{{ item.title }}</h3><p>{{ item.description }}</p>
          <span class="module-status">{{ item.route ? '现在体验 →' : '后续开发' }}</span>
        </component>
      </div>
    </section>
  </AppShell>
</template>
