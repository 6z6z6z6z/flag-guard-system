<template>
  <div class="events-container">
          <div class="header-controls">
      <h1 class="page-title">活动列表</h1>
      <el-button v-if="userStore.userInfo?.role === 'admin' || userStore.userInfo?.role === 'superadmin'" type="primary" @click="showCreateDialog" :icon="Plus">创建活动</el-button>
    </div>
    <el-divider />

    <div class="content-area">
      <el-row :gutter="20" v-if="events.length > 0">
        <el-col :xs="24" :sm="12" :md="8" v-for="event in events" :key="event.event_id" class="event-col">
          <el-card class="event-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="event-name">{{ event.name }}</span>
                <el-tag :type="getEventDisplayStatus(event.time) === '未开始' ? 'success' : 'info'" size="small">
                  {{ getEventDisplayStatus(event.time) }}
                </el-tag>
              </div>
            </template>
            <div class="card-body">
              <p><el-icon><Timer /></el-icon> <strong>时间：</strong>{{ formatTime(event.time) }}</p>
              <p><el-icon><Location /></el-icon> <strong>地点：</strong>{{ event.location }}</p>
              <p><el-icon><Umbrella /></el-icon> <strong>着装：</strong> {{ event.uniform_required }}</p>
            </div>
            <div class="card-footer">
              <div class="actions">
                <!-- 报名/取消报名按钮 -->
                <el-button
                  v-if="getEventDisplayStatus(event.time) === '未开始' && !event.is_registered"
                  type="success"
                  size="small"
                  @click="registerEvent(event)"
                  round
                >
                  报名参加
                </el-button>
                <el-button
                  v-else-if="getEventDisplayStatus(event.time) === '未开始' && event.is_registered"
                  type="danger"
                  size="small"
                  @click="cancelRegistration(event)"
                  round
                >
                  取消报名
                </el-button>
                 <el-button
                  v-else-if="getEventDisplayStatus(event.time) === '已结束'"
                  type="info"
                  size="small"
                  disabled
                  round
                >
                  活动已结束
                </el-button>

                <!-- 管理员操作 -->
                <div class="admin-actions" v-if="userStore.userInfo?.role === 'admin' || userStore.userInfo?.role === 'superadmin'">
                   <el-button type="primary" link @click="showEditDialog(event)" :disabled="getEventDisplayStatus(event.time) === '已结束'">编辑</el-button>
                   <el-button type="danger" link @click="handleDelete(event)">删除</el-button>
                   <el-button type="info" link @click="showRegistrations(event)">查看报名</el-button>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-else description="暂无活动"></el-empty>
    </div>

    <div class="pagination-container">
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
      @close="resetForm"
      :body-style="{ padding: '20px 60px' }"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="活动名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入活动名称" />
        </el-form-item>
        <el-form-item label="活动地点" prop="location">
          <el-input v-model="form.location" placeholder="请输入活动地点" />
        </el-form-item>
        <el-form-item label="活动时间" prop="time">
          <el-date-picker
            v-model="form.time"
            type="datetime"
            placeholder="选择活动时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="着装要求" prop="uniform_required">
          <el-input v-model="form.uniform_required" placeholder="请输入着装要求" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 报名人员名单对话框 -->
    <el-dialog
      v-model="registrationsDialogVisible"
      title="报名人员名单"
      width="1000px"
    >
      <div v-if="registrations.length === 0 && !registrationsLoading" class="empty-data">
        <el-empty description="暂无报名人员"></el-empty>
      </div>
      <el-table 
        v-else
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
        <el-table-column prop="phone_number" label="电话号码" min-width="150" />
        <el-table-column label="身高(cm)" min-width="100">
          <template #default="scope">
            {{ scope.row.height || '未填写' }}
          </template>
        </el-table-column>
        <el-table-column label="体重(kg)" min-width="100">
          <template #default="scope">
            {{ scope.row.weight || '未填写' }}
          </template>
        </el-table-column>
        <el-table-column label="鞋码" min-width="100">
          <template #default="scope">
            {{ scope.row.shoe_size || '未填写' }}
          </template>
        </el-table-column>
        <el-table-column label="报名时间" min-width="150">
          <template #default="scope">
            {{ scope.row.created_at ? formatRegistrationTime(scope.row.created_at) : '未知' }}
          </template>
        </el-table-column>
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
import { Plus, Location, Timer, Umbrella } from '@element-plus/icons-vue'
import { formatRegistrationTime, formatDate, formatTimeForBackend, isTrainingPast } from '../utils/formatDate'

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

// 检查活动是否已过期，并返回状态字符串
const getEventDisplayStatus = (time: string): string => {
  return isTrainingPast(time) ? '已结束' : '未开始'
}

// 格式化时间显示
const formatTime = (time: string) => {
  return formatDate(time)
}

const fetchEvents = async (page = 1, limit = 10) => {
  if (!userStore.getToken()) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }

  loading.value = true
  try {
    const response = await request.get('/events/', {
      params: {
        page: page,
        per_page: limit,
      }
    })
    if (response.data?.items) {
      const { items, total, current_page, per_page, pages } = response.data
      events.value = items
      pagination.value = {
        total,
        currentPage: current_page,
        pageSize: per_page,
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
      await fetchEvents(pagination.value.currentPage, pagination.value.pageSize)  // 重新获取活动列表以更新状态
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
    await fetchEvents(pagination.value.currentPage, pagination.value.pageSize) // 发生错误时也刷新一下列表
  }
}

const cancelRegistration = async (event: Event) => {
  try {
    console.log('开始取消报名:', event)  // 添加调试日志
    const response = await request.delete(`/events/${event.event_id}/register`)
    console.log('取消报名响应:', response) // 调整日志记录
    
    if (response.code === 200) {
      ElMessage.success(response.msg || '取消报名成功')
      await fetchEvents(pagination.value.currentPage, pagination.value.pageSize)  // 重新获取活动列表以更新状态
    } else {
      ElMessage.error(response.msg || '取消报名失败')
    }
  } catch (error: any) {
    console.error('取消报名失败:', error)  // 添加调试日志
    ElMessage.error(error.message || error.response?.data?.msg || '取消报名失败')
  }
}

const showCreateDialog = () => {
  if (userStore.userInfo?.role !== 'admin' && userStore.userInfo?.role !== 'superadmin') {
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
  if (userStore.userInfo?.role !== 'admin' && userStore.userInfo?.role !== 'superadmin') {
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

const resetForm = () => {
  isEdit.value = false;
  form.value = {
    name: '',
    time: new Date(),
    uniform_required: '',
    trainings: [],
    location: ''
  };
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 检查用户是否为管理员
    if (userStore.userInfo?.role !== 'admin' && userStore.userInfo?.role !== 'superadmin') {
      ElMessage.error('只有管理员可以创建活动')
      return
    }
    
    // 处理时间格式
    let timeValue = form.value.time
    if (typeof timeValue === 'string') {
      timeValue = new Date(timeValue)
    }
    
    // 直接使用前端输入的北京时间发送给后端
    const formData = {
      ...form.value,
      time: formatTimeForBackend(timeValue)
    }
    
    if (isEdit.value && form.value.event_id) {
      await request.put(`/events/${form.value.event_id}`, formData)
      ElMessage.success('活动更新成功')
    } else {
      await request.post('/events/', formData)
      ElMessage.success('活动创建成功')
    }
    
    dialogVisible.value = false
    fetchEvents(pagination.value.currentPage, pagination.value.pageSize)
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
  if (userStore.userInfo?.role !== 'admin' && userStore.userInfo?.role !== 'superadmin') {
    ElMessage.error('只有管理员可以删除活动')
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要删除该活动吗？', '提示', {
      type: 'warning'
    })
    
    await request.delete(`/events/${row.event_id}`)
    ElMessage.success('删除成功')
    fetchEvents(pagination.value.currentPage, pagination.value.pageSize)
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
    console.log('获取报名人员名单响应:', response)  // 添加调试日志
    
    // 打印详细的人员信息以便调试
    if (response.data && response.data.items) {
      console.log('报名人员详细信息:', JSON.stringify(response.data.items))
    }
    
    // 标准化处理响应数据，确保所有可能的返回格式都能被正确处理
    if (response.data) {
      let registrationItems: any[] = []
      
      // 处理嵌套的数据格式
      if (response.data.items) {
        registrationItems = response.data.items
      } else if (response.data.data && response.data.data.items) {
        registrationItems = response.data.data.items
      } 
      // 处理直接数组格式
      else if (Array.isArray(response.data)) {
        registrationItems = response.data
      }
      // 处理嵌套在data中的数组
      else if (response.data.data && Array.isArray(response.data.data)) {
        registrationItems = response.data.data
      }
      
      // 处理创建时间，使用统一的时间格式化函数
      registrations.value = registrationItems.map((reg: any) => {
        return {
          ...reg,
          // 使用统一的时间格式化函数
          created_at: formatRegistrationTime(reg.created_at)
        };
      });
      
      console.log('处理后的报名数据:', registrations.value)
    } else {
      console.warn('无效的报名人员数据格式')
      registrations.value = []
    }
  } catch (error: any) {
    console.error('获取报名人员名单失败:', error)
    ElMessage.error(error.response?.data?.msg || '获取报名人员名单失败')
  } finally {
    registrationsLoading.value = false
  }
}

// 处理页码变化
const handleCurrentChange = (page: number) => {
  pagination.value.currentPage = page
  fetchEvents(page, pagination.value.pageSize)
}

// 处理每页条数变化
const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  fetchEvents(pagination.value.currentPage, size)
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
.events-container {
  padding: 20px;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.content-area {
  margin-top: 20px;
}

.event-col {
  margin-bottom: 20px;
}

.event-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.card-body p {
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.card-body p .el-icon {
  color: #409EFF;
}

.card-footer {
  margin-top: auto;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-actions {
  display: flex;
  gap: 5px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.empty-data {
  padding: 30px 0;
  text-align: center;
}
</style> 