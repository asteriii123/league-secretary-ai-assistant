import axios from 'axios'
import { http } from './http'

export interface StudentAnswer {
  answer: string
  sources: string[]
  has_reliable_source: boolean
  disclaimer: string
}

export interface MeetingActionItem {
  task: string
  owner: string
  deadline: string
}

export interface MeetingSummary {
  title: string
  meeting_type: string
  summary: string
  key_points: string[]
  decisions: string[]
  action_items: MeetingActionItem[]
  requires_manual_review: boolean
  redacted_sensitive_data: boolean
}

export async function askStudentQuestion(question: string) {
  const response = await http.post<StudentAnswer>('/api/ai/student-qa', { question }, { timeout: 95000 })
  return response.data
}

export async function summarizeMeeting(meetingType: string, transcript: string) {
  const response = await http.post<MeetingSummary>(
    '/api/ai/meeting-summary',
    { meeting_type: meetingType, transcript },
    { timeout: 95000 },
  )
  return response.data
}

export function getApiErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return '无法连接后端，请稍后重试。'
  }
  return '请求失败，请稍后重试。'
}
