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
      <el-table-column prop="location" label="地点" min-width="120" />
      <el-table-column prop="time" label="时间" min-width="180">
        <template #default="{ row }">
          {{ formatTime(row.time) }}
        </template>
      </el-table-column>
      <el-table-column prop="uniform_required" label="着装要求" min-width="150" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="isEventExpired(row.time) ? 'info' : 'success'">
            {{ isEventExpired(row.time) ? '已结束' : '进行中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <!-- 报名按钮 -->
          <el-button
            v-if="!row.is_registered && !isEventExpired(row.time)"
            type="success"
            size="small"
            @click="registerEvent(row)"
          >
            报名
          </el-button>
          <el-button
            v-else-if="row.is_registered && !isEventExpired(row.time)"
            type="danger"
            size="small"
            @click="cancelRegistration(row)"
          >
            取消报名
          </el-button>
          <el-button
            v-else
            type="info"
            size="small"
            disabled
          >
            {{ row.is_registered ? '已报名' : '报名' }}
          </el-button>
          <!-- 管理员操作按钮 -->
          <el-button type="primary" link v-if="userStore.userInfo?.role === 'admin'" @click="showEditDialog(row)">编辑</el-button>
          <el-button type="danger" link v-if="userStore.userInfo?.role === 'admin'" @click="handleDelete(row)">删除</el-button>
          <el-button type="info" link v-if="userStore.userInfo?.role === 'admin'" @click="showRegistrations(row)">查看报名</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container" style="margin-top: 20px; text-align: right;">
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

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
        <el-form-item label="地点" prop="location" required>
          <el-input v-model="form.location" placeholder="请输入活动地点" />
        </el-form-item>
        <el-form-item label="时间" prop="time">
          <el-date-picker
            v-model="form.time"
            type="datetime"
            placeholder="选择日期时间"
            format="YYYY-MM-DD HH:mm"
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
        <el-table-column prop="phone_number" label="电话号码" min-width="150" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useUserStore } from '../stores/user'
import request from '../utils/request'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

interface Event {
  event_id: number
  name: string
  time: string
  uniform_required: string
  trainings?: Array<{
    training_id: number
    name: string
    type: string
  }>
  is_registered?: boolean
  location: string
}

interface EventForm {
  event_id?: number
  name: string
  time: Date
  uniform_required: string
  trainings: number[]
  location: string
}

const events = ref<Event[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const pagination = ref({
  total: 0,
  currentPage: 1,
  pageSize: 10,
  pageCount: 1
})

const form = ref<EventForm>({
  name: '',
  time: new Date(),
  uniform_required: '',
  trainings: [],
  location: ''
})

const rules = {
  name: [{ required: true, message: '请输入活动名称', trigger: 'blur' }],
  time: [{ required: true, message: '请选择时间', trigger: 'change' }],
  uniform_required: [{ required: true, message: '请输入着装要求', trigger: 'blur' }],
  location: [{ required: true, message: '请输入活动地点', trigger: 'blur' }]
}

// 检查活动是否已过期
const isEventExpired = (time: string): boolean => {
  return new Date(time) < new Date()
}

// 格式化时间显示
const formatTime = (time: string) => {
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

const fetchEvents = async () => {
  if (!userStore.getToken()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }

  loading.value = true
  try {
    const response = await request.get('/events/')
    if (response.data?.items) {
      const { items, total, current_page, pages } = response.data
      events.value = items
      pagination.value = {
        total,
        currentPage: current_page,
        pageSize: 10,
        pageCount: pages
      }
    }
  } catch (error: any) {
    if (error.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      userStore.logout()
    } else {
      ElMessage.error(error.response?.data?.msg || '获取事件列表失败')
    }
  } finally {
    loading.value = false
  }
}

const registerEvent = async (event: Event) => {
  try {
    console.log('开始报名活动:', event)  // 添加调试日志
    const response = await request.post(`/events/${event.event_id}/register`)
    console.log('报名响应:', response)  // 添加调试日志
    
    if (response.code === 201) {
      ElMessage.success(response.msg || '报名成功')
      await fetchEvents()  // 重新获取活动列表以更新状态
    } else {
      ElMessage.error(response.msg || '报名失败')
    }
  } catch (error: any) {
    console.error('报名失败:', error)  // 添加调试日志
    if (error.response?.data?.code === 409) {
      ElMessage.warning(error.response.data.msg || '您已报名该活动')
    } else if (error.response?.data?.code === 410) {
      ElMessage.error(error.response.data.msg || '活动已过期，无法报名')
    } else {
      ElMessage.error(error.message || error.response?.data?.msg || '报名失败')
    }
    await fetchEvents() // 发生错误时也刷新一下列表
  }
}

const cancelRegistration = async (event: Event) => {
  try {
    console.log('开始取消报名:', event)  // 添加调试日志
    const response = await request.delete(`/events/${event.event_id}/register`)
    console.log('取消报名响应:', response) // 调整日志记录
    
    if (response.code === 200) {
      ElMessage.success(response.msg || '取消报名成功')
      await fetchEvents()  // 重新获取活动列表以更新状态
    } else {
      ElMessage.error(response.msg || '取消报名失败')
    }
  } catch (error: any) {
    console.error('取消报名失败:', error)  // 添加调试日志
    ElMessage.error(error.message || error.response?.data?.msg || '取消报名失败')
  }
}

const showCreateDialog = () => {
  if (userStore.userInfo?.role !== 'admin') {
    ElMessage.error('只有管理员可以创建活动')
    return
  }
  
  isEdit.value = false
  form.value = {
    name: '',
    time: new Date(),
    uniform_required: '',
    trainings: [],
    location: ''
  }
  dialogVisible.value = true
}

const showEditDialog = (row: Event) => {
  if (userStore.userInfo?.role !== 'admin') {
    ElMessage.error('只有管理员可以编辑活动')
    return
  }
  
  isEdit.value = true
  form.value = {
    event_id: row.event_id,
    name: row.name,
    time: new Date(row.time),
    uniform_required: row.uniform_required || '',
    trainings: row.trainings?.map(t => t.training_id) || [],
    location: row.location || ''
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 检查用户是否为管理员
    if (userStore.userInfo?.role !== 'admin') {
      ElMessage.error('只有管理员可以创建活动')
      return
    }
    
    // 处理时间格式
    let timeValue = form.value.time
    if (typeof timeValue === 'string') {
      timeValue = new Date(timeValue)
    }
    
    // 转换为UTC时间
    const utcTime = new Date(timeValue.getTime() - timeValue.getTimezoneOffset() * 60000)
    
    const formData = {
      ...form.value,
      time: utcTime.toISOString()
    }
    
    if (isEdit.value && form.value.event_id) {
      await request.put(`/events/${form.value.event_id}`, formData)
      ElMessage.success('活动更新成功')
    } else {
      await request.post('/events/', formData)
      ElMessage.success('活动创建成功')
    }
    
    dialogVisible.value = false
    fetchEvents()
  } catch (error: any) {
    console.error('提交表单失败:', error)
    if (error.response?.status === 403) {
      ElMessage.error('没有权限执行此操作')
    } else {
      ElMessage.error(error.response?.data?.msg || '操作失败')
    }
  }
}

const handleDelete = async (row: Event) => {
  if (userStore.userInfo?.role !== 'admin') {
    ElMessage.error('只有管理员可以删除活动')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要删除该活动吗？', '提示', {
      type: 'warning'
    })
    
    await request.delete(`/events/${row.event_id}`)
    ElMessage.success('删除成功')
    fetchEvents()
  } catch (error: any) {
    if (error === 'cancel') return
    console.error('删除失败:', error)
    if (error.response?.status === 403) {
      ElMessage.error('没有权限执行此操作')
    } else {
      ElMessage.error(error.response?.data?.msg || '删除失败')
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
    console.log('获取报名人员名单响应:', response.data)  // 添加调试日志
    
    if (response.data && Array.isArray(response.data)) {
      registrations.value = response.data.map((reg: any) => ({
        ...reg,
        created_at: new Date().toLocaleString()  // 添加报名时间
      }))
    } else {
      console.warn('无效的报名人员数据格式:', response.data)  // 添加调试日志
      registrations.value = []
    }
  } catch (error: any) {
    console.error('获取报名人员名单失败:', error)  // 添加调试日志
    ElMessage.error(error.response?.data?.msg || '获取报名人员名单失败')
  } finally {
    registrationsLoading.value = false
  }
}

// 处理页码变化
const handleCurrentChange = (page: number) => {
  pagination.value.currentPage = page
  fetchEvents()
}

// 处理每页条数变化
const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
  fetchEvents()
}

onMounted(async () => {
  try {
    await userStore.initStore()
    await fetchEvents()
  } catch (error) {
    console.error('Failed to initialize page:', error)
    ElMessage.error('初始化失败，请刷新页面重试')
  }
})

// 处理 ResizeObserver 错误
onBeforeUnmount(() => {
  const resizeObserverError = 'ResizeObserver loop completed with undelivered notifications.'
  const originalError = window.console.error
  window.console.error = (...args) => {
    if (args[0] === resizeObserverError) return
    originalError.apply(window.console, args)
  }
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

.pagination-container {
  margin-top: 20px;
  text-align: right;
}
</style> 