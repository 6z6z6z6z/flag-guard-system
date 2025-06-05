// ͨ����Ӧ����
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// �û��������
export interface User {
  id: number
  username: string
  email: string
  role: string
  created_at: string
  updated_at: string
}

// �¼��������
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

// ѵ���������
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

// ��¼�������
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

// ��¼�������
export interface LoginParams {
  username: string
  password: string
}

// ע���������
export interface RegisterParams {
  username: string
  email: string
  password: string
  confirm_password: string
} 