import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '../utils/request'

// 定义用户信息接口
interface UserInfo {
  id: number
  username: string
  name: string
  role: string
  college: string
  student_id: string
  phone_number: string
  total_points: number
}

// 定义登录响应接口
interface LoginResponse {
  token: string
  user: UserInfo
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<UserInfo | null>(null)
  
  // 计算属性：判断是否为管理员
  const isAdmin = computed(() => {
    return userInfo.value?.role === 'admin'
  })

  // 获取token - 直接从 localStorage 获取，这是最可靠的同步方式
  const getToken = () => {
    return localStorage.getItem('token')
  }

  // 设置token
  const setToken = (newToken: string) => {
    const cleanToken = newToken.startsWith('Bearer ') ? newToken.substring(7) : newToken;
    token.value = cleanToken
    localStorage.setItem('token', cleanToken)
  }

  // 清除token
  const clearToken = () => {
    token.value = null
    userInfo.value = null
    localStorage.removeItem('token')
  }

  // 登录
  const login = async (username: string, password: string) => {
    try {
      const response = await request.post<LoginResponse>('/auth/login', { username, password })
      if (response.code === 200 && response.data?.token) {
        setToken(response.data.token)
        return response
      }
      throw new Error(response.msg || '登录失败')
    } catch (error: any) {
      console.error('Login error:', error)
      clearToken()
      throw new Error(error?.response?.data?.msg || error?.message || '登录失败')
    }
  }

  // 注册
  const register = async (userData: {
    username: string
    password: string
    name: string
    student_id: string
    college: string
    phone_number: string
    role?: string
  }) => {
    try {
      const response = await request.post('/auth/register', userData)
      if (response.code === 200 || response.code === 201) {
        return response
      }
      throw new Error(response.msg || '注册失败')
    } catch (error: any) {
      console.error('Registration error:', error)
      throw error
    }
  }

  // 获取用户信息
  const getUserInfo = async () => {
    try {
      const response = await request.get<UserInfo>('/auth/info')
      if (response.code === 200 && response.data) {
        userInfo.value = response.data
        return response.data
      }
      throw new Error(response.msg || '获取用户信息失败')
    } catch (error: any) {
      console.error('Get user info error:', error)
      throw error
    }
  }

  // 退出登录
  const logout = () => {
    clearToken()
    window.location.href = '/login'
  }

  // 初始化store
  const initStore = async () => {
    const token = getToken()
    if (token && !userInfo.value) {
      await getUserInfo()
    }
  }

  return {
    token,
    userInfo,
    isAdmin,
    getToken,
    setToken,
    clearToken,
    login,
    register,
    getUserInfo,
    logout,
    initStore,
  }
}) 