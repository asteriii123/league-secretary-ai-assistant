import { http } from './http'
import type { MeetingActionItem, MeetingSummary } from './ai'

export interface MeetingRecord {
  id: number; meeting_type: string; title: string; transcript: string; summary: string
  key_points: string[]; decisions: string[]; action_items: MeetingActionItem[]
  source_name?: string; created_at: string; updated_at: string
}
export interface MeetingRecordPayload {
  meeting_type: string; title: string; transcript: string; summary: string
  key_points: string[]; decisions: string[]; action_items: MeetingActionItem[]
  upload_id?: string; source_name?: string
}
export async function transcribeMeeting(file: File) {
  const data = new FormData(); data.append('file', file)
  return (await http.post<{ transcript: string; upload_id: string; source_name: string }>('/api/meetings/transcribe', data, { timeout: 60 * 60 * 1000 })).data
}
export async function fetchMeetingRecords() { return (await http.get<MeetingRecord[]>('/api/meetings')).data }
export async function createMeetingRecord(payload: MeetingRecordPayload) { return (await http.post<MeetingRecord>('/api/meetings', payload)).data }
export async function updateMeetingRecord(id: number, payload: MeetingRecordPayload) { return (await http.patch<MeetingRecord>(`/api/meetings/${id}`, payload)).data }
export async function deleteMeetingRecord(id: number) { await http.delete(`/api/meetings/${id}`) }
export function summaryToPayload(summary: MeetingSummary, transcript: string, uploadId?: string, sourceName?: string): MeetingRecordPayload {
  return { meeting_type: summary.meeting_type, title: summary.title, transcript, summary: summary.summary, key_points: summary.key_points, decisions: summary.decisions, action_items: summary.action_items, upload_id: uploadId, source_name: sourceName }
}
