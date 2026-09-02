import { http } from './http'

export type KnowledgeStatus = 'pending' | 'processing' | 'done' | 'failed'

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

export async function toggleKnowledge(id: number, enabled: boolean) {
  return (await http.patch<KnowledgeDocument>(`/api/knowledge/${id}/enabled`, { enabled })).data
}

export async function deleteKnowledge(id: number) {
  await http.delete(`/api/knowledge/${id}`)
}
