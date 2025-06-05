import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Event, ApiResponse } from '../types/api'
import request from '../utils/request'

export const useEventStore = defineStore('event', () => {
  const events = ref<Event[]>([])
  const currentEvent = ref<Event | null>(null)
  const loading = ref(false)

  // 获取事件列表
  const getEvents = async () => {
    loading.value = true
    try {
      const res = await request.get<ApiResponse<Event[]>>('/events')
      events.value = res.data.data
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取单个事件
  const getEvent = async (id: number) => {
    loading.value = true
    try {
      const res = await request.get<ApiResponse<Event>>(`/events/${id}`)
      currentEvent.value = res.data.data
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建事件
  const createEvent = async (data: Partial<Event>) => {
    loading.value = true
    try {
      const res = await request.post<ApiResponse<Event>>('/events', data)
      events.value.push(res.data.data)
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新事件
  const updateEvent = async (id: number, data: Partial<Event>) => {
    loading.value = true
    try {
      const res = await request.put<ApiResponse<Event>>(`/events/${id}`, data)
      const index = events.value.findIndex(e => e.id === id)
      if (index !== -1) {
        events.value[index] = res.data.data
      }
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除事件
  const deleteEvent = async (id: number) => {
    loading.value = true
    try {
      const res = await request.delete<ApiResponse<void>>(`/events/${id}`)
      events.value = events.value.filter(e => e.id !== id)
      return res
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    events,
    currentEvent,
    loading,
    getEvents,
    getEvent,
    createEvent,
    updateEvent,
    deleteEvent
  }
}) 