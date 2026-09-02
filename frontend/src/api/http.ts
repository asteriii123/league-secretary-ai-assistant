import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
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
