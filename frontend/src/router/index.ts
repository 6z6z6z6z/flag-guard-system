import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    title?: string
    icon?: string
    roles?: string[]
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../layout/index.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '个人中心', icon: 'UserFilled' }
      },
      {
        path: 'flag-records',
        name: 'FlagRecords',
        component: () => import('../views/FlagRecords.vue'),
        meta: { title: '升降旗记录', icon: 'Flag' }
      },
      {
        path: 'flag-review',
        name: 'FlagReview',
        component: () => import('../views/FlagReview.vue'),
        meta: { title: '升降旗审核', icon: 'Check', roles: ['admin', 'captain', 'superadmin'] }
      },
      {
        path: 'trainings',
        name: 'Trainings',
        component: () => import('../views/Trainings.vue'),
        meta: { title: '训练管理', icon: 'Trophy' }
      },
      {
        path: 'training-review',
        name: 'TrainingReview',
        component: () => import('../views/TrainingReview.vue'),
        meta: { title: '训练审核', icon: 'Document', roles: ['admin', 'captain', 'superadmin'] }
      },
      {
        path: 'events',
        name: 'Events',
        component: () => import('../views/Events.vue'),
        meta: { title: '活动管理', icon: 'Calendar' }
      },
      {
        path: 'event-manage',
        name: 'EventManage',
        component: () => import('../views/EventManage.vue'),
        meta: { title: '活动创建', icon: 'Plus', roles: ['captain', 'admin', 'superadmin'] }
      },
      {
        path: 'points',
        name: 'Points',
        component: () => import('../views/Points.vue'),
        meta: { title: '积分记录', icon: 'DataLine' }
      },
      {
        path: 'points-manage',
        name: 'PointsManage',
        component: () => import('../views/PointsManage.vue'),
        meta: { title: '积分管理', icon: 'Operation', roles: ['admin', 'superadmin'] }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['admin', 'captain', 'superadmin'] }
      },
      {
        path: 'training-attendance/:id',
        name: 'TrainingAttendance',
        component: () => import('@/views/TrainingAttendance.vue'),
        meta: {
          requiresAuth: true
        }
      },
              {
          path: 'training-review/:id',
          name: 'TrainingReview',
          component: () => import('@/views/TrainingReview.vue'),
          meta: {
            requiresAuth: true,
            requiresAdmin: true,
            roles: ['admin', 'captain', 'superadmin']
          }
        }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/404.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)

  if (requiresAuth) {
    const token = userStore.getToken()
    if (token) {
      // Pinia store state is often automatically unwrapped in router guards
      // So, userStore.userInfo directly refers to UserInfo | null
      if (userStore.userInfo === null) { // Direct check for null
        try {
          await userStore.getUserInfo() // This updates userStore.userInfo
          // After getUserInfo, userStore.userInfo will be updated.
          // No need for a local variable as userStore.userInfo is reactive.
        } catch (error) {
          console.error('Authentication error during navigation:', error)
          userStore.logout()
          ElMessage.error('认证失败，请重新登录')
          next({ name: 'Login' })
          return // Ensure only one next() call
        }
      }

      // userStore.userInfo is now either a UserInfo object or still null if getUserInfo failed
      const userRole = userStore.userInfo?.role || '' // Safely access role with optional chaining
      
      const hasRequiredRole = to.matched.every(record => {
        if (record.meta.roles) {
          return (record.meta.roles as string[]).includes(userRole)
        }
        return true
      })

      if (!hasRequiredRole) {
        ElMessage.error('您没有权限访问该页面')
        next({ path: '/dashboard' })
      } else {
        next()
      }
    } else {
      ElMessage.warning('请先登录')
      next({ name: 'Login' })
    }
  } else {
    if (to.name === 'Login' && userStore.getToken()) {
      next({ path: '/' })
    } else {
      next()
    }
  }

  document.title = `${to.meta.title || '学生管理系统'}`
})

export default router