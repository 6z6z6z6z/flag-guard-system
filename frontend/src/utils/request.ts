import axios, { AxiosHeaders, AxiosInstance, AxiosRequestConfig } from 'axios'
import { useUserStore } from '@/stores/user'

// 定义API响应接口
export interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

// 创建axios实例
const instance: AxiosInstance = axios.create({
  timeout: 10000
})

instance.interceptors.request.use(
  config => {
    // 在拦截器函数内部调用 useUserStore()，确保获取到的是初始化后的实例
    // const userStore = useUserStore()

    // 确保 URL 不以 http 开头，这样我们就可以安全地添加 /api 前缀
    if (config.url && !config.url.startsWith('http')) {
      // 统一添加 /api 前缀
      config.url = config.url.startsWith('/') ? `/api${config.url}` : `/api/${config.url}`;
    }

    const token = localStorage.getItem('token')

    const isAuthPath = config.url?.includes('/api/auth/login') || config.url?.includes('/api/auth/register')

    if (token && !isAuthPath) {
      if (!config.headers) {
        config.headers = new AxiosHeaders()
      }
      config.headers.set('Authorization', `Bearer ${token}`)
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  response => {
    // 核心修复：如果HTTP状态码为200，但响应体不是我们期望的标准格式
    if (response.status === 200 && (typeof response.data !== 'object' || response.data === null || !('code' in response.data))) {
      // 我们将其包装成标准的成功响应，并放回 response.data 中
      response.data = { code: 200, msg: '操作成功', data: response.data }
      return response
    }

    // 对于符合我们标准格式的响应，如果业务码不是200或201，则当作错误处理
    if (response.data.code && response.data.code !== 200 && response.data.code !== 201) {
      return Promise.reject(new Error(response.data.msg || 'Error'))
    }
    
    // 对于标准的成功响应，我们直接返回 response，让组件从 response.data 中取值
    return response
  },
  error => {
    console.error('Response error:', error)
    if (error.response?.status === 401) {
      // 在拦截器函数内部调用 useUserStore()
      const userStore = useUserStore()
      userStore.logout()
    }
    return Promise.reject(error)
  }
)

// 封装请求方法，注意现在返回的是 ApiResponse
const request = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => instance.get(url, config).then(res => res.data),
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => instance.post(url, data, config).then(res => res.data),
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => instance.put(url, data, config).then(res => res.data),
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> => instance.delete(url, config).then(res => res.data)
}

export default request 