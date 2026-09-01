<script setup lang="ts">
import { ref } from 'vue'
import { ArrowLeft, Lock, Microphone, Warning } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { getApiErrorMessage, summarizeMeeting, type MeetingSummary } from '@/api/ai'

const router = useRouter()
const meetingType = ref('主题团日')
const transcript = ref('')
const loading = ref(false)
const errorMessage = ref('')
const result = ref<MeetingSummary | null>(null)

async function submitTranscript() {
  const value = transcript.value.trim()
  if (value.length < 20 || loading.value) return
  loading.value = true
  errorMessage.value = ''
  result.value = null
  try {
    result.value = await summarizeMeeting(meetingType.value, value)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppShell role-label="团支书端" active-label="会议内容总结">
    <button class="back-link" type="button" @click="router.push('/secretary')"><ArrowLeft /> 返回团支书工作台</button>
    <section class="tool-heading">
      <span class="module-icon green"><Microphone /></span>
      <div><p class="eyebrow">DeepSeek 测试功能</p><h1>会议内容总结</h1><p>粘贴已经转写好的会议文字稿，生成结构化会议纪要。</p></div>
    </section>

    <div class="privacy-note"><Lock /><span>文字稿会先隐藏常见的姓名、学号、手机号和身份证号，再发送到 DeepSeek。请仍然避免提交敏感或涉密内容。</span></div>

    <section class="ai-form-card" :aria-busy="loading">
      <label for="meeting-type">会议类型</label>
      <select id="meeting-type" v-model="meetingType">
        <option>主题团日</option><option>团课</option><option>支部会议</option><option>其他</option>
      </select>
      <label for="meeting-transcript">会议文字稿</label>
      <textarea id="meeting-transcript" v-model.trim="transcript" maxlength="50000" rows="14" placeholder="请粘贴至少 20 个字的会议文字稿……"></textarea>
      <div class="field-footer"><span>目前只支持文字稿，暂不支持直接上传音频或视频</span><span>{{ transcript.length }}/50000</span></div>
      <button class="primary-action" type="button" :disabled="transcript.trim().length < 20 || loading" @click="submitTranscript">
        {{ loading ? '正在整理会议内容…' : '生成会议纪要' }}
      </button>
      <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }} 请检查 Render 密钥配置后重试。</p>
    </section>

    <section v-if="result" class="result-card" aria-live="polite">
      <div class="result-title"><div><p class="eyebrow">生成结果</p><h2>{{ result.title }}</h2></div><span>{{ result.meeting_type }}</span></div>
      <h3>会议摘要</h3><p class="answer-text">{{ result.summary }}</p>
      <div class="result-columns">
        <div><h3>要点</h3><ul><li v-for="item in result.key_points" :key="item">{{ item }}</li></ul></div>
        <div><h3>决定</h3><ul><li v-for="item in result.decisions" :key="item">{{ item }}</li></ul></div>
      </div>
      <h3>待办事项</h3>
      <div class="action-list"><div v-for="item in result.action_items" :key="`${item.task}-${item.owner}`"><strong>{{ item.task }}</strong><span>负责人：{{ item.owner }}</span><span>截止：{{ item.deadline }}</span></div></div>
      <div class="warning-note"><Warning /><span>AI 结果可能有遗漏，请团支书人工核对后再正式使用。<template v-if="result.redacted_sensitive_data"> 本次已检测并隐藏部分敏感信息。</template></span></div>
    </section>
  </AppShell>
</template>
