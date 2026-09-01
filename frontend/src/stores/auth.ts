import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export type UserRole = 'secretary' | 'student'

export const useAuthStore = defineStore('auth', () => {
  const role = ref<UserRole | null>(null)
  const className = ref('')
  const displayName = ref('')

  const isLoggedIn = computed(() => role.value !== null && className.value !== '')

  function enterAs(nextRole: UserRole, nextClassName: string) {
    role.value = nextRole
    className.value = nextClassName
    displayName.value = nextRole === 'secretary' ? '团支书' : '学生'
  }

  function logout() {
    role.value = null
    className.value = ''
    displayName.value = ''
  }

  return { role, className, displayName, isLoggedIn, enterAs, logout }
})
