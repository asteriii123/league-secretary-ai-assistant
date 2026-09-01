import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  timeout: 8000,
})

export interface WelcomeResponse {
  message: string
  role: string
}

export async function fetchWelcome(role: 'secretary' | 'student') {
  const response = await http.get<WelcomeResponse>('/api/welcome', {
    params: { role },
  })
  return response.data
}
