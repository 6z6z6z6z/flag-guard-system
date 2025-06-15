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
        meta: { title: '升降旗审核', icon: 'Check', roles: ['admin', 'captain'] }
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
        meta: { title: '训练审核', icon: 'Document', roles: ['admin', 'captain'] }
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
        meta: { title: '活动创建', icon: 'Plus', roles: ['captain'] }
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
        meta: { title: '积分管理', icon: 'Operation', roles: ['admin'] }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['admin', 'captain'] }
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
          requiresAdmin: true
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
  // !! 关键改动：在守卫函数内部获取 store 实例
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)

  if (requiresAuth) {
    const token = userStore.getToken()
    if (token) {
      // 如果有 token，但没有用户信息，说明是刷新页面或刚登录
      if (!userStore.userInfo) {
        try {
          // 获取用户信息，这是进入系统的第一步
          await userStore.getUserInfo()
          next()
        } catch (error) {
          console.error('Authentication error during navigation:', error)
          userStore.logout() // 清理状态并跳转到登录页
          ElMessage.error('认证失败，请重新登录')
          next({ name: 'Login' })
        }
      } else {
        // 用户信息已存在，直接放行
        next()
      }
    } else {
      // 没有 token，跳转到登录页
      ElMessage.warning('请先登录')
      next({ name: 'Login' })
    }
  } else {
    // 如果目标路由不需要认证
    if (to.name === 'Login' && userStore.getToken()) {
      // 如果已登录，访问登录页则重定向到首页
      next({ path: '/' })
    } else {
      next()
    }
  }

  // 设置页面标题
  document.title = `${to.meta.title || '学生管理系统'}`
})

export default router