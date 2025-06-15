// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 用户相关类型
export interface User {
  id: number
  username: string
  email: string
  role: string
  created_at: string
  updated_at: string
}

// 事件相关类型
export interface Event {
  id: number
  title: string
  description: string
  start_time: string
  end_time: string
  location: string
  status: string
  created_by: number
  created_at: string
  updated_at: string
}

// 训练相关类型
export interface Training {
  id: number
  title: string
  description: string
  training_time: string
  trainer: string
  participants: string[]
  status: string
  created_at: string
  updated_at: string
}

// 记录相关类型
export interface Record {
  id: number
  user_id: number
  event_id: number
  record_type: string
  points: number
  description: string
  created_at: string
  updated_at: string
}

// 登录请求参数
export interface LoginParams {
  username: string
  password: string
}

// 注册请求参数
export interface RegisterParams {
  username: string
  email: string
  password: string
  confirm_password: string
} 