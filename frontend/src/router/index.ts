import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import SecretaryDashboardView from '@/views/SecretaryDashboardView.vue'
import StudentDashboardView from '@/views/StudentDashboardView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import { useAuthStore, type UserRole } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'login', component: LoginView },
    {
      path: '/secretary',
      name: 'secretary-dashboard',
      component: SecretaryDashboardView,
      meta: { role: 'secretary' },
    },
    {
      path: '/student',
      name: 'student-dashboard',
      component: StudentDashboardView,
      meta: { role: 'student' },
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
  ],
})

router.beforeEach((to) => {
  const requiredRole = to.meta.role as UserRole | undefined
  if (!requiredRole) return true

  const authStore = useAuthStore()
  if (!authStore.isLoggedIn || authStore.role !== requiredRole) return { name: 'login' }
  return true
})

export default router
