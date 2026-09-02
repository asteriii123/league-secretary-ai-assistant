<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, Close, Delete, FolderOpened, Refresh, UploadFilled, View, VideoPlay } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { debugKnowledgeSearch, deleteKnowledge, fetchKnowledgeDetail, fetchKnowledgeDocuments, reindexKnowledge, retryKnowledge, toggleKnowledge, uploadKnowledge, type KnowledgeDetail, type KnowledgeDocument, type RecallItem } from '@/api/knowledge'

const router = useRouter()
const documents = ref<KnowledgeDocument[]>([])
const loading = ref(false)
const error = ref('')
const file = ref<File>()
const uploading = ref(false)
const detail = ref<KnowledgeDetail>()
const detailOpen = ref(false)
const query = ref('')
const searching = ref(false)
const searchResults = ref<{ vector: RecallItem[]; bm25: RecallItem[]; rrf: RecallItem[] }>()
const resultTab = ref<'rrf' | 'vector' | 'bm25'>('rrf')

const typeText: Record<string, string> = { pdf: 'PDF', word: 'Word', ppt: 'PPT', txt: 'TXT' }
const statusText: Record<string, string> = { pending: '待处理', processing: '解析中', done: '已完成', failed: '失败' }
const indexText: Record<string, string> = { pending: '待索引', indexing: '索引中', indexed: '索引完成', failed: '索引失败' }
const pendingCount = computed(() => documents.value.filter((item) => item.status === 'pending' || item.status === 'processing').length)

async function load() {
  loading.value = true
  error.value = ''
  try {
    documents.value = await fetchKnowledgeDocuments()
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? '知识资料加载失败'
  } finally {
    loading.value = false
  }
}

async function upload() {
  if (!file.value) return
  uploading.value = true
  error.value = ''
  try {
    const document = await uploadKnowledge(file.value)
    file.value = undefined
    await load()
    void watchDocument(document.id)
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? '上传失败'
  } finally {
    uploading.value = false
  }
}

async function watchDocument(id: number) {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 2000))
    await load()
    const target = documents.value.find((item) => item.id === id)
    if (!target || target.status === 'failed' || (target.status === 'done' && (target.index_status === 'indexed' || target.index_status === 'failed'))) return
  }
}

async function openDetail(item: KnowledgeDocument) {
  error.value = ''
  try {
    detail.value = await fetchKnowledgeDetail(item.id)
    detailOpen.value = true
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? '详情加载失败'
  }
}

async function retry(item: KnowledgeDocument) {
  error.value = ''
  try {
    const updated = await retryKnowledge(item.id)
    const index = documents.value.findIndex((doc) => doc.id === item.id)
    if (index >= 0) documents.value[index] = updated
    void watchDocument(item.id)
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? '重试失败'
  }
}

async function reindex(item: KnowledgeDocument) {
  error.value = ''
  try {
    const updated = await reindexKnowledge(item.id)
    const index = documents.value.findIndex((doc) => doc.id === item.id)
    if (index >= 0) documents.value[index] = updated
    void watchDocument(item.id)
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? '重新索引失败'
  }
}

async function search() {
  if (query.value.trim().length < 2) return
  searching.value = true; error.value = ''; searchResults.value = undefined
  try { searchResults.value = await debugKnowledgeSearch(query.value.trim()) }
  catch (e: any) { error.value = e.response?.data?.detail ?? '混合检索失败' }
  finally { searching.value = false }
}

async function toggle(item: KnowledgeDocument) {
  error.value = ''
  try {
    const updated = await toggleKnowledge(item.id, !item.enabled)
    const index = documents.value.findIndex((doc) => doc.id === item.id)
    if (index >= 0) documents.value[index] = updated
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? '操作失败'
  }
}

async function remove(item: KnowledgeDocument) {
  if (!confirm(`确定删除“${item.filename}”及其索引吗？`)) return
  await deleteKnowledge(item.id)
  if (detail.value?.id === item.id) detailOpen.value = false
  await load()
}

onMounted(load)
</script>

<template>
  <AppShell role-label="团支书端" active-label="知识资料">
    <button class="back-link" type="button" @click="router.push('/secretary')"><ArrowLeft />返回团支书工作台</button>
    <section class="tool-heading"><span class="module-icon purple"><FolderOpened /></span><div><p class="eyebrow">解析 · 分块 · 索引</p><h1>知识资料</h1><p>上传PDF、Word、PPT和TXT，本地解析并生成Small-to-Big父子块。</p></div></section>

    <p v-if="error" class="error-message" role="alert">{{ error }}</p>

    <section class="knowledge-upload-card">
      <div class="upload-hint"><UploadFilled /><div><strong>选择本地知识资料</strong><p>支持PDF、Word、PPT、TXT，单文件不超过50MB。Word和PPT会先转成PDF再解析，扫描PDF自动走OCR。</p></div></div>
      <div class="upload-row">
        <input type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.txt" @change="file = ($event.target as HTMLInputElement).files?.[0]" />
        <button class="primary-action" type="button" :disabled="!file || uploading" @click="upload">{{ uploading ? '上传解析中…' : '上传并解析' }}</button>
      </div>
    </section>

    <section class="retrieval-debug-card">
      <div><p class="eyebrow">第七阶段调试</p><h2>混合召回测试</h2><p>查看Chroma向量、BM25全文和RRF融合结果；当前只返回候选小块，不生成AI回答。</p></div>
      <div class="retrieval-search-row"><input v-model.trim="query" placeholder="输入测试问题，例如：团费应如何缴纳？" @keyup.enter="search" /><button class="primary-action" :disabled="query.length < 2 || searching" @click="search">{{ searching ? '召回中…' : '开始检索' }}</button></div>
      <template v-if="searchResults"><div class="mode-tabs retrieval-tabs"><button :class="{ active: resultTab === 'rrf' }" @click="resultTab = 'rrf'">RRF融合（{{ searchResults.rrf.length }}）</button><button :class="{ active: resultTab === 'vector' }" @click="resultTab = 'vector'">向量（{{ searchResults.vector.length }}）</button><button :class="{ active: resultTab === 'bm25' }" @click="resultTab = 'bm25'">BM25（{{ searchResults.bm25.length }}）</button></div><div class="recall-results"><article v-for="item in searchResults[resultTab]" :key="item.chunk_id"><header><strong>#{{ item.rank }} {{ item.filename }}</strong><span>第{{ item.page }}页</span></header><p>{{ item.content }}</p><small v-if="resultTab === 'rrf'">向量排名 {{ item.vector_rank ?? '—' }} · BM25排名 {{ item.bm25_rank ?? '—' }} · RRF {{ item.rrf_score }}</small><small v-else>得分 {{ item.score }}</small></article><p v-if="!searchResults[resultTab].length" class="empty-copy">这一路没有召回结果。</p></div></template>
    </section>

    <div class="notice-toolbar">
      <div><strong>{{ documents.length }}</strong><span>份资料</span><template v-if="pendingCount"><span class="processing-hint">{{ pendingCount }} 份处理中</span></template></div>
      <button class="secondary-action" type="button" :disabled="loading" @click="load"><Refresh />刷新状态</button>
    </div>

    <section class="saved-meetings" :aria-busy="loading">
      <div class="saved-meeting-grid knowledge-grid">
        <article v-for="item in documents" :key="item.id">
          <header><span :class="['status-chip', item.status]">{{ statusText[item.status] }}</span><span :class="['status-chip', item.index_status]">{{ indexText[item.index_status] }}</span><span class="file-type-chip">{{ typeText[item.file_type] ?? item.file_type }}</span></header>
          <h3>{{ item.filename }}</h3>
          <dl class="knowledge-meta"><div><dt>页码</dt><dd>{{ item.page_count }}</dd></div><div><dt>父块</dt><dd>{{ item.parent_count }}</dd></div><div><dt>小块</dt><dd>{{ item.small_count }}</dd></div></dl>
          <p v-if="item.status === 'failed'" class="error-message">{{ item.error_message }}</p>
          <p v-else-if="item.status === 'pending' || item.status === 'processing'" class="empty-copy">正在解析，请稍候…</p>
          <p v-else-if="item.index_status === 'failed'" class="error-message">{{ item.index_error }}</p>
          <p v-else-if="item.index_status === 'pending' || item.index_status === 'indexing'" class="empty-copy">正在建立检索索引…</p>
          <footer>
            <button class="secondary-action" :disabled="item.status === 'pending' || item.status === 'processing'" @click="openDetail(item)"><View />查看分块</button>
            <button v-if="item.status === 'failed'" class="primary-action" @click="retry(item)"><VideoPlay />重试</button>
            <button v-if="item.status === 'done' && item.index_status === 'failed'" class="primary-action" @click="reindex(item)"><VideoPlay />重建索引</button>
            <button class="secondary-action" @click="toggle(item)">{{ item.enabled ? '停用' : '启用' }}</button>
            <button class="danger-action" @click="remove(item)"><Delete />删除</button>
          </footer>
        </article>
        <p v-if="!documents.length" class="empty-copy">还没有上传知识资料。</p>
      </div>
    </section>

    <div v-if="detailOpen && detail" class="modal-backdrop" @click.self="detailOpen = false">
      <section class="editor-modal knowledge-detail-modal" role="dialog" aria-modal="true" aria-labelledby="knowledge-detail-title">
        <header><div><p class="eyebrow">父子分块预览</p><h2 id="knowledge-detail-title">{{ detail.filename }}</h2></div><button class="icon-action" aria-label="关闭详情" @click="detailOpen = false"><Close /></button></header>
        <p class="knowledge-summary">共 {{ detail.parent_count }} 个父块、{{ detail.small_count }} 个小块、{{ detail.page_count }} 页。</p>
        <div class="chunk-list">
          <article v-for="parent in detail.parents" :key="parent.id" class="parent-chunk">
            <header><span class="parent-tag">父块</span><strong>{{ parent.heading || '未命名章节' }}</strong><span class="chunk-meta">{{ parent.section_path }}</span><span class="chunk-meta">第 {{ parent.page }} 页 · {{ parent.char_count }} 字</span></header>
            <p class="parent-content">{{ parent.content }}</p>
            <details class="small-chunks">
              <summary>小块（{{ parent.smalls.length }}）— 仅用于检索召回</summary>
              <div v-for="small in parent.smalls" :key="small.id" class="small-chunk">{{ small.content }}<span class="chunk-meta">{{ small.char_count }} 字</span></div>
            </details>
          </article>
        </div>
      </section>
    </div>
  </AppShell>
</template>
