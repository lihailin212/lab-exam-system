import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/scan',
    name: 'ScanConfirm',
    component: () => import('../views/ScanConfirm.vue')
  },
  {
    path: '/scan-exam',
    name: 'ScanExam',
    component: () => import('../views/ScanExam.vue')
  },
  {
    path: '/',
    name: 'ExamList',
    component: () => import('../views/ExamList.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exam/:id',
    name: 'Exam',
    component: () => import('../views/Exam.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    redirect: '/admin/dashboard',
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/admin/Dashboard.vue')
      },
      {
        path: 'users',
        name: 'UserManage',
        component: () => import('../views/admin/UserManage.vue')
      },
      {
        path: 'exams',
        name: 'ExamManage',
        component: () => import('../views/admin/ExamManage.vue')
      },
      {
        path: 'questions/:examId',
        name: 'QuestionManage',
        component: () => import('../views/admin/QuestionManage.vue')
      },
      {
        path: 'scores',
        name: 'ScoreStat',
        component: () => import('../views/admin/ScoreStat.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    next('/')
  } else {
    next()
  }
})

export default router
