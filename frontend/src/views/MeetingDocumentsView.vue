<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ArrowLeft, Delete, DocumentChecked } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { deleteMeetingRecord, downloadMeetingRecord, fetchMeetingRecords, type MeetingRecord } from '@/api/meetings'

const router = useRouter(); const records = ref<MeetingRecord[]>([]); const selected = ref<MeetingRecord>(); const error = ref('')
async function load() { try { records.value = await fetchMeetingRecords() } catch (cause: any) { error.value = cause.response?.data?.detail ?? '加载失败' } }
async function remove(record: MeetingRecord) { if (!confirm(`确定删除“${record.title}”吗？`)) return; await deleteMeetingRecord(record.id); if (selected.value?.id === record.id) selected.value = undefined; await load() }
onMounted(load)
</script>

<template>
  <AppShell role-label="团支书端" active-label="会议文档">
    <button class="back-link" type="button" @click="router.push('/secretary/ai')"><ArrowLeft />返回 AI 助手</button>
    <section class="tool-heading"><span class="module-icon green"><DocumentChecked /></span><div><p class="eyebrow">SQLite 本地保存</p><h1>会议文档</h1><p>查看旧纪要和 AI 助手新生成的纪要，或下载 Word。</p></div></section>
    <p v-if="error" class="error-message">{{ error }}</p>
    <section class="notice-layout">
      <div class="notice-list"><button v-for="record in records" :key="record.id" :class="['notice-list-item', { active: selected?.id === record.id }]" @click="selected = record"><strong>{{ record.title }}</strong><p>{{ record.summary }}</p><small>{{ record.meeting_type }} · {{ new Date(record.updated_at).toLocaleString() }}</small></button><p v-if="!records.length" class="empty-copy">还没有会议文档。</p></div>
      <article v-if="selected" class="notice-detail"><div class="notice-detail-heading"><div><span class="status-chip published">{{ selected.meeting_type }}</span><h2>{{ selected.title }}</h2></div></div><h3>会议摘要</h3><p class="notice-content">{{ selected.summary }}</p><h3>主要内容</h3><ul><li v-for="item in selected.key_points" :key="item">{{ item }}</li></ul><h3>会议决定</h3><ul><li v-for="item in selected.decisions" :key="item">{{ item }}</li></ul><div class="detail-actions"><button class="primary-action" @click="downloadMeetingRecord(selected.id, selected.title)"><DocumentChecked />下载Word</button><button class="danger-action" @click="remove(selected)"><Delete />删除</button></div></article>
      <div v-else class="notice-placeholder"><DocumentChecked /><p>选择一份纪要查看详情。</p></div>
    </section>
  </AppShell>
</template>
