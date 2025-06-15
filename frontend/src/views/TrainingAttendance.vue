<template>
  <div class="attendance-container">
    <div class="header">
      <h2>考勤名单</h2>
      <el-button @click="goBack">返回</el-button>
    </div>

    <el-card class="table-card">
      <el-table 
        :data="attendanceList" 
        style="width: 100%" 
        v-loading="loading"
        border
        stripe
        highlight-current-row
      >
        <el-table-column prop="user_id" label="学号" min-width="120" />
        <el-table-column prop="username" label="姓名" min-width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="报名时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import dayjs from 'dayjs'

interface Attendance {
  user_id: string
  username: string
  status: string
  created_at: string
}

const route = useRoute()
const router = useRouter()
const trainingId = route.params.id
const attendanceList = ref<Attendance[]>([])
const loading = ref(false)

// 获取考勤名单
const fetchAttendanceList = async () => {
  loading.value = true
  try {
    const response = await request.get(`/trainings/${trainingId}/attendance`)
    attendanceList.value = response.data
  } catch (error) {
    console.error('获取考勤名单失败:', error)
    ElMessage.error('获取考勤名单失败')
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return ''
  // 将UTC时间转换为本地时间 (UTC+8)
  return dayjs(date).add(8, 'hour').format('YYYY-MM-DD HH:mm:ss')
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'registered':
      return 'info'
    case 'attended':
      return 'success'
    case 'absent':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'registered':
      return '已报名'
    case 'attended':
      return '已签到'
    case 'absent':
      return '缺勤'
    default:
      return '未知'
  }
}

// 返回上一页
const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchAttendanceList()
})
</script>

<style scoped>
.attendance-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.table-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}
</style> 