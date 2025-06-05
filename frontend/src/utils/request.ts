import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// ����axiosʵ��
const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ����������
request.interceptors.request.use(
  config => {
    // ȷ��headers�������
    config.headers = config.headers || {}
    
    // ��localStorage��ȡtoken
    const token = localStorage.getItem('token')
    console.log('Current token:', token)  // ��ӵ�����־
    
    if (token) {
      // ���token�Ƿ��Ѿ�����Bearerǰ׺
      const authHeader = token.startsWith('Bearer ') ? token : `Bearer ${token}`
      config.headers.Authorization = authHeader
      
      // ��ӡ������Ϣ�����ڵ���
      console.log('Request:', {
        url: config.url,
        method: config.method,
        headers: config.headers,
        baseURL: config.baseURL,
        fullURL: `${config.baseURL}${config.url}`,
        authHeader: authHeader  // ��ӵ�����־
      })
    } else {
      console.warn('No token found in localStorage')  // ��ӵ�����־
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// ��Ӧ������
request.interceptors.response.use(
  response => {
    // ��ӡ��Ӧ��Ϣ�����ڵ���
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
      
      // ��ӡ������Ϣ�����ڵ���
      console.error('Error details:', {
        status,
        data,
        config: error.config,
        baseURL: error.config?.baseURL,
        fullURL: error.config ? `${error.config.baseURL}${error.config.url}` : undefined
      })
      
      switch (status) {
        case 401:
          ElMessage.error(data?.error || data?.msg || 'δ��Ȩ�������µ�¼')
          localStorage.removeItem('token')
          router.push('/login')
          break
        case 403:
          ElMessage.error(data?.error || data?.msg || '�ܾ�����')
          break
        case 404:
          ElMessage.error(data?.error || data?.msg || '�������Դ������')
          break
        case 422:
          ElMessage.error(data?.error || data?.msg || '�����������')
          break
        case 500: {
          // ʹ�ÿ鼶����������������
          const errorMessage = data?.error || data?.msg || '����������'
          console.error('Server error:', {
            message: errorMessage,
            details: data?.details,
            stack: data?.stack
          })
          ElMessage.error(errorMessage)
          break
        }
        default:
          ElMessage.error(data?.error || data?.msg || 'δ֪����')
      }
    } else if (error.request) {
      ElMessage.error('�������������������')
    } else {
      ElMessage.error('�������ô���')
    }
    
    return Promise.reject(error)
  }
)

export default request 