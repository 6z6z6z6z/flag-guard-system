// @ts-nocheck
<template>
  <div class="trainings-container">
    <div class="header">
      <h2>训练管理</h2>
      <el-button v-if="userStore.isAdmin" type="primary" @click="handleCreate">
        创建训练
      </el-button>
    </div>

    <el-table :data="trainings" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="训练名称" />
      <el-table-column prop="type" label="训练类型">
        <template #default="scope">
          {{ scope.row.type === 'regular' ? '常规训练' : '特殊训练' }}
        </template>
      </el-table-column>
      <el-table-column prop="start_time" label="开始时间">
        <template #default="scope">
          {{ formatDateTime(scope.row.start_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="end_time" label="结束时间">
        <template #default="scope">
          {{ formatDateTime(scope.row.end_time) }}
          <el-tag 
            v-if="isTrainingEnded(scope.row)" 
            type="danger" 
            size="small" 
            style="margin-left: 8px"
          >
            已结束
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="points" label="积分" />
      <el-table-column label="操作" width="360">
        <template #default="{ row }">
          <el-button-group>
            <el-button 
              v-if="!row.registered" 
              type="primary" 
              size="small" 
              @click="handleRegister(row)"
              :disabled="isTrainingEnded(row)"
            >
              报名
            </el-button>
            <el-button 
              v-else 
              type="danger" 
              size="small" 
              @click="handleCancelRegister(row)"
              :disabled="isTrainingEnded(row) || row.status === 'awarded'"
            >
              取消报名
            </el-button>
            <el-button 
              v-if="userStore.isAdmin" 
              type="primary" 
              size="small" 
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button 
              v-if="userStore.isAdmin" 
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
            >
              删除
            </el-button>
            <el-button 
              v-if="userStore.isAdmin" 
              type="info" 
              size="small" 
              @click="handleViewRegistrations(row)"
            >
              报名名单
            </el-button>
            <el-button 
              v-if="userStore.isAdmin" 
              type="warning" 
              size="small" 
              @click="handleReviewAttendance(row)"
              :disabled="row.reviewed"
            >
              审核考勤
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="训练名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="训练类型" prop="type">
          <el-select v-model="form.type" style="width: 100%">
            <el-option label="常规训练" value="regular" />
            <el-option label="特殊训练" value="special" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择开始时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            placeholder="选择结束时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="积分" prop="points">
          <el-input-number v-model="form.points" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 报名名单对话框 -->
    <el-dialog
      title="报名名单"
      v-model="registrationDialogVisible"
      width="800px"
    >
      <el-table :data="registrations" style="width: 100%">
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="student_id" label="学号" />
        <el-table-column prop="college" label="学院" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.status === 'awarded' ? 'success' : 'warning'"
            >
              {{ row.status === 'awarded' ? '已参加' : '已报名' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="考勤" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.attendance_status === 'present' ? 'success' : 'danger'"
            >
              {{ row.attendance_status === 'present' ? '已到' : '未到' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="points_awarded" label="获得积分" width="100">
          <template #default="{ row }">
            {{ row.points_awarded || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 考勤审核对话框 -->
    <el-dialog
      title="考勤审核"
      v-model="attendanceDialogVisible"
      width="800px"
    >
      <el-table :data="attendanceList" style="width: 100%">
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="student_id" label="学号" />
        <el-table-column prop="college" label="学院" />
        <el-table-column label="考勤状态" width="200">
          <template #default="{ row }">
            <el-select v-model="row.attendance_status" style="width: 100%">
              <el-option label="未到" value="absent" />
              <el-option label="出勤" value="present" />
              <el-option label="迟到" value="late" />
              <el-option label="早退" value="early_leave" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'awarded' ? 'success' : 'warning'">
              {{ row.status === 'awarded' ? '已审核' : '未审核' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="attendanceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAttendance">提交审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import request from '../utils/request'
import { useUserStore } from '../stores/user'

interface Training {
  training_id: number;
  name: string;
  type: string;
  start_time: string;
  end_time: string | null;
  points: number;
  created_by: number;
  registered?: boolean;
  status?: string | null;
  reviewed?: boolean;
}

interface Registration {
  user_id: number;
  name: string;
  student_id: string;
  college: string;
  status: string;
  attended: boolean;
  points_awarded: number | null;
}

interface AttendanceRecord {
  user_id: number;
  name: string;
  student_id: string;
  college: string;
  attendance_status: string;
  status: string;
  points_awarded: number | null;
}

const trainings = ref<Training[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const registrations = ref<Registration[]>([])
const registrationDialogVisible = ref(false)
const currentTraining = ref<Training | null>(null)
const attendanceDialogVisible = ref(false)
const attendanceList = ref<AttendanceRecord[]>([])
const currentAttendanceTraining = ref<Training | null>(null)
const form = ref({
  training_id: null as number | null,
  name: '',
  type: 'regular',
  start_time: '',
  end_time: '',
  points: 1
})

const userStore = useUserStore()

const rules = {
  name: [{ required: true, message: '请输入训练名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择训练类型', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  points: [{ required: true, message: '请输入积分', trigger: 'change' }]
}

const fetchTrainings = async () => {
  loading.value = true
  try {
    const response = await request.get('/trainings')
    if (response.data) {
      trainings.value = response.data.map((training: any) => {
        return {
          ...training,
          registered: Boolean(training.registered)  // 确保转换为布尔值
        }
      })
    }
  } catch (error) {
    ElMessage.error('获取训练列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  dialogTitle.value = '创建训练'
  form.value = {
    training_id: null,
    name: '',
    type: 'regular',
    start_time: '',
    end_time: '',
    points: 1
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑训练'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个训练吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/trainings/${row.training_id}`)
    ElMessage.success('删除成功')
    fetchTrainings()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        // 处理日期时间格式
        const formData = {
          ...form.value,
          start_time: form.value.start_time ? new Date(form.value.start_time).toISOString() : null,
          end_time: form.value.end_time ? new Date(form.value.end_time).toISOString() : null
        }
        
        console.log('提交的表单数据:', formData)  // 添加调试日志
        
        if (form.value.training_id) {
          await request.put(`/trainings/${form.value.training_id}`, formData)
          ElMessage.success('更新成功')
        } else {
          const response = await request.post('/trainings', formData)
          console.log('创建训练响应:', response.data)  // 添加调试日志
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        await fetchTrainings()  // 重新获取训练列表
      } catch (error: any) {
        console.error('提交表单失败:', error)  // 添加调试日志
        ElMessage.error(error.response?.data?.error || (form.value.training_id ? '更新失败' : '创建失败'))
      }
    }
  })
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  // 添加8小时时区偏移
  date.setHours(date.getHours() + 8)
  return date.toLocaleString()
}

// 检查训练是否已结束
const isTrainingEnded = (training: any) => {
  if (!training.end_time) return false
  const now = new Date()
  const endTime = new Date(training.end_time)
  // 添加8小时时区偏移
  endTime.setHours(endTime.getHours() + 8)
  return endTime < now
}

// 报名训练
const handleRegister = async (training: any) => {
  try {
    const response = await request.post(`/trainings/${training.training_id}/register`)
    if (response.data?.message === 'Successfully registered for training') {
      ElMessage.success('报名成功')
      training.registered = true
    } else {
      ElMessage.error(response.data?.message || '报名失败')
    }
  } catch (error) {
    ElMessage.error('报名失败')
  }
}

// 取消报名
const handleCancelRegister = async (training: any) => {
  try {
    const response = await request.post(`/trainings/${training.training_id}/cancel`)
    if (response.data?.message === 'Successfully cancelled registration') {
      ElMessage.success('取消报名成功')
      training.registered = false
    } else {
      ElMessage.error(response.data?.message || '取消报名失败')
    }
  } catch (error) {
    ElMessage.error('取消报名失败')
  }
}

// 查看报名名单
const handleViewRegistrations = async (training: Training) => {
  try {
    currentTraining.value = training
    const response = await request.get(`/trainings/${training.training_id}/registrations`)
    registrations.value = response.data
    registrationDialogVisible.value = true
  } catch (error: any) {
    console.error('获取报名名单失败:', error)
    ElMessage.error(error.response?.data?.error || '获取报名名单失败')
  }
}

// 审核考勤
const handleReviewAttendance = async (training: Training) => {
  try {
    console.log('当前用户信息:', userStore.userInfo)  // 使用正确的属性名
    console.log('用户是否为管理员:', userStore.isAdmin)
    
    if (!userStore.isAdmin) {
      ElMessage.error('只有管理员可以审核考勤')
      return
    }
    
    currentAttendanceTraining.value = training
    const response = await request.get(`/trainings/${training.training_id}/attendance`)
    attendanceList.value = response.data
    attendanceDialogVisible.value = true
  } catch (error: any) {
    console.error('获取考勤名单失败:', error)
    ElMessage.error(error.response?.data?.error || '获取考勤名单失败')
  }
}

const submitAttendance = async () => {
  if (!currentAttendanceTraining.value) return
  try {
    const attendance_records = attendanceList.value.map(record => ({
      user_id: record.user_id,
      attendance_status: record.attendance_status
    }))
    
    await request.post(`/trainings/${currentAttendanceTraining.value.training_id}/attendance`, {
      attendance_records
    })
    ElMessage.success('考勤审核成功')
    attendanceDialogVisible.value = false
    await fetchTrainings()
  } catch (error: any) {
    console.error('提交考勤失败:', error)
    ElMessage.error(error.response?.data?.error || '提交考勤失败')
  }
}

onMounted(async () => {
  await fetchTrainings()
})
</script>

<style scoped>
.trainings-container {
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
</style> 