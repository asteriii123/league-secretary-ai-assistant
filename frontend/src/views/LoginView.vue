<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Avatar, Lock, MagicStick, Management } from '@element-plus/icons-vue'
import { useAuthStore, type UserRole } from '@/stores/auth'
import { DEMO_CLASSES } from '@/config/classes'

const router = useRouter()
const authStore = useAuthStore()
const selectedClass = ref('')

function enter(role: UserRole) {
  if (!selectedClass.value) return
  authStore.enterAs(role, selectedClass.value)
  router.push(role === 'secretary' ? '/secretary' : '/student')
}
</script>

<template>
  <main class="login-page">
    <section class="login-intro">
      <div class="intro-topline">
        <span class="intro-logo"><MagicStick /></span>
        <span>团支书 AI 助手</span>
      </div>

      <div class="intro-copy">
        <p class="kicker">为 23 级团支书打造</p>
        <h1>让繁琐团务，<br /><span>变得清晰简单。</span></h1>
        <p class="intro-description">
          一个统一的团务工作平台。未来将在这里完成通知、信息收集、会议整理和政策答疑。
        </p>
      </div>

      <div class="intro-footer">
        <span class="status-dot"></span>
        <span>基础框架已就绪</span>
      </div>
    </section>

    <section class="login-panel">
      <div class="login-box">
        <p class="step-label">第一阶段 · 班级工作台</p>
        <h2>选择班级和身份</h2>
        <p class="login-hint">当前使用演示班级，不连接真实账号或数据库。</p>

        <label class="class-field" for="class-select">
          <span>所在班级</span>
          <select id="class-select" v-model="selectedClass">
            <option value="" disabled>请选择班级</option>
            <option v-for="className in DEMO_CLASSES" :key="className" :value="className">
              {{ className }}
            </option>
          </select>
        </label>

        <p v-if="!selectedClass" class="selection-hint">请先选择班级，再选择身份</p>

        <div class="role-options">
          <button class="role-card" type="button" :disabled="!selectedClass" @click="enter('secretary')">
            <span class="role-icon secretary"><Management /></span>
            <span class="role-copy">
              <strong>我是该班团支书</strong>
              <small>管理本班通知、收集任务和会议材料</small>
            </span>
            <ArrowRight class="role-arrow" />
          </button>

          <button class="role-card" type="button" :disabled="!selectedClass" @click="enter('student')">
            <span class="role-icon student"><Avatar /></span>
            <span class="role-copy">
              <strong>我是该班学生</strong>
              <small>查看本班通知、提交任务和使用 AI 答疑</small>
            </span>
            <ArrowRight class="role-arrow" />
          </button>
        </div>

        <div class="security-note">
          <Lock />
          <span>刷新页面后需要重新选择班级和身份</span>
        </div>
      </div>
    </section>
  </main>
</template>
