<script setup lang="ts">
import { ref } from 'vue'
import { Bell, ChatDotRound, Document, UploadFilled, Refresh } from '@element-plus/icons-vue'
import AppShell from '@/components/AppShell.vue'
import { fetchWelcome } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const backendMessage = ref('还没有连接后端')
const checking = ref(false)
const connected = ref(false)

const modules = [
  { title: '本班通知', description: '查看团支书发布的最新通知', icon: Bell, tone: 'coral' },
  { title: '待提交任务', description: '查看个人信息和材料收集任务', icon: Document, tone: 'blue' },
  { title: '文件提交', description: '未来上传表格、申请书和证明材料', icon: UploadFilled, tone: 'green' },
  { title: 'AI 答疑', description: '使用 DeepSeek 测试团务常见问题问答', icon: ChatDotRound, tone: 'purple', route: '/student/ai-qa' },
]

async function checkBackend() {
  checking.value = true
  try {
    const data = await fetchWelcome('student')
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
  <AppShell role-label="学生端" active-label="我的工作台">
    <section class="welcome-row">
      <div>
        <p class="eyebrow">{{ authStore.className }}</p>
        <h1>学生工作台</h1>
        <p>查看本班通知、待办任务和材料提交入口。</p>
      </div>
      <div class="date-card student-card">
        <span>当前身份</span>
        <strong>班级学生</strong>
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
        <div><span class="eyebrow">功能规划</span><h2>我的班级服务</h2></div>
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
