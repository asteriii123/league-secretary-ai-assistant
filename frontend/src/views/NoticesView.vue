<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, Bell, Close, Delete, Download, EditPen, MagicStick, Plus, User } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { createNotice, deleteNotice, downloadNoticeAttachment, fetchNoticeReaders, fetchNotices, generateNoticeDraft, markNoticeRead, updateNotice, type Notice, type NoticeForm } from '@/api/notices'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore(); const router = useRouter(); const notices = ref<Notice[]>([]); const loading = ref(false); const error = ref(''); const editorOpen = ref(false); const editingId = ref<number>(); const selected = ref<Notice>(); const attachment = ref<File>(); const aiTopic = ref(''); const aiLoading = ref(false); const readers = ref<{ read: { display_name: string }[]; unread: { display_name: string }[] }>()
const form = ref<NoticeForm>({ title: '', content: '', status: 'draft', deadline: '' })
const unreadCount = computed(() => notices.value.filter((item) => !item.is_read).length)
const statusText: Record<string, string> = { draft: '草稿', published: '已发布', withdrawn: '已撤回' }
async function load() { loading.value = true; error.value = ''; try { notices.value = await fetchNotices() } catch (e: any) { error.value = e.response?.data?.detail ?? '通知加载失败' } finally { loading.value = false } }
function openCreate() { editingId.value = undefined; form.value = { title: '', content: '', status: 'draft', deadline: '' }; attachment.value = undefined; aiTopic.value = ''; editorOpen.value = true }
function openEdit(item: Notice) { editingId.value = item.id; form.value = { title: item.title, content: item.content, status: item.status, deadline: item.deadline ?? '' }; attachment.value = undefined; editorOpen.value = true }
async function save() { try { const payload = { ...form.value, attachment: attachment.value }; if (editingId.value) await updateNotice(editingId.value, payload); else await createNotice(payload); editorOpen.value = false; await load() } catch (e: any) { error.value = e.response?.data?.detail ?? '通知保存失败' } }
async function changeStatus(item: Notice, status: Notice['status']) { await updateNotice(item.id, { title: item.title, content: item.content, deadline: item.deadline ?? '', status }); await load() }
async function remove(item: Notice) { if (!confirm(`确定删除“${item.title}”吗？`)) return; await deleteNotice(item.id); selected.value = undefined; await load() }
async function openDetail(item: Notice) { selected.value = item; readers.value = undefined; if (auth.role === 'student' && !item.is_read) { await markNoticeRead(item.id); item.is_read = true } }
async function showReaders(item: Notice) { readers.value = await fetchNoticeReaders(item.id); selected.value = item }
async function aiDraft() { if (aiTopic.value.trim().length < 2) return; aiLoading.value = true; try { const draft = await generateNoticeDraft(aiTopic.value); form.value.title = draft.title; form.value.content = draft.content } catch (e: any) { error.value = e.response?.data?.detail ?? 'AI起草失败' } finally { aiLoading.value = false } }
onMounted(load)
</script>

<template>
  <AppShell :role-label="auth.role === 'secretary' ? '团支书端' : '学生端'" active-label="通知管理">
    <button class="back-link" type="button" @click="router.push(auth.role === 'secretary' ? '/secretary' : '/student')"><ArrowLeft />返回工作台</button>
    <section class="tool-heading"><span class="module-icon coral"><Bell /></span><div><p class="eyebrow">班级协作</p><h1>通知管理</h1><p>{{ auth.role === 'secretary' ? '发布通知并查看学生阅读情况。' : `查看本班通知，目前有 ${unreadCount} 条未读。` }}</p></div></section>
    <p v-if="error" class="error-message" role="alert">{{ error }}</p>
    <div class="notice-toolbar"><div><strong>{{ notices.length }}</strong><span>条通知</span></div><button v-if="auth.role === 'secretary'" class="primary-action" type="button" @click="openCreate"><Plus />新建通知</button></div>
    <section class="notice-layout">
      <div class="notice-list" :aria-busy="loading">
        <button v-for="item in notices" :key="item.id" :class="['notice-list-item', { active: selected?.id === item.id, unread: auth.role === 'student' && !item.is_read }]" type="button" @click="openDetail(item)"><span :class="['status-chip', item.status]">{{ statusText[item.status] }}</span><strong>{{ item.title }}</strong><p>{{ item.content }}</p><small>{{ new Date(item.created_at).toLocaleString() }}<template v-if="auth.role === 'secretary'"> · 已读 {{ item.read_count }}/{{ item.student_count }}</template></small></button>
        <p v-if="loading" class="empty-copy">正在加载通知…</p><p v-else-if="!notices.length" class="empty-copy">暂时没有通知。</p>
      </div>
      <article v-if="selected" class="notice-detail"><div class="notice-detail-heading"><div><span :class="['status-chip', selected.status]">{{ statusText[selected.status] }}</span><h2>{{ selected.title }}</h2></div><button class="icon-action" aria-label="关闭详情" @click="selected = undefined"><Close /></button></div><p class="notice-content">{{ selected.content }}</p><dl><div><dt>发布时间</dt><dd>{{ new Date(selected.created_at).toLocaleString() }}</dd></div><div><dt>截止时间</dt><dd>{{ selected.deadline ? new Date(selected.deadline).toLocaleString() : '未设置' }}</dd></div></dl><button v-if="selected.attachment_name" class="secondary-action" @click="downloadNoticeAttachment(selected)"><Download />下载 {{ selected.attachment_name }}</button>
        <div v-if="auth.role === 'secretary'" class="detail-actions"><button class="secondary-action" @click="openEdit(selected)"><EditPen />编辑</button><button v-if="selected.status !== 'published'" class="primary-action" @click="changeStatus(selected, 'published')">发布</button><button v-if="selected.status === 'published'" class="secondary-action" @click="changeStatus(selected, 'withdrawn')">撤回</button><button class="secondary-action" @click="showReaders(selected)"><User />阅读情况</button><button class="danger-action" @click="remove(selected)"><Delete />删除</button></div>
        <div v-if="readers" class="reader-grid"><div><h3>已读（{{ readers.read.length }}）</h3><p v-for="item in readers.read" :key="item.display_name">{{ item.display_name }}</p><small v-if="!readers.read.length">暂无</small></div><div><h3>未读（{{ readers.unread.length }}）</h3><p v-for="item in readers.unread" :key="item.display_name">{{ item.display_name }}</p><small v-if="!readers.unread.length">暂无</small></div></div>
      </article><div v-else class="notice-placeholder"><Bell /><p>选择一条通知查看详情</p></div>
    </section>
    <div v-if="editorOpen" class="modal-backdrop" @click.self="editorOpen = false"><section class="editor-modal" role="dialog" aria-modal="true" aria-labelledby="notice-editor-title"><header><div><p class="eyebrow">团支书端</p><h2 id="notice-editor-title">{{ editingId ? '编辑通知' : '新建通知' }}</h2></div><button class="icon-action" aria-label="关闭编辑窗口" @click="editorOpen = false"><Close /></button></header><div class="ai-draft-row"><input v-model.trim="aiTopic" placeholder="告诉AI通知主题，例如：周五前收团费" /><button class="secondary-action" :disabled="aiLoading || aiTopic.length < 2" @click="aiDraft"><MagicStick />{{ aiLoading ? '起草中…' : 'AI辅助起草' }}</button></div><label>标题<input v-model.trim="form.title" maxlength="200" /></label><label>正文<textarea v-model.trim="form.content" rows="9"></textarea></label><label>截止时间<input v-model="form.deadline" type="datetime-local" /></label><label>附件<input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png" @change="attachment = ($event.target as HTMLInputElement).files?.[0]" /></label><label>保存状态<select v-model="form.status"><option value="draft">保存草稿</option><option value="published">立即发布</option><option v-if="editingId" value="withdrawn">撤回</option></select></label><footer><button class="secondary-action" @click="editorOpen = false">取消</button><button class="primary-action" :disabled="!form.title || !form.content" @click="save">保存通知</button></footer></section></div>
  </AppShell>
</template>
