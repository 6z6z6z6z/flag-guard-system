import { defineStore } from 'pinia'
import request from '../utils/request'
import { ElMessage } from 'element-plus'
import router from '../router'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null as any
  }),

  getters: {
    isLoggedIn: (state) => {
      console.log('Checking login status, token:', state.token)
      return !!state.token
    },
    isAdmin: (state) => {
      console.log('Checking admin status, userInfo:', state.userInfo)
      return state.userInfo?.role === 'admin'
    },
    isCaptain: (state) => state.userInfo?.role === 'captain'
  },

  actions: {
    async register(userData: any) {
      try {
        const res = await request.post('/auth/register', userData)
        if (res.data?.msg === 'User created successfully') {
          ElMessage.success('注册成功')
          return res
        }
        throw new Error(res.data?.msg || '注册失败')
      } catch (error: any) {
        ElMessage.error(error.response?.data?.msg || error.message || '注册失败')
        throw error
      }
    },

    async login(username: string, password: string) {
      try {
        const res = await request.post('/auth/login', { username, password })
        if (res.data?.data?.token) {
          const token = res.data.data.token
          console.log('Setting token:', token)
          this.token = token
          localStorage.setItem('token', token)
          
          if (res.data.data.user) {
            console.log('Setting user info:', res.data.data.user)
            this.userInfo = res.data.data.user
          }
          return res
        }
        throw new Error(res.data?.msg || '登录失败')
      } catch (error: any) {
        console.error('Login error:', error)
        ElMessage.error(error.response?.data?.msg || error.message || '登录失败')
        throw error
      }
    },

    async getUserInfo() {
      if (this.userInfo) {
        console.log('Using cached user info:', this.userInfo)
        return this.userInfo
      }

      try {
        if (!this.token) {
          console.warn('No token available for getUserInfo')
          throw new Error('未登录')
        }

        console.log('Fetching user info with token:', this.token)
        const res = await request.get('/users/profile')
        
        if (res.data?.data) {
          console.log('Received user info:', res.data.data)
          this.userInfo = res.data.data
          return this.userInfo
        }
        throw new Error('获取用户信息失败')
      } catch (error: any) {
        console.error('获取用户信息失败:', error)
        if (error.response?.status === 401) {
          console.log('Token expired, logging out')
          this.logout()
          ElMessage.error('登录已过期，请重新登录')
        } else {
          ElMessage.error(error.response?.data?.msg || error.message || '获取用户信息失败')
        }
        throw error
      }
    },

    async updateProfile(data: any) {
      try {
        const res = await request.put('/users/profile', data)
        if (res.data?.data) {
          this.userInfo = { ...this.userInfo, ...res.data.data }
          return this.userInfo
        }
        throw new Error('更新用户信息失败')
      } catch (error: any) {
        ElMessage.error(error.response?.data?.msg || error.message || '更新用户信息失败')
        throw error
      }
    },

    logout() {
      console.log('Logging out, clearing token and user info')
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
      router.push('/login')
    }
  }
}) 