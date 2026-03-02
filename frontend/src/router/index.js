import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/chat'
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('../views/ChatView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () => import('../views/KnowledgeView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/history',
      name: 'History',
      component: () => import('../views/HistoryView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents',
      name: 'Agents',
      component: () => import('../views/AgentsView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.meta.requiresAuth

  if (requiresAuth && !token) {
    // Route requires authentication but no token found
    next('/login')
  } else if (to.path === '/login' && token) {
    // Already logged in, redirect to home
    next('/')
  } else {
    // Proceed as normal
    next()
  }
})

export default router
