<template>
  <div class="points-manage-container">
    <!-- 手动调整积分表单 -->
    <el-card class="adjust-card">
      <template #header>
        <div class="card-header">
          <h3>积分调整</h3>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="adjustForm"
        :rules="rules"
        label-width="100px"
        :disabled="submitting"
      >
        <el-form-item label="用户" prop="user_id">
          <el-select
            v-model="adjustForm.user_id"
            filterable
            remote
            :remote-method="searchUsers"
            :loading="loading"
            placeholder="请输入用户名或学号搜索"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.user_id"
              :label="user.name + ' (' + user.student_id + ')'"
              :value="user.user_id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="积分变动" prop="points_change">
          <el-input-number
            v-model="adjustForm.points_change"
            :precision="0"
            :step="1"
            placeholder="输入积分变动值"
          />
          <span class="points-tip">正数为增加，负数为减少</span>
        </el-form-item>

        <el-form-item label="变动类型" prop="change_type">
          <el-select v-model="adjustForm.change_type" placeholder="选择变动类型">
            <el-option label="升降旗" value="flag" />
            <el-option label="训练" value="training" />
            <el-option label="活动" value="event" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="说明" prop="description">
          <el-input
            v-model="adjustForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入积分变动说明"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="submitAdjustment" :loading="submitting">
            提交调整
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 积分调整历史记录 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <h3>调整历史</h3>
          <div class="filter-group">
            <el-input
              v-model="searchQuery"
              placeholder="按用户名/姓名/学号搜索"
              clearable
              @clear="fetchHistory"
              @keyup.enter="fetchHistory"
              style="width: 240px; margin-right: 10px;"
            />
            <el-select v-model="filterType" placeholder="选择类型" clearable @change="fetchHistory">
              <el-option label="升降旗" value="flag" />
              <el-option label="训练" value="training" />
              <el-option label="活动" value="event" />
              <el-option label="其他" value="other" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="history" style="width: 100%">
        <el-table-column prop="change_time" label="时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.change_time) }}
          </template>
        </el-table-column>
        <el-table-column label="用户" width="180">
          <template #default="scope">
            {{ scope.row.user?.name }} ({{ scope.row.user?.student_id }})
          </template>
        </el-table-column>
        <el-table-column prop="change_type" label="类型" width="100">
          <template #default="scope">
            {{ getChangeTypeText(scope.row.change_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="points_change" label="积分变动" width="100">
          <template #default="scope">
            <span :class="scope.row.points_change >= 0 ? 'positive' : 'negative'">
              {{ scope.row.points_change >= 0 ? '+' : '' }}{{ scope.row.points_change }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import { formatDateTime } from '../utils/format'

interface UserOption {
  user_id: number
  name: string
  student_id: string
}

const formRef = ref<FormInstance>()
const submitting = ref(false)
const loading = ref(false)
const userOptions = ref<UserOption[]>([])

// 表单数据
const adjustForm = ref({
  user_id: '',
  points_change: 0,
  change_type: '',
  description: ''
})

// 表单验证规则
const rules: FormRules = {
  user_id: [
    { required: true, message: '请选择用户', trigger: 'change' }
  ],
  points_change: [
    { required: true, message: '请输入积分变动值', trigger: 'blur' }
  ],
  change_type: [
    { required: true, message: '请选择变动类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入说明', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ]
}

// 历史记录数据
const history = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterType = ref('')
const searchQuery = ref('')

// 搜索用户
const searchUsers = async (query: string) => {
  if (query) {
    loading.value = true
    try {
      const { data: responseData } = await request.get('/users/search', {
        params: { query }
      })
      console.log('Search response:', responseData)
      if (responseData) {
        userOptions.value = responseData
      } else {
        userOptions.value = []
      }
    } catch (error) {
      console.error('Search users error:', error)
      ElMessage.error('搜索用户失败')
      userOptions.value = []
    } finally {
      loading.value = false
    }
  } else {
    userOptions.value = []
  }
}

// 获取积分调整历史记录
const fetchHistory = async () => {
  try {
    const { data: responseData } = await request.get('/points/history/all', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        type: filterType.value || undefined,
        query: searchQuery.value || undefined
      }
    })
    console.log('History response:', responseData)
    if (responseData && responseData.items) {
      history.value = responseData.items
      total.value = responseData.total
    } else {
      console.error('Invalid response format:', responseData)
      ElMessage.error('获取历史记录失败：响应格式错误')
    }
  } catch (error: any) {
    console.error('Error fetching history:', error)
    ElMessage.error(error.response?.data?.msg || '获取历史记录失败')
  }
}

// 提交积分调整
const submitAdjustment = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        await request.post('/points/adjust', adjustForm.value)
        ElMessage.success('积分调整成功')
        // 重置表单
        adjustForm.value = {
          user_id: '',
          points_change: 0,
          change_type: '',
          description: ''
        }
        // 刷新历史记录
        await fetchHistory()
      } catch (error: any) {
        console.error('Error submitting adjustment:', error)
        ElMessage.error(error.response?.data?.msg || '积分调整失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchHistory()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchHistory()
}

// 获取变动类型文本
const getChangeTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    flag: '升降旗',
    training: '训练',
    event: '活动',
    other: '其他',
    training_award: '训练'
  }
  return typeMap[type] || type
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.points-manage-container {
  padding: 20px;
}

.adjust-card,
.history-card {
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

.points-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 14px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style> 