<script setup lang="ts">
import { ref } from 'vue'
import { ArrowLeft, ChatDotRound, Warning } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { askStudentQuestion, getApiErrorMessage, type StudentAnswer } from '@/api/ai'

const router = useRouter()
const question = ref('')
const loading = ref(false)
const errorMessage = ref('')
const result = ref<StudentAnswer | null>(null)

async function submitQuestion() {
  const value = question.value.trim()
  if (value.length < 2 || loading.value) return
  loading.value = true
  errorMessage.value = ''
  result.value = null
  try {
    result.value = await askStudentQuestion(value)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppShell role-label="学生端" active-label="AI 团务问答">
    <button class="back-link" type="button" @click="router.push('/student')">
      <ArrowLeft /> 返回学生工作台
    </button>

    <section class="tool-heading">
      <span class="module-icon purple"><ChatDotRound /></span>
      <div>
        <p class="eyebrow">DeepSeek 测试功能</p>
        <h1>学生端团务问答</h1>
        <p>可以询问入团、入党申请材料等常见问题。</p>
      </div>
    </section>

    <section class="ai-form-card" :aria-busy="loading">
      <label for="student-question">你的问题</label>
      <textarea
        id="student-question"
        v-model.trim="question"
        maxlength="1000"
        rows="7"
        placeholder="例如：入党申请书一般需要包含哪些内容？"
      ></textarea>
      <div class="field-footer"><span>请不要填写身份证号、手机号等个人信息</span><span>{{ question.length }}/1000</span></div>
      <button class="primary-action" type="button" :disabled="question.trim().length < 2 || loading" @click="submitQuestion">
        {{ loading ? 'DeepSeek 正在回答…' : '提交问题' }}
      </button>
      <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }} 请检查 Render 是否已配置 DeepSeek 密钥，然后重试。</p>
    </section>

    <section v-if="result" class="result-card" aria-live="polite">
      <p class="eyebrow">AI 回答</p>
      <div class="answer-text">{{ result.answer }}</div>
      <div class="warning-note"><Warning /><span>{{ result.disclaimer }}</span></div>
    </section>
    <div v-else class="warning-note standalone"><Warning /><span>当前未接入本地知识库，不能提供可核验的校内文件来源，仅用于测试大模型连接。</span></div>
  </AppShell>
</template>
