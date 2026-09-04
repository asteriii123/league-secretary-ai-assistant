import { API_BASE_URL, http } from './http'

export type Source =
  | { type?: 'knowledge'; label: string; filename: string; heading: string; page: number }
  | { type: 'web'; label: string; title: string; url: string; domain: string; provider: 'tavily' | 'baidu' }
export interface Conversation { id: number; title: string; mode?: string; created_at: string; updated_at: string }
export interface ChatMessage { id: number; role: 'user' | 'assistant'; content: string; status: string; sources: Source[]; meeting_job_id?: number; created_at: string }
export interface MeetingMinutes { title: string; meeting_type: string; summary: string; key_points: string[]; decisions: string[]; action_items: { task: string; owner: string; deadline: string }[]; requires_manual_review: boolean; redacted_sensitive_data: boolean }
export interface MeetingJob { id: number; conversation_id: number; meeting_type: string; instruction: string; status: string; source_name: string; transcript: string; filtered_transcript: string; minutes: Partial<MeetingMinutes>; download_ready: boolean; error_message?: string }

export async function fetchConversations() { return (await http.get<Conversation[]>('/api/ai/conversations')).data }
export async function createConversation() { return (await http.post<Conversation>('/api/ai/conversations')).data }
export async function renameConversation(id: number, title: string) { return (await http.patch<Conversation>(`/api/ai/conversations/${id}`, { title })).data }
export async function deleteConversation(id: number) { await http.delete(`/api/ai/conversations/${id}`) }
export async function fetchMessages(id: number) { return (await http.get<ChatMessage[]>(`/api/ai/conversations/${id}/messages`)).data }

export async function streamQuestion(id: number, question: string, webSearchEnabled: boolean, signal: AbortSignal) {
  return fetch(`${API_BASE_URL}/api/ai/conversations/${id}/messages/stream`, {
    method: 'POST', signal,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token') ?? ''}` },
    body: JSON.stringify({ question, web_search_enabled: webSearchEnabled }),
  })
}

export async function createMeetingJob(conversationId: number, instruction: string, file: File) {
  const body = new FormData(); body.append('conversation_id', String(conversationId)); body.append('instruction', instruction); body.append('file', file)
  return (await http.post<MeetingJob>('/api/ai/meeting-jobs', body, { timeout: 60 * 60 * 1000 })).data
}
export async function fetchMeetingJob(id: number) { return (await http.get<MeetingJob>(`/api/ai/meeting-jobs/${id}`)).data }
export async function resumeTranscript(id: number, transcript: string) { return (await http.post<MeetingJob>(`/api/ai/meeting-jobs/${id}/resume-transcript`, { transcript })).data }
export async function confirmMinutes(id: number, minutes: MeetingMinutes) { return (await http.post<MeetingJob>(`/api/ai/meeting-jobs/${id}/confirm-minutes`, minutes)).data }
export async function retryMeetingJob(id: number) { return (await http.post<MeetingJob>(`/api/ai/meeting-jobs/${id}/retry`)).data }
export async function downloadMeetingDocument(id: number, filename: string) {
  const response = await http.get(`/api/ai/meeting-jobs/${id}/document`, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data); const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url)
}
