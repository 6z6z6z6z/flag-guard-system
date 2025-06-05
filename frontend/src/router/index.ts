import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '../stores/user'

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

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || '学生管理系统'}`
  
  // 获取 token
  const token = localStorage.getItem('token')
  const userStore = useUserStore()
  
  // 如果是访问登录或注册页面
  if (to.path === '/login' || to.path === '/register') {
    if (token) {
      // 如果已登录，重定向到首页
      next('/')
    } else {
      // 未登录，允许访问登录/注册页面
      next()
    }
    return
  }
  
  // 检查是否需要登录
  if (to.meta.requiresAuth) {
    if (!token) {
      // 未登录，重定向到登录页
      next('/login')
      return
    }
    
    // 已登录，检查用户信息
    if (!userStore.userInfo) {
      try {
        // 获取用户信息
        await userStore.getUserInfo()
      } catch (error) {
        // 获取用户信息失败，清除 token 并重定向到登录页
        localStorage.removeItem('token')
        next('/login')
        return
      }
    }
    
    // 检查角色权限
    if (to.meta.roles && userStore.userInfo && !to.meta.roles.includes(userStore.userInfo.role)) {
      next('/403')
      return
    }
  }
  
  next()
})

export default router