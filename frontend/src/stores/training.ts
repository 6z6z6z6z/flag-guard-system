import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Training, ApiResponse } from '../types/api'
import request from '../utils/request'

export const useTrainingStore = defineStore('training', () => {
  const trainings = ref<Training[]>([])
  const currentTraining = ref<Training | null>(null)
  const loading = ref(false)

  // 获取训练列表
  const getTrainings = async () => {
    loading.value = true
    try {
      const res = await request.get<ApiResponse<Training[]>>('/trainings')
      trainings.value = res.data.data
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取单个训练
  const getTraining = async (id: number) => {
    loading.value = true
    try {
      const res = await request.get<ApiResponse<Training>>(`/trainings/${id}`)
      currentTraining.value = res.data.data
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建训练
  const createTraining = async (data: Partial<Training>) => {
    loading.value = true
    try {
      const res = await request.post<ApiResponse<Training>>('/trainings', data)
      trainings.value.push(res.data.data)
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新训练
  const updateTraining = async (id: number, data: Partial<Training>) => {
    loading.value = true
    try {
      const res = await request.put<ApiResponse<Training>>(`/trainings/${id}`, data)
      const index = trainings.value.findIndex(t => t.id === id)
      if (index !== -1) {
        trainings.value[index] = res.data.data
      }
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除训练
  const deleteTraining = async (id: number) => {
    loading.value = true
    try {
      const res = await request.delete<ApiResponse<void>>(`/trainings/${id}`)
      trainings.value = trainings.value.filter(t => t.id !== id)
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    trainings,
    currentTraining,
    loading,
    getTrainings,
    getTraining,
    createTraining,
    updateTraining,
    deleteTraining
  }
}) 