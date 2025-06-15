import { defineStore } from 'pinia'
import { ref } from 'vue'
import request, { ApiResponse } from '../utils/request'

// 定义事件接口
export interface Event {
  id: number
  name: string
  description: string
  time: string
  location: string
  points: number
  created_at: string
  updated_at: string
}

export const useEventStore = defineStore('event', () => {
  const events = ref<Event[]>([])
  const currentEvent = ref<Event | null>(null)

  // 获取所有事件
  const fetchEvents = async () => {
    try {
      const res = await request.get<Event[]>('/events')
      events.value = res.data
      return res
    } catch (error) {
      throw error
    }
  }

  // 获取单个事件
  const fetchEventById = async (id: number) => {
    try {
      const res = await request.get<Event>(`/events/${id}`)
      currentEvent.value = res.data
      return res
    } catch (error) {
      throw error
    }
  }

  // 创建事件
  const createEvent = async (data: Partial<Event>) => {
    try {
      const res = await request.post<Event>('/events', data)
      events.value.push(res.data)
      return res
    } catch (error) {
      throw error
    }
  }

  // 更新事件
  const updateEvent = async (id: number, data: Partial<Event>) => {
    try {
      const res = await request.put<Event>(`/events/${id}`, data)
      const index = events.value.findIndex(e => e.id === id)
      if (index !== -1) {
        events.value[index] = res.data
      }
      return res
    } catch (error) {
      throw error
    }
  }

  // 删除事件
  const deleteEvent = async (id: number) => {
    try {
      await request.delete<ApiResponse>(`/events/${id}`)
      events.value = events.value.filter(e => e.id !== id)
    } catch (error) {
      throw error
    }
  }

  return {
    events,
    currentEvent,
    fetchEvents,
    fetchEventById,
    createEvent,
    updateEvent,
    deleteEvent
  }
}) 