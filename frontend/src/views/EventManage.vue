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
        :model="eventForm"
        :rules="rules"
        label-width="100px"
        :disabled="submitting"
      >
        <el-form-item label="活动名称" prop="name">
          <el-input v-model="eventForm.name" placeholder="请输入活动名称" />
        </el-form-item>

        <el-form-item label="活动时间" prop="time">
          <el-date-picker
            v-model="eventForm.time"
            type="datetime"
            placeholder="选择活动时间"
            :disabled-date="disabledDate"
          />
        </el-form-item>

        <el-form-item label="着装要求" prop="uniform_required">
          <el-input
            v-model="eventForm.uniform_required"
            type="textarea"
            :rows="2"
            placeholder="请输入着装要求"
          />
        </el-form-item>

        <el-form-item label="关联训练" prop="trainings">
          <el-select
            v-model="eventForm.trainings"
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
          <el-button type="primary" @click="submitEvent" :loading="submitting">
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
          <el-button type="primary" @click="submitEdit" :loading="submitting">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const formRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const submitting = ref(false)
const dialogVisible = ref(false)
const currentEvent = ref(null)

// 表单数据
const eventForm = ref({
  name: '',
  time: '',
  uniform_required: '',
  trainings: []
})

const editForm = ref({
  name: '',
  time: '',
  uniform_required: '',
  trainings: []
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入活动名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  time: [
    { required: true, message: '请选择活动时间', trigger: 'change' }
  ],
  uniform_required: [
    { required: true, message: '请输入着装要求', trigger: 'blur' }
  ]
}

// 列表数据
const events = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const trainingOptions = ref([])

// 获取活动列表
const fetchEvents = async () => {
  try {
    const response = await request.get('/events', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value
      }
    })
    events.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取活动列表失败')
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

// 创建活动
const submitEvent = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await request.post('/events', eventForm.value)
        ElMessage.success('活动创建成功')
        // 重置表单
        eventForm.value = {
          name: '',
          time: '',
          uniform_required: '',
          trainings: []
        }
        // 刷新列表
        fetchEvents()
      } catch (error) {
        ElMessage.error('创建失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 编辑活动
const handleEdit = (event: any) => {
  currentEvent.value = event
  editForm.value = {
    name: event.name,
    time: event.time,
    uniform_required: event.uniform_required,
    trainings: event.trainings.map((t: any) => t.training_id)
  }
  dialogVisible.value = true
}

// 提交编辑
const submitEdit = async () => {
  if (!editFormRef.value || !currentEvent.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await request.put(`/events/${currentEvent.value.event_id}`, editForm.value)
        ElMessage.success('更新成功')
        dialogVisible.value = false
        fetchEvents()
      } catch (error) {
        ElMessage.error('更新失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 删除活动
const handleDelete = async (event: any) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个活动吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await request.delete(`/events/${event.event_id}`)
    ElMessage.success('删除成功')
    fetchEvents()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
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