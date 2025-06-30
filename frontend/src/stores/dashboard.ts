import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../utils/request'

// 定义接口
interface DashboardStats {
  total_users: number
  total_trainings: number
  total_events: number
  total_flags: number
  pending_records: number
  total_points: number
}

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态
  const stats = ref<DashboardStats>({
    total_users: 0,
    total_trainings: 0,
    total_events: 0,
    total_flags: 0,
    pending_records: 0,
    total_points: 0,
  })
  const recentEvents = ref<any[]>([])
  const recentTrainings = ref<any[]>([])
  const pendingTasks = ref<any[]>([])
  const loading = ref(false)

  // 动作
  const fetchDashboardData = async () => {
    loading.value = true
    try {
      const response = await request.get('/dashboard/')
      if (response && response.data) {
        const data = response.data
        stats.value = {
          total_users: data.total_users || 0,
          total_trainings: data.total_trainings || 0,
          total_events: data.total_events || 0,
          total_flags: data.total_flags || 0,
          pending_records: data.pending_records || 0,
          total_points: data.total_points || 0,
        }
        recentEvents.value = data.recent_events || []
        recentTrainings.value = data.recent_trainings || []
        pendingTasks.value = data.pending_tasks || []
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      // 在这里可以添加错误处理，例如显示一个提示
    } finally {
      loading.value = false
    }
  }

  return {
    stats,
    recentEvents,
    recentTrainings,
    pendingTasks,
    loading,
    fetchDashboardData,
  }
}) 