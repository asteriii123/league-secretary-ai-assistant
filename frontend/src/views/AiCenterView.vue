<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ChatDotRound, Close, Delete, Document, FolderOpened, Menu, Plus, Promotion, RefreshRight, UploadFilled } from '@element-plus/icons-vue'
import AppShell from '@/components/AppShell.vue'
import MarkdownContent from '@/components/MarkdownContent.vue'
import { useAuthStore } from '@/stores/auth'
import {
  confirmMinutes, createConversation, createMeetingJob, deleteConversation, downloadMeetingDocument,
  fetchConversations, fetchMeetingJob, fetchMessages, renameConversation, resumeTranscript, retryMeetingJob, streamQuestion,
  type ChatMessage, type Conversation, type MeetingJob, type MeetingMinutes,
} from '@/api/conversations'

const auth = useAuthStore()
const conversations = ref<Conversation[]>([]); const active = ref<Conversation>(); const messages = ref<ChatMessage[]>([])
const jobs = ref<Record<number, MeetingJob>>({}); const question = ref(''); const loading = ref(false); const stage = ref(''); const error = ref('')
const controller = ref<AbortController>(); const chatBody = ref<HTMLElement>(); const drawerOpen = ref(false)
const meetingFile = ref<File>(); let pollTimer: number | undefined
const role = computed(() => auth.role as 'secretary' | 'student')
const examples = computed(() => role.value === 'secretary' ? ['根据本班资料，团费应该如何缴纳？', '帮我查找主题团日的流程要求'] : ['入党申请书一般包含哪些内容？', '团员需要履行哪些义务？'])

async function scrollLatest() { await nextTick(); chatBody.value?.scrollTo({ top: chatBody.value.scrollHeight, behavior: 'smooth' }) }
async function loadConversations(selectId?: number) {
  conversations.value = await fetchConversations()
  const target = conversations.value.find(item => item.id === (selectId ?? active.value?.id)) ?? conversations.value[0]
  if (target) await selectConversation(target)
}
async function selectConversation(item: Conversation) {
  active.value = item; drawerOpen.value = false; messages.value = await fetchMessages(item.id); await loadJobs(); scrollLatest()
}
async function newConversation() {
  const item = await createConversation(); conversations.value.unshift(item); await selectConversation(item)
}
async function removeConversation(item: Conversation) {
  if (!confirm(`确定删除“${item.title}”的聊天记录吗？已生成的会议文档不会被删除。`)) return
  await deleteConversation(item.id); active.value = undefined; messages.value = []; await loadConversations()
}
async function editConversation(item: Conversation) { const title = prompt('输入新的对话名称', item.title)?.trim(); if (!title || title === item.title) return; const saved = await renameConversation(item.id, title); Object.assign(item, saved); if (active.value?.id === item.id) Object.assign(active.value, saved) }
async function ensureConversation() {
  if (!active.value) await newConversation()
  return active.value!
}
function handleEvent(block: string, answer: ChatMessage) {
  const event = block.match(/^event: (.+)$/m)?.[1]; const text = block.match(/^data: (.+)$/m)?.[1]
  if (!event || !text) return
  const data = JSON.parse(text)
  if (event === 'content') answer.content += data.text
  if (event === 'sources') answer.sources = data.items
  if (event === 'status') stage.value = data.message
  if (event === 'message') answer.id = data.assistant_message_id
  if (event === 'error') { answer.content = data.message; answer.status = 'failed' }
  scrollLatest()
}
async function send(text = question.value) {
  const value = text.trim(); if ((!value && !meetingFile.value) || loading.value) return
  try {
    if (meetingFile.value) { await uploadMeeting(value); return }
    const conversation = await ensureConversation()
    const now = new Date().toISOString(); const answer: ChatMessage = { id: -Date.now(), role: 'assistant', content: '', status: 'streaming', sources: [], created_at: now }
    messages.value.push({ id: answer.id - 1, role: 'user', content: value, status: 'complete', sources: [], created_at: now }, answer)
    question.value = ''; loading.value = true; stage.value = '正在连接本地后端'; error.value = ''; controller.value = new AbortController(); scrollLatest()
    const response = await streamQuestion(conversation.id, value, controller.value.signal)
    if (!response.ok || !response.body) { const detail = await response.json().catch(() => ({})); throw new Error(detail.detail ?? '聊天请求失败') }
    const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''
    while (true) { const chunk = await reader.read(); if (chunk.done) break; buffer += decoder.decode(chunk.value, { stream: true }); const blocks = buffer.split(/\r?\n\r?\n/); buffer = blocks.pop() ?? ''; blocks.forEach(item => handleEvent(item, answer)) }
    if (buffer.trim()) handleEvent(buffer, answer)
    await loadConversations(conversation.id)
  } catch (cause: any) {
    if (cause.name !== 'AbortError') { error.value = cause.message || '请求失败'; const answer = messages.value[messages.value.length - 1]; if (answer?.role === 'assistant') { answer.content = error.value; answer.status = 'failed' } }
  } finally { loading.value = false; stage.value = ''; controller.value = undefined }
}
function stop() { controller.value?.abort(); loading.value = false; stage.value = '已停止生成' }
function retryMessage(index: number) { const previous = messages.value[index - 1]; if (previous?.role === 'user') send(previous.content) }
async function uploadMeeting(instruction = question.value.trim()) {
  if (!meetingFile.value) return
  try {
    const conversation = await ensureConversation()
    loading.value = true; error.value = ''; await createMeetingJob(conversation.id, instruction || '请整理为标准会议纪要', meetingFile.value)
    meetingFile.value = undefined; question.value = ''; await loadConversations(conversation.id)
  } catch (cause: any) { error.value = cause.response?.data?.detail ?? cause.message ?? '上传失败' } finally { loading.value = false }
}
async function loadJobs() {
  const ids = [...new Set(messages.value.map(item => item.meeting_job_id).filter((id): id is number => Boolean(id)))]
  const results = await Promise.all(ids.map(id => fetchMeetingJob(id).catch(() => undefined)))
  for (const job of results) if (job) jobs.value[job.id] = job
}
async function approveTranscript(job: MeetingJob) { await resumeTranscript(job.id, job.transcript); job.status = 'filtering' }
async function approveMinutes(job: MeetingJob) { await confirmMinutes(job.id, job.minutes as MeetingMinutes); job.status = 'creating_document' }
async function retryJob(job: MeetingJob) { await retryMeetingJob(job.id); job.status = 'queued' }
function jobLabel(status: string) { return ({ queued: '等待处理', transcribing: '本地转写中', awaiting_transcript_review: '等待确认转写稿', filtering: '脱敏与去冗余中', generating_minutes: '生成纪要中', awaiting_minutes_review: '等待确认纪要', creating_document: '生成Word中', complete: '已完成', failed: '处理失败' } as Record<string,string>)[status] ?? status }
async function pollJobs() {
  const pending = Object.values(jobs.value).filter(job => !['complete', 'failed', 'awaiting_transcript_review', 'awaiting_minutes_review'].includes(job.status))
  for (const item of pending) jobs.value[item.id] = await fetchMeetingJob(item.id).catch(() => item)
}
onMounted(async () => { await loadConversations(); pollTimer = window.setInterval(pollJobs, 2500) })
onBeforeUnmount(() => { if (pollTimer) window.clearInterval(pollTimer); controller.value?.abort() })
</script>

<template>
  <AppShell :role-label="role === 'secretary' ? '团支书端' : '学生端'" active-label="AI 助手">
    <section class="ai-center">
      <aside :class="['conversation-sidebar', { open: drawerOpen }]">
        <header><strong>历史对话</strong><button class="icon-action mobile-only" aria-label="关闭历史对话" @click="drawerOpen = false"><Close /></button></header>
        <button class="primary-action" @click="newConversation"><Plus />新建对话</button>
        <div class="conversation-list"><div v-for="item in conversations" :key="item.id" :class="['conversation-row', { active: active?.id === item.id }]"><button class="conversation-select" title="双击标题可重命名" @click="selectConversation(item)"><span><ChatDotRound /></span><div><strong @dblclick.stop="editConversation(item)">{{ item.title }}</strong><small>最近更新 {{ new Date(item.updated_at).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }}</small></div></button><button class="conversation-delete" :aria-label="`删除对话：${item.title}`" @click="removeConversation(item)"><Delete /></button></div></div>
        <RouterLink v-if="role === 'secretary'" class="meeting-doc-link" to="/secretary/meeting-documents"><Document />会议文档</RouterLink>
      </aside>
      <button v-if="drawerOpen" class="drawer-backdrop" aria-label="关闭历史对话" @click="drawerOpen = false"></button>

      <div class="ai-chat-workspace">
        <header class="ai-center-header"><button class="icon-action mobile-only" aria-label="打开历史对话" @click="drawerOpen = true"><Menu /></button><div><p class="eyebrow">DeepSeek + 本班知识库</p><h1>{{ active?.title ?? 'AI 团务助手' }}</h1></div><RouterLink v-if="role === 'secretary'" class="secondary-action" to="/secretary/knowledge"><FolderOpened />管理知识库</RouterLink></header>
        <p v-if="error" class="error-message" role="alert">{{ error }}</p>
        <div :class="['ai-dialog-body', { 'is-empty': !messages.length }]">
        <div ref="chatBody" class="ai-center-messages" aria-live="polite">
          <div v-if="!messages.length" class="chat-empty"><strong>今天需要 AI 帮你处理什么？</strong><p>{{ role === 'secretary' ? '直接提问会检索本班资料；添加音视频会自动整理会议纪要。' : '直接提问，回答会结合本班已启用的知识资料。' }}</p></div>
          <article v-for="(message, messageIndex) in messages" :key="message.id" :class="['chat-message', message.role, { error: message.status === 'failed', 'has-meeting': message.role === 'assistant' && message.meeting_job_id }]">
            <span>{{ message.role === 'user' ? '你' : 'AI' }}</span><div>
              <p v-if="message.role === 'user'">{{ message.content }}</p><MarkdownContent v-else :content="message.content || '正在思考…'" />
              <ul v-if="message.sources?.length" class="chat-sources"><li v-for="source in message.sources" :key="source.label"><strong>[{{ source.label }}]</strong> {{ source.filename }} · {{ source.heading || '未命名章节' }} · 第{{ source.page }}页</li></ul>
              <button v-if="message.role === 'assistant' && message.status === 'failed' && !message.meeting_job_id" class="retry-button" @click="retryMessage(messageIndex)"><RefreshRight />重新生成</button>
              <section v-if="message.role === 'assistant' && message.meeting_job_id && jobs[message.meeting_job_id]" class="meeting-job-card">
                <header><strong>{{ jobs[message.meeting_job_id]!.source_name }}</strong><span>{{ jobLabel(jobs[message.meeting_job_id]!.status) }}</span></header>
                <p v-if="jobs[message.meeting_job_id]!.error_message" class="error-message">{{ jobs[message.meeting_job_id]!.error_message }}</p>
                <template v-if="jobs[message.meeting_job_id]!.status === 'awaiting_transcript_review'"><label>请检查并修改转写稿<textarea v-model="jobs[message.meeting_job_id]!.transcript" rows="10"></textarea></label><button class="primary-action" @click="approveTranscript(jobs[message.meeting_job_id]!)">确认转写稿，继续处理</button></template>
                <template v-if="jobs[message.meeting_job_id]!.status === 'awaiting_minutes_review'"><label>纪要标题<input v-model="jobs[message.meeting_job_id]!.minutes.title" /></label><label>会议摘要<textarea v-model="jobs[message.meeting_job_id]!.minutes.summary" rows="4"></textarea></label><label>主要内容（每行一项）<textarea :value="jobs[message.meeting_job_id]!.minutes.key_points?.join('\n')" rows="5" @input="jobs[message.meeting_job_id]!.minutes.key_points = ($event.target as HTMLTextAreaElement).value.split('\n').filter(Boolean)"></textarea></label><label>会议决定（每行一项）<textarea :value="jobs[message.meeting_job_id]!.minutes.decisions?.join('\n')" rows="5" @input="jobs[message.meeting_job_id]!.minutes.decisions = ($event.target as HTMLTextAreaElement).value.split('\n').filter(Boolean)"></textarea></label><button class="primary-action" @click="approveMinutes(jobs[message.meeting_job_id]!)">确认纪要并生成Word</button></template>
                <button v-if="jobs[message.meeting_job_id]!.status === 'failed'" class="secondary-action" @click="retryJob(jobs[message.meeting_job_id]!)"><RefreshRight />重试</button>
                <button v-if="jobs[message.meeting_job_id]!.download_ready" class="primary-action" @click="downloadMeetingDocument(jobs[message.meeting_job_id]!.id, `${jobs[message.meeting_job_id]!.source_name}-会议纪要.docx`)"><Document />下载Word纪要</button>
              </section>
            </div>
          </article>
        </div>
        <p v-if="stage" class="chat-stage">{{ stage }}</p>
        <div class="unified-composer"><div v-if="meetingFile" class="attachment-chip"><UploadFilled /><span>{{ meetingFile.name }}</span><button type="button" aria-label="移除附件" @click="meetingFile = undefined"><Close /></button></div><div class="composer-row"><label v-if="role === 'secretary'" class="attachment-button" title="添加音频或视频"><UploadFilled /><span class="sr-only">添加音频或视频</span><input type="file" accept="audio/*,video/*,.mkv" @change="meetingFile = ($event.target as HTMLInputElement).files?.[0]" /></label><textarea v-model="question" rows="3" maxlength="2000" aria-label="输入问题或会议整理要求" :placeholder="role === 'secretary' ? '输入问题，或添加音视频并填写整理要求；Enter发送' : '输入问题，Enter发送，Shift+Enter换行'" @keydown.enter.exact.prevent="send()"></textarea><button v-if="loading && !meetingFile" class="send-button stop" aria-label="停止生成" @click="stop"><Close /></button><button v-else class="send-button" aria-label="发送" :disabled="!question.trim() && !meetingFile" @click="send()"><Promotion /></button></div></div>
        <div v-if="!messages.length" class="empty-suggestions"><button v-for="item in examples" :key="item" @click="send(item)">{{ item }}</button></div>
        </div>
        <p class="chat-disclaimer">知识库依据不足时只提供通用建议，请以学校和学院正式文件为准。</p>
      </div>
    </section>
  </AppShell>
</template>
