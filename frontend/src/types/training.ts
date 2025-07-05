export interface Training {
  training_id: number
  name: string
  start_time: string
  end_time: string | null
  points: number
  created_by: number
  location: string
  created_at: string | null
  updated_at: string | null
  is_registered?: boolean
  status?: string
}

export interface Registration {
  registration_id: number
  user_id: number
  student_id: string
  name: string
  college: string
  phone_number: string
  username: string
  created_at: string
  status: string
  attendance_status: 'present' | 'absent' | 'late' | 'early_leave' | null
  points_awarded: number | null
} 