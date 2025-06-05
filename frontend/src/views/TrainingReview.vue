<template>
  <div class="training-review-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>训练考勤审核</h3>
          <el-radio-group v-model="filterStatus" @change="fetchTrainings">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="pending">待审核</el-radio-button>
            <el-radio-button label="reviewed">已审核</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="trainings" style="width: 100%">
        <el-table-column prop="name" label="训练名称" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="scope">
            {{ getTrainingTypeText(scope.row.type) }}
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="points" label="积分" width="80" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button
              v-if="!scope.row.reviewed"
              type="primary"
              size="small"
              @click="handleReview(scope.row)"
            >
              考勤
            </el-button>
            <el-tag v-else type="success">已审核</el-tag>
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

    <!-- 考勤对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentTraining ? currentTraining.name + ' - 考勤' : '考勤'"
      width="70%"
    >
      <el-table
        v-if="currentTraining"
        ref="attendanceTableRef"
        :data="attendanceList"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="user.name" label="姓名" width="120" />
        <el-table-column prop="user.student_id" label="学号" width="120" />
        <el-table-column prop="user.college" label="学院" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.attended ? 'success' : ''">
              {{ scope.row.attended ? '已到' : '未到' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="points_awarded" label="获得积分" width="100">
          <template #default="scope">
            {{ scope.row.attended ? currentTraining.points : 0 }}
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAttendance" :loading="submitting">
            提交
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

interface Training {
  training_id: number;
  name: string;
  type: string;
  start_time: string;
  end_time: string;
  points: number;
  reviewed: boolean;
}

interface AttendanceRecord {
  user_id: number;
  name: string;
  student_id: string;
  college: string;
  attended: boolean;
}

// 列表数据
const trainings = ref<Training[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('all')

// 考勤相关
const dialogVisible = ref(false)
const currentTraining = ref<Training | null>(null)
const attendanceList = ref<AttendanceRecord[]>([])
const selectedAttendees = ref<AttendanceRecord[]>([])
const submitting = ref(false)

// 获取训练列表
const fetchTrainings = async () => {
  try {
    const response = await request.get('/trainings/review', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        status: filterStatus.value === 'all' ? undefined : filterStatus.value
      }
    })
    trainings.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取训练列表失败')
  }
}

// 获取考勤名单
const fetchAttendanceList = async (trainingId: number) => {
  try {
    const response = await request.get(`/trainings/${trainingId}/attendance`)
    attendanceList.value = response.data
    // 预选已到人员
    const attendanceTableRef = ref()
    attendanceList.value.forEach((item: any, index: number) => {
      if (item.attended) {
        attendanceTableRef.value?.toggleRowSelection(attendanceList.value[index], true)
      }
    })
  } catch (error) {
    ElMessage.error('获取考勤名单失败')
  }
}

// 处理考勤
const handleReview = async (training: any) => {
  currentTraining.value = training
  await fetchAttendanceList(training.training_id)
  dialogVisible.value = true
}

// 处理选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedAttendees.value = selection
}

// 提交考勤
const submitAttendance = async () => {
  if (!currentTraining.value) return
  
  submitting.value = true
  try {
    const attendees = selectedAttendees.value.map(item => item.user_id)
    await request.post(`/trainings/${currentTraining.value.training_id}/attendance`, {
      attendees
    })
    ElMessage.success('考勤提交成功')
    dialogVisible.value = false
    fetchTrainings()
  } catch (error: any) {
    if (error.response?.data?.error === '该训练已经审核过，不能重复审核') {
      ElMessage.error('该训练已经审核过，不能重复审核')
      dialogVisible.value = false
      fetchTrainings()
    } else {
      ElMessage.error(error.response?.data?.error || '提交失败')
    }
  } finally {
    submitting.value = false
  }
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchTrainings()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchTrainings()
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

// 获取训练类型文本
const getTrainingTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    regular: '常规训练',
    special: '专项训练',
    competition: '赛前训练'
  }
  return typeMap[type] || type
}

onMounted(() => {
  fetchTrainings()
})
</script>

<style scoped>
.training-review-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
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