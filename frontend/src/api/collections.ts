import { API_BASE_URL, http } from './http'

export type FieldType = 'text' | 'date' | 'single'
export interface CollectionField { id: string; label: string; type: FieldType; required: boolean; options: string[] }
export interface CollectionTask {
  id: number; title: string; description: string; fields: CollectionField[]; status: 'draft' | 'published' | 'closed'
  deadline?: string; attachment_required: boolean; allow_modify: boolean; submitted_count: number; student_count: number
  my_status?: 'draft' | 'submitted' | 'returned'; created_at: string; updated_at: string
}
export interface TaskForm { title: string; description: string; fields: CollectionField[]; status: CollectionTask['status']; deadline: string; attachment_required: boolean; allow_modify: boolean }
export interface Submission {
  id: number; student_id: number; student_name: string; answers: Record<string, string>; status: 'draft' | 'submitted' | 'returned'
  return_reason?: string; attachment_name?: string; submitted_at?: string; updated_at: string
}

export async function fetchCollectionTasks() { return (await http.get<CollectionTask[]>('/api/collections')).data }
export async function createCollectionTask(payload: TaskForm) { return (await http.post<CollectionTask>('/api/collections', payload)).data }
export async function updateCollectionTask(id: number, payload: TaskForm) { return (await http.patch<CollectionTask>(`/api/collections/${id}`, payload)).data }
export async function deleteCollectionTask(id: number) { await http.delete(`/api/collections/${id}`) }
export async function fetchTaskSubmissions(id: number) { return (await http.get<{ submissions: Submission[]; missing: { student_id: number; student_name: string }[]; overdue: { student_id: number; student_name: string }[] }>(`/api/collections/${id}/submissions`)).data }
export async function returnTaskSubmission(taskId: number, submissionId: number, reason: string) { await http.post(`/api/collections/${taskId}/submissions/${submissionId}/return`, { reason }) }
export async function fetchMySubmission(taskId: number) { return (await http.get<Submission | null>(`/api/collections/${taskId}/my-submission`)).data }
export async function saveMySubmission(taskId: number, answers: Record<string, string>, submit: boolean, attachment?: File) {
  const data = new FormData(); data.append('answers', JSON.stringify(answers)); data.append('submit', String(submit)); if (attachment) data.append('attachment', attachment)
  return (await http.put<Submission>(`/api/collections/${taskId}/my-submission`, data)).data
}
export async function downloadSubmissionAttachment(taskId: number, submission: Submission) {
  const response = await http.get<Blob>(`/api/collections/${taskId}/submissions/${submission.id}/attachment`, { responseType: 'blob' })
  const url = URL.createObjectURL(response.data); const anchor = document.createElement('a'); anchor.href = url; anchor.download = submission.attachment_name ?? '材料'; anchor.click(); URL.revokeObjectURL(url)
}
export async function exportTask(id: number, title: string) {
  const response = await fetch(`${API_BASE_URL}/api/collections/${id}/export`, { headers: { Authorization: `Bearer ${localStorage.getItem('token') ?? ''}` } })
  if (!response.ok) throw new Error('导出失败')
  const url = URL.createObjectURL(await response.blob()); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${title}-提交汇总.csv`; anchor.click(); URL.revokeObjectURL(url)
}
