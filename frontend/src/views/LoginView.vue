<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock, MagicStick } from '@element-plus/icons-vue'
import { http } from '@/api/http'
import { useAuthStore, type UserRole } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const mode = ref<'login' | 'register'>('login')
const username = ref('secretary1')
const password = ref('123456')
const displayName = ref('')
const inviteCode = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  if (loading.value) return
  loading.value = true; errorMessage.value = ''
  try {
    const endpoint = mode.value === 'login' ? '/api/auth/login' : '/api/auth/register'
    const body = mode.value === 'login' ? { username: username.value, password: password.value } : { username: username.value, password: password.value, display_name: displayName.value, invite_code: inviteCode.value }
    const { data } = await http.post(endpoint, body)
    authStore.login(data.access_token, data.user as { role: UserRole; class_name: string; display_name: string })
    router.push(data.user.role === 'secretary' ? '/secretary' : '/student')
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail ?? '无法连接本地后端，请确认FastAPI已经启动。'
  } finally { loading.value = false }
}
</script>

<template>
  <main class="login-page">
    <section class="login-intro">
      <div class="intro-topline"><span class="intro-logo"><MagicStick /></span><span>团支书 AI 助手</span></div>
      <div class="intro-copy"><p class="kicker">本地数据 · 班级隔离</p><h1>让繁琐团务，<br /><span>变得清晰简单。</span></h1><p class="intro-description">通知、信息收集、会议整理和知识问答，都保存在你的电脑中。</p></div>
      <div class="intro-footer"><span class="status-dot"></span><span>第二阶段本地版</span></div>
    </section>
    <section class="login-panel">
      <form class="login-box" @submit.prevent="submit">
        <p class="step-label">本地账号</p><h2>{{ mode === 'login' ? '登录班级工作台' : '使用邀请码注册' }}</h2>
        <p class="login-hint">演示团支书账号：secretary1，密码：123456。</p>
        <label class="class-field"><span>账号</span><input v-model.trim="username" autocomplete="username" required minlength="3" /></label>
        <label class="class-field"><span>密码</span><input v-model="password" type="password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" required minlength="6" /></label>
        <template v-if="mode === 'register'">
          <label class="class-field"><span>姓名</span><input v-model.trim="displayName" required /></label>
          <label class="class-field"><span>班级邀请码</span><input v-model.trim="inviteCode" required placeholder="例如 JSJ23-1" /></label>
        </template>
        <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
        <button class="primary-action login-submit" :disabled="loading" type="submit">{{ loading ? '正在验证…' : mode === 'login' ? '登录' : '注册并进入' }}</button>
        <button class="text-action" type="button" @click="mode = mode === 'login' ? 'register' : 'login'; errorMessage = ''">{{ mode === 'login' ? '我是学生，使用邀请码注册' : '已有账号，返回登录' }}</button>
        <div class="security-note"><Lock /><span>账号和业务数据仅保存在本机SQLite数据库</span></div>
      </form>
    </section>
  </main>
</template>
