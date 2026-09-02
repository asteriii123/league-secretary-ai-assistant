import { http } from './http'

export interface Notice {
  id: number
  title: string
  content: string
  status: 'draft' | 'published' | 'withdrawn'
  deadline?: string
  attachment_name?: string
  read_count: number
  student_count: number
  is_read: boolean
  created_at: string
  updated_at: string
}

export interface NoticeForm {
  title: string
  content: string
  status: Notice['status']
  deadline: string
  attachment?: File
  removeAttachment?: boolean
}

function toFormData(payload: NoticeForm) {
  const form = new FormData()
  form.append('title', payload.title)
  form.append('content', payload.content)
  form.append('status', payload.status)
  if (payload.deadline) form.append('deadline', payload.deadline)
  if (payload.attachment) form.append('attachment', payload.attachment)
  if (payload.removeAttachment) form.append('remove_attachment', 'true')
  return form
}

export async function fetchNotices() { return (await http.get<Notice[]>('/api/notices')).data }
export async function createNotice(payload: NoticeForm) { return (await http.post<Notice>('/api/notices', toFormData(payload))).data }
export async function updateNotice(id: number, payload: NoticeForm) { return (await http.patch<Notice>(`/api/notices/${id}`, toFormData(payload))).data }
export async function deleteNotice(id: number) { await http.delete(`/api/notices/${id}`) }
export async function markNoticeRead(id: number) { await http.post(`/api/notices/${id}/read`) }
export async function generateNoticeDraft(topic: string) { return (await http.post<{ title: string; content: string }>('/api/notices/ai-draft', { topic }, { timeout: 95000 })).data }
export async function fetchNoticeReaders(id: number) { return (await http.get<{ read: { id: number; display_name: string }[]; unread: { id: number; display_name: string }[] }>(`/api/notices/${id}/readers`)).data }
export async function downloadNoticeAttachment(notice: Notice) {
  const response = await http.get<Blob>(`/api/notices/${notice.id}/attachment`, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data); const link = document.createElement('a')
  link.href = url; link.download = notice.attachment_name ?? '附件'; link.click(); URL.revokeObjectURL(url)
}
