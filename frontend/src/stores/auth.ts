import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export type UserRole = 'secretary' | 'student'

export const useAuthStore = defineStore('auth', () => {
  const role = ref<UserRole | null>((localStorage.getItem('role') as UserRole | null) ?? null)
  const className = ref(localStorage.getItem('className') ?? '')
  const displayName = ref(localStorage.getItem('displayName') ?? '')
  const token = ref(localStorage.getItem('token') ?? '')

  const isLoggedIn = computed(() => role.value !== null && className.value !== '' && token.value !== '')

  function login(nextToken: string, user: { role: UserRole; class_name: string; display_name: string }) {
    token.value = nextToken
    role.value = user.role
    className.value = user.class_name
    displayName.value = user.display_name
    localStorage.setItem('token', nextToken)
    localStorage.setItem('role', user.role)
    localStorage.setItem('className', user.class_name)
    localStorage.setItem('displayName', user.display_name)
  }

  function logout() {
    role.value = null
    className.value = ''
    displayName.value = ''
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('className')
    localStorage.removeItem('displayName')
  }

  return { role, className, displayName, token, isLoggedIn, login, logout }
})
