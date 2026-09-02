import { http } from './http'

export type KnowledgeStatus = 'pending' | 'processing' | 'done' | 'failed'
export type IndexStatus = 'pending' | 'indexing' | 'indexed' | 'failed'

export interface KnowledgeSmallChunk {
  id: number
  content: string
  char_count: number
}

export interface KnowledgeParentChunk {
  id: number
  content: string
  heading: string
  section_path: string
  page: number
  char_count: number
  smalls: KnowledgeSmallChunk[]
}

export interface KnowledgeDocument {
  id: number
  filename: string
  file_type: string
  status: KnowledgeStatus
  error_message?: string
  page_count: number
  parent_count: number
  small_count: number
  enabled: boolean
  index_status: IndexStatus
  index_error?: string
  indexed_at?: string
  created_at: string
  updated_at: string
}

export interface KnowledgeDetail extends KnowledgeDocument {
  parents: KnowledgeParentChunk[]
}

export async function uploadKnowledge(file: File) {
  const data = new FormData()
  data.append('file', file)
  return (await http.post<KnowledgeDocument>('/api/knowledge', data, { timeout: 60 * 1000 })).data
}

export async function fetchKnowledgeDocuments() {
  return (await http.get<KnowledgeDocument[]>('/api/knowledge')).data
}

export async function fetchKnowledgeDetail(id: number) {
  return (await http.get<KnowledgeDetail>(`/api/knowledge/${id}`)).data
}

export async function retryKnowledge(id: number) {
  return (await http.post<KnowledgeDocument>(`/api/knowledge/${id}/retry`)).data
}

export async function reindexKnowledge(id: number) {
  return (await http.post<KnowledgeDocument>(`/api/knowledge/${id}/reindex`)).data
}

export interface RecallItem {
  chunk_id?: number; document_id: number; parent_id: number; content: string; filename: string
  heading: string; section_path: string; page: number; rank: number; score?: number
  vector_rank?: number; bm25_rank?: number; rrf_score?: number; rerank_score?: number; source_label?: string
}

export async function debugKnowledgeSearch(query: string) {
  return (await http.post<{ vector: RecallItem[]; bm25: RecallItem[]; rrf: RecallItem[]; rerank: RecallItem[]; parents: RecallItem[] }>('/api/rag/search/debug', { query }, { timeout: 180000 })).data
}

export async function toggleKnowledge(id: number, enabled: boolean) {
  return (await http.patch<KnowledgeDocument>(`/api/knowledge/${id}/enabled`, { enabled })).data
}

export async function deleteKnowledge(id: number) {
  await http.delete(`/api/knowledge/${id}`)
}
