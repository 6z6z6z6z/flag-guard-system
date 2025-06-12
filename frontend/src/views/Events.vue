<template>
  <div class="events">
    <div class="header">
      <h2>活动管理</h2>
      <el-button v-if="userStore.userInfo?.role === 'admin'" type="primary" @click="showCreateDialog">创建活动</el-button>
    </div>

    <el-table 
      :data="events" 
      style="width: 100%" 
      v-loading="loading"
      :resize-observer="false"
      :max-height="500"
    >
      <el-table-column prop="name" label="活动名称" min-width="150" />
      <el-table-column prop="time" label="时间" min-width="180" />
      <el-table-column prop="uniform_required" label="着装要求" min-width="150" />
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <!-- 报名按钮 -->
          <el-button
            v-if="!row.is_registered"
            type="success"
            size="small"
            @click="registerEvent(row)"
          >
            报名
          </el-button>
          <el-button
            v-else
            type="danger"
            size="small"
            @click="cancelRegistration(row)"
          >
            取消报名
          </el-button>
          <!-- 管理员操作按钮 -->
          <el-button type="primary" link v-if="userStore.userInfo?.role === 'admin'" @click="showEditDialog(row)">编辑</el-button>
          <el-button type="danger" link v-if="userStore.userInfo?.role === 'admin'" @click="handleDelete(row)">删除</el-button>
          <el-button type="info" link v-if="userStore.userInfo?.role === 'admin'" @click="showRegistrations(row)">查看报名</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑活动对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑活动' : '创建活动'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="活动名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="时间" prop="time">
          <el-date-picker
            v-model="form.time"
            type="datetime"
            placeholder="选择日期时间"
          />
        </el-form-item>
        <el-form-item label="着装要求" prop="uniform_required">
          <el-input v-model="form.uniform_required" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 报名人员名单对话框 -->
    <el-dialog
      v-model="registrationsDialogVisible"
      title="报名人员名单"
      width="1000px"
    >
      <el-table 
        :data="registrations" 
        style="width: 100%" 
        v-loading="registrationsLoading"
        :resize-observer="false"
        :max-height="500"
      >
        <el-table-column prop="name" label="姓名" min-width="100" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="student_id" label="学号" min-width="120" />
        <el-table-column prop="college" label="学院" min-width="150" />
        <el-table-column prop="height" label="身高(cm)" min-width="100" />
        <el-table-column prop="weight" label="体重(kg)" min-width="100" />
        <el-table-column prop="shoe_size" label="鞋码" min-width="100" />
        <el-table-column prop="created_at" label="报名时间" min-width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'registered' ? 'success' : 'info'">
              {{ row.status === 'registered' ? '已报名' : row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

interface Event {
  event_id: number
  name: string
  time: string
  uniform_required: string
  is_registered?: boolean
}

const events = ref<Event[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

const form = ref<{
  event_id?: number
  name: string
  time: string
  uniform_required: string
}>({
  name: '',
  time: '',
  uniform_required: ''
})

const rules = {
  name: [{ required: true, message: '请输入活动名称', trigger: 'blur' }],
  time: [{ required: true, message: '请选择时间', trigger: 'change' }],
  uniform_required: [{ required: true, message: '请输入着装要求', trigger: 'blur' }]
}

const fetchEvents = async () => {
  loading.value = true
  try {
    const response = await request.get('/events')
    console.log('Events response:', response.data)
    
    if (Array.isArray(response.data)) {
      events.value = response.data.map((event: any) => {
        const processedEvent = {
          ...event,
          time: new Date(event.time).toLocaleString(),
          is_registered: Boolean(event.is_registered)  // 确保转换为布尔值
        }
        console.log('Processed event:', processedEvent)  // 添加调试日志
        return processedEvent
      })
      console.log('All processed events:', events.value)  // 添加调试日志
    } else {
      console.warn('Invalid events data format:', response.data)
      events.value = []
    }
  } catch (error) {
    console.error('获取活动列表失败:', error)
    ElMessage.error('获取活动列表失败')
    events.value = []
  } finally {
    loading.value = false
  }
}

const registerEvent = async (event: Event) => {
  try {
    const response = await request.post(`/events/${event.event_id}/register`)
    if (response.data?.message === 'Successfully registered for event') {
      ElMessage.success('报名成功')
      event.is_registered = true
    } else {
      ElMessage.error(response.data?.message || '报名失败')
    }
  } catch (error) {
    ElMessage.error('报名失败')
  }
}

const cancelRegistration = async (event: Event) => {
  try {
    const response = await request.post(`/events/${event.event_id}/cancel`)
    if (response.data?.message === 'Successfully cancelled registration') {
      ElMessage.success('取消报名成功')
      event.is_registered = false
    } else {
      ElMessage.error(response.data?.message || '取消报名失败')
    }
  } catch (error) {
    ElMessage.error('取消报名失败')
  }
}

const showCreateDialog = () => {
  isEdit.value = false
  form.value = {
    name: '',
    time: '',
    uniform_required: ''
  }
  dialogVisible.value = true
}

const showEditDialog = (row: Event) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        if (isEdit.value) {
          await request.put(`/events/${form.value.event_id}`, form.value)
          ElMessage.success('更新成功')
        } else {
          await request.post('/events', form.value)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchEvents()
      } catch (error) {
        ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
      }
    }
  })
}

const handleDelete = async (row: Event) => {
  try {
    await ElMessageBox.confirm('确定要删除这个活动吗？', '提示', {
      type: 'warning'
    })
    
    await request.delete(`/events/${row.event_id}`)
    ElMessage.success('删除成功')
    
    // 从列表中移除被删除的活动
    const index = events.value.findIndex(e => e.event_id === row.event_id)
    if (index !== -1) {
      events.value.splice(index, 1)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      // 错误消息已经在请求拦截器中处理
    }
  }
}

// 报名人员名单相关
const registrationsDialogVisible = ref(false)
const registrationsLoading = ref(false)
const registrations = ref<any[]>([])

// 显示报名人员名单
const showRegistrations = async (row: Event) => {
  try {
    registrationsLoading.value = true
    registrationsDialogVisible.value = true
    
    const response = await request.get(`/events/${row.event_id}/registrations`)
    registrations.value = response.data
  } catch (error: any) {
    console.error('获取报名人员名单失败:', error)
    ElMessage.error('获取报名人员名单失败')
  } finally {
    registrationsLoading.value = false
  }
}

// 添加 ResizeObserver 错误处理
const handleResizeObserverError = (e: ErrorEvent) => {
  if (e.message === 'ResizeObserver loop completed with undelivered notifications.') {
    e.stopImmediatePropagation()
  }
}

onMounted(() => {
  console.log('Component mounted, fetching events...')  // 添加调试日志
  fetchEvents()  // 确保在组件挂载时获取活动列表
  window.addEventListener('error', handleResizeObserverError)
})

onBeforeUnmount(() => {
  window.removeEventListener('error', handleResizeObserverError)
})
</script>

<style scoped>
.events {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 