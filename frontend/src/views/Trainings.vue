// @ts-nocheck
<template>
  <div class="trainings-container">
    <!-- 创建训练表单 -->
    <el-card class="create-card" v-if="isAdmin">
      <template #header>
        <div class="card-header">
          <h3>创建训练</h3>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        :disabled="submitting"
      >
        <el-form-item label="训练名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入训练名称" />
        </el-form-item>

        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择开始时间"
            value-format="YYYY-MM-DD HH:mm"
            format="YYYY-MM-DD HH:mm"
            @change="handleStartTimeChange"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            placeholder="选择结束时间"
            value-format="YYYY-MM-DD HH:mm"
            format="YYYY-MM-DD HH:mm"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="积分" prop="points">
          <el-input-number v-model="form.points" :min="1" style="width: 100%" />
        </el-form-item>

        <el-form-item label="地点" prop="location">
          <el-input v-model="form.location" placeholder="请输入训练地点" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            创建训练
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 训练列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <h3>训练列表</h3>
        </div>
      </template>

      <el-table 
        :data="trainings" 
        style="width: 100%" 
        v-loading="loading"
        border
        stripe
      >
        <el-table-column prop="name" label="训练名称" min-width="120" />
        <el-table-column prop="start_time" label="开始时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" min-width="160">
          <template #default="{ row }">
            {{ formatDate(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="points" label="积分" width="80" align="center" />
        <el-table-column prop="location" label="地点" min-width="120" />
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <div class="operation-buttons">
              <el-button-group>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="handleEdit(row)"
                  :disabled="isActionDisabled(row)"
                  v-if="isAdmin"
                >
                  编辑
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="handleDelete(row.training_id)"
                  :disabled="isActionDisabled(row)"
                  v-if="isAdmin"
                >
                  删除
                </el-button>
              </el-button-group>
              <el-button-group>
                <el-button 
                  type="success" 
                  size="small" 
                  @click="handleRegister(row)"
                  v-if="!row.is_registered"
                  :disabled="isTrainingStarted(row.start_time)"
                >
                  报名
                </el-button>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="handleCancelRegister(row)"
                  v-if="row.is_registered"
                  :disabled="isTrainingStarted(row.start_time)"
                >
                  取消报名
                </el-button>
                <el-button 
                  type="info" 
                  size="small" 
                  @click="handleViewRegistrations(row)"
                  v-if="isAdmin"
                >
                  查看报名
                </el-button>
              </el-button-group>
            </div>
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
      :title="'编辑训练 - ' + (currentTraining?.name || '')"
      width="50%"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="rules"
        label-width="100px"
        :disabled="submitting"
      >
        <el-form-item label="训练名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入训练名称" />
        </el-form-item>

        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="editForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            value-format="YYYY-MM-DD HH:mm"
            format="YYYY-MM-DD HH:mm"
            @change="handleStartTimeChange"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="editForm.end_time"
            type="datetime"
            placeholder="选择结束时间"
            value-format="YYYY-MM-DD HH:mm"
            format="YYYY-MM-DD HH:mm"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="积分" prop="points">
          <el-input-number v-model="editForm.points" :min="1" style="width: 100%" />
        </el-form-item>

        <el-form-item label="地点" prop="location">
          <el-input v-model="editForm.location" placeholder="请输入训练地点" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleUpdate" :loading="submitting">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 报名名单对话框 -->
    <el-dialog
      v-model="registrationsDialogVisible"
      title="报名名单"
      width="80%"
    >
      <el-table :data="currentRegistrations" style="width: 100%">
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="college" label="学院" />
        <el-table-column prop="created_at" label="报名时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="attendance_status" label="出勤状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="getAttendanceStatusType(row.attendance_status)"
              v-if="row.attendance_status"
            >
              {{ getAttendanceStatusText(row.attendance_status) }}
            </el-tag>
            <span v-else>未审核</span>
          </template>
        </el-table-column>
        <el-table-column prop="points_awarded" label="获得积分" width="100">
          <template #default="{ row }">
            {{ row.points_awarded || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" v-if="isAdmin">
          <template #default="{ row }">
            <el-select 
              v-model="row.attendance_status" 
              placeholder="考勤状态"
              @change="(status: string) => handleUpdateAttendance(row.registration_id, status)"
            >
              <el-option label="出勤" value="present" />
              <el-option label="缺勤" value="absent" />
              <el-option label="迟到" value="late" />
              <el-option label="早退" value="early_leave" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="registrationsDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmAttendance" :loading="submitting">确认考勤</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTrainingStore } from '@/stores/training'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Training, Registration } from '@/types/training'
import { formatDate, isTrainingStarted } from '@/utils/formatDate'

const trainingStore = useTrainingStore()
const userStore = useUserStore()

const { trainings, total, loading } = storeToRefs(trainingStore)
const { isAdmin } = storeToRefs(userStore)

const currentPage = ref(1)
const pageSize = ref(10)

const formRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const dialogVisible = ref(false)
const registrationsDialogVisible = ref(false)
const submitting = ref(false)

const form = ref({
  name: '',
  start_time: '',
  end_time: '',
  points: 1,
  location: '',
})

const editForm = ref<Partial<Training>>({})
const currentTraining = ref<Training | null>(null)
const currentRegistrations = ref<Registration[]>([])

const rules = ref<FormRules>({
  name: [{ required: true, message: '请输入训练名称', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  points: [{ required: true, message: '请输入积分', trigger: 'blur' }],
  location: [{ required: true, message: '请输入地点', trigger: 'blur' }],
})

const fetchTrainings = () => {
  trainingStore.getTrainings(currentPage.value, pageSize.value)
}

onMounted(fetchTrainings)

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchTrainings()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchTrainings()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await trainingStore.createTraining(form.value)
        ElMessage.success('创建成功')
        formRef.value?.resetFields()
        fetchTrainings()
      } catch (error) {
        ElMessage.error('创建失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleEdit = (row: Training) => {
  currentTraining.value = row
  editForm.value = { ...row }
  dialogVisible.value = true
}

const handleUpdate = async () => {
  if (!editFormRef.value) return
  if (!currentTraining.value) {
    ElMessage.error('没有选中的训练，无法更新')
    return
  }

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      const trainingId = currentTraining.value?.training_id
      if (!trainingId) {
        ElMessage.error("无法获取训练ID")
        return
      }

      submitting.value = true
      try {
        await trainingStore.updateTraining(trainingId, editForm.value)
        ElMessage.success('更新成功')
        dialogVisible.value = false
        fetchTrainings()
      } catch (error) {
        ElMessage.error('更新失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDelete = async (trainingId: number) => {
  await ElMessageBox.confirm('确定删除这项训练吗？', '提示', {
    type: 'warning',
  })
  try {
    await trainingStore.deleteTraining(trainingId)
    ElMessage.success('删除成功')
    fetchTrainings()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleRegister = async (row: Training) => {
  try {
    await trainingStore.registerTraining(row.training_id)
    ElMessage.success('报名成功')
    fetchTrainings()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '报名失败')
  }
}

const handleCancelRegister = async (row: Training) => {
  try {
    await trainingStore.cancelRegister(row.training_id)
    ElMessage.success('取消报名成功')
    fetchTrainings()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '取消报名失败')
  }
}

const handleViewRegistrations = async (row: Training) => {
  try {
    currentTraining.value = row;
    currentRegistrations.value = await trainingStore.getRegistrations(row.training_id)
    registrationsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取报名列表失败')
  }
}

const handleStartTimeChange = (val: string) => {
  if (val && !form.value.end_time) {
    const startTime = new Date(val)
    const endTime = new Date(startTime.getTime() + 2 * 60 * 60 * 1000) // 默认2小时
    form.value.end_time = formatDate(endTime.toISOString())
  }
}

// --- Helper functions for attendance ---

const getAttendanceStatusType = (status: string | null) => {
  switch (status) {
    case 'present': return 'success';
    case 'late':
    case 'early_leave': return 'warning';
    case 'absent': return 'danger';
    default: return 'info';
  }
};

const getAttendanceStatusText = (status: string | null) => {
  switch (status) {
    case 'present': return '出勤';
    case 'late': return '迟到';
    case 'early_leave': return '早退';
    case 'absent': return '缺勤';
    default: return '未审核';
  }
};

const calculatePoints = (status: string, basePoints: number) => {
  switch (status) {
    case 'present': return basePoints;
    case 'late':
    case 'early_leave': return basePoints * 0.5;
    case 'absent': return 0;
    default: return 0;
  }
};

const handleUpdateAttendance = async (registrationId: number, status: string) => {
  if (!currentTraining.value) return;
  const points = calculatePoints(status, currentTraining.value.points);

  const index = currentRegistrations.value.findIndex(reg => reg.registration_id === registrationId);
  if (index !== -1) {
    currentRegistrations.value[index].attendance_status = status as any;
    currentRegistrations.value[index].points_awarded = points;
  }
};

const confirmAttendance = async () => {
  if (!currentTraining.value) return;
  
  const updates = currentRegistrations.value.map(reg => ({
    registration_id: reg.registration_id,
    attendance_status: reg.attendance_status,
    points_awarded: reg.points_awarded,
  }));

  submitting.value = true;
  try {
    await trainingStore.confirmAttendance(currentTraining.value.training_id, updates);
    ElMessage.success('出勤情况确认成功');
    registrationsDialogVisible.value = false;
    fetchTrainings();
  } catch (error) {
    ElMessage.error('确认考勤失败');
  } finally {
    submitting.value = false;
  }
};

const isActionDisabled = (training: any) => {
  if (userStore.isAdmin) {
    return false // 管理员始终可以操作
  }
  return new Date(training.end_time) < new Date()
}

</script>

<style scoped>
.trainings-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.create-card {
  margin-bottom: 20px;
}

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
  font-size: 18px;
  color: #303133;
}

.operation-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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

:deep(.el-button-group) {
  display: inline-flex;
}

:deep(.el-button-group .el-button) {
  margin: 0;
}
</style> 