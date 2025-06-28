<template>
  <div class="points-container">
    <div class="header-controls">
      <h1 class="page-title">积分记录</h1>
      <div class="filter-group">
        <el-select v-model="filterType" placeholder="选择类型" clearable @change="fetchPointHistory">
          <el-option label="升降旗" value="flag" />
          <el-option label="训练" value="training" />
          <el-option label="活动" value="event" />
        </el-select>
      </div>
    </div>
    <el-divider />

    <div class="points-summary">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="当前总积分">
          <span class="total-points">{{ totalPoints }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="本月获得积分">
          <span class="monthly-points">{{ monthlyPoints }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="上月获得积分">
          <span class="last-monthly-points">{{ lastMonthPoints }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <el-table :data="pointHistory" style="width: 100%; margin-top: 20px">
      <el-table-column prop="change_time" label="时间" width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.change_time) }}
        </template>
      </el-table-column>
      <el-table-column prop="change_type" label="类型" width="120">
        <template #default="scope">
          {{ getChangeTypeText(scope.row.change_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="points_change" label="积分变动" width="120">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import { formatDateTime } from '../utils/format'

// 定义类型
interface PointHistoryItem {
  history_id: number;
  user_id: number;
  points_change: number;
  change_type: string;
  description: string;
  related_id: number | null;
  change_time: string;
}

interface PointHistoryResponse {
  items: PointHistoryItem[];
  total: number;
  pages: number;
  current_page: number;
  total_points: number;
}

interface PointStatisticsResponse {
  total_points: number;
  monthly_points: number;
  last_month_points: number;
  recent_history: PointHistoryItem[];
}

// 数据
const pointHistory = ref<PointHistoryItem[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterType = ref('')
const totalPoints = ref(0)
const monthlyPoints = ref(0)
const lastMonthPoints = ref(0)

// 获取积分历史
const fetchPointHistory = async () => {
  try {
    const response = await request.get<PointHistoryResponse>('/points/history', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        type: filterType.value
      }
    })
    if (response && response.data) {
      const { items = [], total: totalCount = 0 } = response.data
      pointHistory.value = items
      total.value = totalCount
    } else {
      ElMessage.error('获取积分历史失败：数据格式错误')
    }
  } catch (error) {
    ElMessage.error('获取积分历史失败')
  }
}

// 获取积分统计
const fetchPointsStatistics = async () => {
  try {
    const response = await request.get<PointStatisticsResponse>('/points/statistics')
    if (response && response.data) {
      totalPoints.value = response.data.total_points || 0
      monthlyPoints.value = response.data.monthly_points || 0
      lastMonthPoints.value = response.data.last_month_points || 0
    } else {
      ElMessage.error('获取积分统计失败：数据格式错误')
    }
  } catch (error) {
    ElMessage.error('获取积分统计失败')
  }
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchPointHistory()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchPointHistory()
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
  fetchPointHistory()
  fetchPointsStatistics()
})
</script>

<style scoped>
.points-container {
  padding: 20px;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  margin: 0;
}

.points-summary {
  margin-bottom: 20px;
}

.total-points {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.monthly-points,
.last-monthly-points {
  font-size: 18px;
  color: #67C23A;
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