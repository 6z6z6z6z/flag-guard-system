import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import type { Training, Registration } from '@/types/training'

interface TrainingsResponse {
  items: Training[];
  total: number;
  pages: number;
  current_page: number;
}

export const useTrainingStore = defineStore('training', () => {
  const trainings = ref<Training[]>([])
  const total = ref(0)
  const loading = ref(false)

  const getTrainings = async (page = 1, per_page = 10) => {
    loading.value = true
    try {
      const response = await request.get<TrainingsResponse>('/trainings/', {
        params: { page, per_page }
      });
      if (response.code === 200 && response.data) {
        trainings.value = response.data.items;
        total.value = response.data.total;
      }
    } finally {
      loading.value = false
    }
  }

  const createTraining = async (data: Partial<Training>) => {
    return await request.post('/trainings/', data)
  }

  const updateTraining = async (id: number, data: Partial<Training>) => {
    return await request.put(`/trainings/${id}`, data)
  }

  const deleteTraining = async (id: number) => {
    return await request.delete(`/trainings/${id}`)
  }

  const registerTraining = async (trainingId: number) => {
    return await request.post(`/trainings/${trainingId}/register`)
  }

  const cancelRegister = async (trainingId: number) => {
    return await request.delete(`/trainings/${trainingId}/register`)
  }

  const getRegistrations = async (trainingId: number): Promise<Registration[]> => {
    const response = await request.get(`/trainings/${trainingId}/registrations`);
    console.log('训练报名数据响应:', response);
    
    if (response.code === 200) {
      if (Array.isArray(response.data)) {
        return response.data as Registration[];
      }
      
      if (typeof response.data === 'object' && response.data !== null) {
        // 检查data.items
        if ('items' in response.data && Array.isArray(response.data.items)) {
          return response.data.items as Registration[];
        }
        
        // 检查data.registrations
        if ('registrations' in response.data && Array.isArray(response.data.registrations)) {
          return response.data.registrations as Registration[];
        }
        
        // 如果data本身似乎是注册数组
        if (Array.isArray(response.data)) {
          return response.data as Registration[];
        }
      }
    }
    
    return [];
  }

  const confirmAttendance = async (trainingId: number, updates: any[]) => {
    return await request.post(`/trainings/${trainingId}/registrations/attendance`, { updates });
  }

  return {
    trainings,
    total,
    loading,
    getTrainings,
    createTraining,
    updateTraining,
    deleteTraining,
    registerTraining,
    cancelRegister,
    getRegistrations,
    confirmAttendance,
  }
})