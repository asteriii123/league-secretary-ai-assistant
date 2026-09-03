import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import SecretaryDashboardView from '@/views/SecretaryDashboardView.vue'
import StudentDashboardView from '@/views/StudentDashboardView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import MeetingDocumentsView from '@/views/MeetingDocumentsView.vue'
import AiCenterView from '@/views/AiCenterView.vue'
import NoticesView from '@/views/NoticesView.vue'
import CollectionsView from '@/views/CollectionsView.vue'
import KnowledgeView from '@/views/KnowledgeView.vue'
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
    {
      path: '/student/ai-qa',
      redirect: '/student/ai',
    },
    {
      path: '/student/ai',
      name: 'student-ai',
      component: AiCenterView,
      meta: { role: 'student' },
    },
    {
      path: '/secretary/meeting-summary',
      redirect: '/secretary/ai',
    },
    {
      path: '/secretary/ai',
      name: 'secretary-ai',
      component: AiCenterView,
      meta: { role: 'secretary' },
    },
    {
      path: '/secretary/meeting-documents',
      name: 'meeting-documents',
      component: MeetingDocumentsView,
      meta: { role: 'secretary' },
    },
    { path: '/secretary/notices', name: 'secretary-notices', component: NoticesView, meta: { role: 'secretary' } },
    { path: '/student/notices', name: 'student-notices', component: NoticesView, meta: { role: 'student' } },
    { path: '/secretary/collections', name: 'secretary-collections', component: CollectionsView, meta: { role: 'secretary' } },
    { path: '/student/collections', name: 'student-collections', component: CollectionsView, meta: { role: 'student' } },
    { path: '/secretary/knowledge', name: 'secretary-knowledge', component: KnowledgeView, meta: { role: 'secretary' } },
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
