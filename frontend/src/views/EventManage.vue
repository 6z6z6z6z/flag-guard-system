<template>
  <div class="event-manage-container">
    <!-- 创建活动表单 -->
    <el-card class="create-card">
      <template #header>
        <div class="card-header">
          <h3>创建活动</h3>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        :disabled="submitting"
      >
        <el-form-item label="活动名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入活动名称" />
        </el-form-item>

        <el-form-item label="活动时间" prop="time">
          <el-date-picker
            v-model="form.time"
            type="datetime"
            placeholder="选择活动时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            :disabled-date="disabledDate"
          />
        </el-form-item>

        <el-form-item label="着装要求" prop="uniform_required">
          <el-input
            v-model="form.uniform_required"
            type="textarea"
            :rows="2"
            placeholder="请输入着装要求"
          />
        </el-form-item>

        <el-form-item label="关联训练" prop="trainings">
          <el-select
            v-model="form.trainings"
            multiple
            filterable
            placeholder="选择关联训练"
          >
            <el-option
              v-for="training in trainingOptions"
              :key="training.training_id"
              :label="training.name"
              :value="training.training_id"
            />
          </el-select>
          <div class="form-tip">可以选择多个训练项目</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            创建活动
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 活动列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <h3>活动列表</h3>
        </div>
      </template>

      <el-table :data="events" style="width: 100%">
        <el-table-column prop="name" label="活动名称" />
        <el-table-column prop="time" label="活动时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.time) }}
          </template>
        </el-table-column>
        <el-table-column prop="uniform_required" label="着装要求" show-overflow-tooltip />
        <el-table-column label="关联训练" width="200">
          <template #default="scope">
            <el-tag
              v-for="training in scope.row.trainings"
              :key="training.training_id"
              size="small"
              style="margin-right: 5px"
            >
              {{ training.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button-group>
              <el-button
                type="primary"
                size="small"
                @click="handleEdit(scope.row)"
                :disabled="isEventPast(scope.row.time)"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)"
                :disabled="isEventPast(scope.row.time)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="'编辑活动 - ' + (currentEvent?.name || '')"
      width="50%"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="rules"
        label-width="100px"
        :disabled="submitting"
      >
        <el-form-item label="活动名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入活动名称" />
        </el-form-item>

        <el-form-item label="活动时间" prop="time">
          <el-date-picker
            v-model="editForm.time"
            type="datetime"
            placeholder="选择活动时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            :disabled-date="disabledDate"
          />
        </el-form-item>

        <el-form-item label="着装要求" prop="uniform_required">
          <el-input
            v-model="editForm.uniform_required"
            type="textarea"
            :rows="2"
            placeholder="请输入着装要求"
          />
        </el-form-item>

        <el-form-item label="关联训练" prop="trainings">
          <el-select
            v-model="editForm.trainings"
            multiple
            filterable
            placeholder="选择关联训练"
          >
            <el-option
              v-for="training in trainingOptions"
              :key="training.training_id"
              :label="training.name"
              :value="training.training_id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const formRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const submitting = ref(false)
const dialogVisible = ref(false)
const currentEvent = ref<Event | null>(null)
const isEdit = ref(false)

const form = ref<EventForm>({
  name: '',
  time: null,
  uniform_required: '',
  trainings: []
})

const editForm = ref<EventForm>({
  name: '',
  time: null,
  uniform_required: '',
  trainings: []
})

const rules = reactive<FormRules>({
  name: [
    { required: true, message: '请输入活动名称', trigger: 'blur' }
  ],
  time: [
    { required: true, message: '请选择活动时间', trigger: 'change' }
  ],
  uniform_required: [
    { required: true, message: '请输入着装要求', trigger: 'blur' }
  ]
})

interface Event {
  event_id: number
  name: string
  time: string | Date
  uniform_required: string
  created_by: number
  created_at: string
  trainings: Array<{
    training_id: number
    name: string
  }>
  is_registered?: boolean
}

interface Training {
  training_id: number
  name: string
}

interface EventForm {
  name: string
  time: Date | null
  uniform_required: string
  trainings: number[]
}

const loading = ref(false)
const events = ref<Event[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const trainingOptions = ref<Training[]>([])

// 获取活动列表
const fetchEvents = async () => {
  loading.value = true
  try {
    const response = await request.get('/events')
    console.log('获取活动列表响应:', response.data)  // 添加调试日志
    
    if (response.data && response.data.data && response.data.data.items) {
      events.value = response.data.data.items.map((event: any) => {
        const processedEvent = {
          ...event,
          time: new Date(event.time).toLocaleString(),
          is_registered: Boolean(event.is_registered)
        }
        console.log('处理后的活动数据:', processedEvent)  // 添加调试日志
        return processedEvent
      })
    } else {
      console.warn('无效的活动数据格式:', response.data)  // 添加调试日志
      events.value = []
    }
  } catch (error) {
    console.error('获取活动列表失败:', error)  // 添加调试日志
    ElMessage.error('获取活动列表失败')
    events.value = []
  } finally {
    loading.value = false
  }
}

// 获取训练选项
const fetchTrainingOptions = async () => {
  try {
    const response = await request.get('/trainings/options')
    trainingOptions.value = response.data
  } catch (error) {
    ElMessage.error('获取训练选项失败')
  }
}

// 禁用过去的日期
const disabledDate = (time: Date) => {
  return time.getTime() < Date.now() - 8.64e7 // 禁用今天之前的日期
}

// 判断活动是否已过期
const isEventPast = (time: string) => {
  return new Date(time).getTime() < Date.now()
}

// 格式化时间为后端需要的格式（保持本地时区）
const formatDateTimeForBackend = (date: Date | string) => {
  const d = new Date(date)
  // 获取本地时区偏移（分钟）
  const timezoneOffset = d.getTimezoneOffset()
  // 创建一个新的Date对象，调整时区偏移
  const localDate = new Date(d.getTime() - (timezoneOffset * 60000))
  // 返回ISO格式但保持本地时间
  return localDate.toISOString().slice(0, 19) + '+08:00'
}

// 解析后端返回的时间字符串
const parseBackendDateTime = (timeStr: string | Date) => {
  if (timeStr instanceof Date) {
    return timeStr
  }
  // 如果时间字符串包含时区信息，直接解析
  if (timeStr.includes('+') || timeStr.includes('Z')) {
    return new Date(timeStr)
  }
  // 否则假设是本地时间
  return new Date(timeStr)
}

// 创建活动
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        // 处理时间格式 - 保持本地时区
        const formData = {
          ...form.value,
          time: form.value.time ? formatDateTimeForBackend(form.value.time) : null
        }
        
        console.log('提交的表单数据:', formData)  // 添加调试日志
        
        if (isEdit.value && currentEvent.value) {
          const response = await request.put(`/events/${currentEvent.value.event_id}`, formData)
          console.log('更新活动响应:', response.data)  // 添加调试日志
          ElMessage.success('更新成功')
        } else {
          const response = await request.post('/events', formData)
          console.log('创建活动响应:', response.data)  // 添加调试日志
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await fetchEvents()
      } catch (error: any) {
        console.error('提交表单失败:', error)  // 添加调试日志
        ElMessage.error(error.response?.data?.msg || (isEdit.value ? '更新失败' : '创建失败'))
      }
    }
  })
}

// 编辑活动
const handleEdit = (event: Event) => {
  isEdit.value = true
  currentEvent.value = event
  editForm.value = {
    name: event.name,
    time: parseBackendDateTime(event.time),  // 正确解析后端时间
    uniform_required: event.uniform_required || '',
    trainings: event.trainings.map(t => t.training_id)
  }
  dialogVisible.value = true
}

// 删除活动
const handleDelete = async (event: Event) => {
  try {
    await ElMessageBox.confirm('确定要删除该活动吗？', '提示', {
      type: 'warning'
    })
    
    const response = await request.delete(`/events/${event.event_id}`)
    console.log('删除活动响应:', response.data)  // 添加调试日志
    
    if (response.data.code === 200) {
      ElMessage.success('删除成功')
      await fetchEvents()
    } else {
      ElMessage.error(response.data.msg || '删除失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除活动失败:', error)  // 添加调试日志
      ElMessage.error(error.response?.data?.msg || '删除失败')
    }
  }
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchEvents()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchEvents()
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  fetchEvents()
  fetchTrainingOptions()
})

// 监听对话框关闭
watch(dialogVisible, (val) => {
  if (!val) {
    currentEvent.value = null
    editForm.value = {
      name: '',
      time: null,
      uniform_required: '',
      trainings: []
    }
  }
})
</script>

<style scoped>
.event-manage-container {
  padding: 20px;
}

.create-card,
.list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style> 