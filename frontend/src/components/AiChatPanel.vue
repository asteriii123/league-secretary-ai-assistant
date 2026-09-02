<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { ChatDotRound, Close, Delete, Promotion, RefreshRight } from '@element-plus/icons-vue'
import { API_BASE_URL } from '@/api/http'

interface Source { label: string; filename: string; heading: string; page: number }
interface Message { role: 'user' | 'assistant'; content: string; failed?: boolean; sources?: Source[] }
const props = defineProps<{ role: 'secretary' | 'student' }>()
const messages = ref<Message[]>([])
const question = ref('')
const loading = ref(false)
const stage = ref('')
const controller = ref<AbortController | null>(null)
const chatBody = ref<HTMLElement | null>(null)
const examples = computed(() => props.role === 'secretary'
  ? ['帮我起草一份团费收缴通知', '主题团日活动可以怎样安排？']
  : ['入党申请书一般包含哪些内容？', '团员需要履行哪些义务？'])

async function scrollToLatest() { await nextTick(); chatBody.value?.scrollTo({ top: chatBody.value.scrollHeight, behavior: 'smooth' }) }
function handleEvent(block: string) {
  const event = block.match(/^event: (.+)$/m)?.[1]
  const dataText = block.match(/^data: (.+)$/m)?.[1]
  if (!event || !dataText) return
  const data = JSON.parse(dataText)
  const answer = messages.value[messages.value.length - 1]
  if (!answer || answer.role !== 'assistant') return
  if (event === 'content') answer.content += data.text
  if (event === 'sources') answer.sources = data.items
  if (event === 'status') stage.value = data.message
  if (event === 'error') { answer.content = data.message; answer.failed = true }
  scrollToLatest()
}
async function send(text = question.value) {
  const value = text.trim()
  if (!value || loading.value) return
  const history = messages.value.filter((item) => !item.failed).map(({ role, content }) => ({ role, content })).slice(-10)
  messages.value.push({ role: 'user', content: value }, { role: 'assistant', content: '' })
  question.value = ''; loading.value = true; stage.value = '正在连接本地后端'; controller.value = new AbortController(); scrollToLatest()
  try {
    const response = await fetch(`${API_BASE_URL}/api/ai/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token') ?? ''}` },
      body: JSON.stringify({ question: value, history }),
      signal: controller.value.signal,
    })
    if (!response.ok || !response.body) { const detail = await response.json().catch(() => ({})); throw new Error(detail.detail ?? '聊天请求失败') }
    const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''
    while (true) {
      const { done, value: chunk } = await reader.read(); if (done) break
      buffer += decoder.decode(chunk, { stream: true }); const blocks = buffer.split(/\r?\n\r?\n/); buffer = blocks.pop() ?? ''; blocks.forEach(handleEvent)
    }
    if (buffer.trim()) handleEvent(buffer)
  } catch (error: any) {
    if (error.name !== 'AbortError') { const answer = messages.value[messages.value.length - 1]; if (answer) { answer.content = error.message || '请求失败，请稍后重试。'; answer.failed = true } }
  } finally { loading.value = false; stage.value = ''; controller.value = null; scrollToLatest() }
}
function stop() { controller.value?.abort(); loading.value = false; stage.value = '已停止生成' }
function retry(index: number) { const previous = messages.value[index - 1]; if (previous?.role !== 'user') return; messages.value.splice(index - 1, 2); send(previous.content) }
function clearChat() { if (!loading.value) messages.value = [] }
</script>

<template>
  <section class="chat-panel" aria-label="AI团务助手">
    <header class="chat-header"><div><span class="module-icon purple"><ChatDotRound /></span><div><p class="eyebrow">DeepSeek + 本班知识库</p><h2>AI 团务助手</h2></div></div><button class="icon-action" type="button" aria-label="清空聊天" :disabled="loading || !messages.length" @click="clearChat"><Delete /></button></header>
    <div ref="chatBody" class="chat-body" aria-live="polite">
      <div v-if="!messages.length" class="chat-empty"><strong>今天想处理什么团务工作？</strong><p>直接提问，或从下面的示例开始。</p><div><button v-for="item in examples" :key="item" type="button" @click="send(item)">{{ item }}</button></div></div>
      <article v-for="(message, index) in messages" :key="index" :class="['chat-message', message.role, { error: message.failed }]">
        <span>{{ message.role === 'user' ? '你' : 'AI' }}</span><div><p>{{ message.content || (loading && index === messages.length - 1 ? '正在思考…' : '') }}</p><ul v-if="message.sources?.length" class="chat-sources"><li v-for="source in message.sources" :key="source.label"><strong>[{{ source.label }}]</strong> {{ source.filename }} · {{ source.heading || '未命名章节' }} · 第{{ source.page }}页</li></ul><button v-if="message.failed" class="retry-button" type="button" @click="retry(index)"><RefreshRight />重新发送</button></div>
      </article>
    </div>
    <p v-if="stage" class="chat-stage" role="status">{{ stage }}</p>
    <div class="chat-composer"><textarea v-model="question" rows="3" maxlength="2000" aria-label="输入团务问题" placeholder="输入问题，Enter发送，Shift+Enter换行" @keydown.enter.exact.prevent="send()"></textarea><button v-if="loading" class="send-button stop" type="button" aria-label="停止生成" @click="stop"><Close /></button><button v-else class="send-button" type="button" aria-label="发送问题" :disabled="!question.trim()" @click="send()"><Promotion /></button></div>
    <p class="chat-disclaimer">知识库回答会显示引用；没有可靠资料时仅提供通用建议，请以学校和学院正式文件为准。</p>
  </section>
</template>
