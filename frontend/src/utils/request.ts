import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 确保headers对象存在
    config.headers = config.headers || {}
    
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    console.log('Current token:', token)  // 添加调试日志
    
    if (token) {
      // 检查token是否已经包含Bearer前缀
      const authHeader = token.startsWith('Bearer ') ? token : `Bearer ${token}`
      config.headers.Authorization = authHeader
      
      // 打印请求信息，用于调试
      console.log('Request:', {
        url: config.url,
        method: config.method,
        headers: config.headers,
        baseURL: config.baseURL,
        fullURL: `${config.baseURL}${config.url}`,
        authHeader: authHeader  // 添加调试日志
      })
    } else {
      console.warn('No token found in localStorage')  // 添加调试日志
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 打印响应信息，用于调试
    console.log('Response:', {
      url: response.config.url,
      status: response.status,
      data: response.data,
      baseURL: response.config.baseURL,
      fullURL: `${response.config.baseURL}${response.config.url}`
    })
    
    return response
  },
  error => {
    console.error('Response error:', error)
    
    if (error.response) {
      const { status, data } = error.response
      
      // 打印错误信息，用于调试
      console.error('Error details:', {
        status,
        data,
        config: error.config,
        baseURL: error.config?.baseURL,
        fullURL: error.config ? `${error.config.baseURL}${error.config.url}` : undefined
      })
      
      switch (status) {
        case 401:
          ElMessage.error(data?.error || data?.msg || '未授权，请重新登录')
          localStorage.removeItem('token')
          router.push('/login')
          break
        case 403:
          ElMessage.error(data?.error || data?.msg || '拒绝访问')
          break
        case 404:
          ElMessage.error(data?.error || data?.msg || '请求的资源不存在')
          break
        case 422:
          ElMessage.error(data?.error || data?.msg || '请求参数错误')
          break
        case 500: {
          // 使用块级作用域来声明变量
          const errorMessage = data?.error || data?.msg || '服务器错误'
          console.error('Server error:', {
            message: errorMessage,
            details: data?.details,
            stack: data?.stack
          })
          ElMessage.error(errorMessage)
          break
        }
        default:
          ElMessage.error(data?.error || data?.msg || '未知错误')
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default request 