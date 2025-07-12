<template>
  <div class="points-container">
    <div class="header-controls">
      <h1 class="page-title">积分记录</h1>
      <div class="filter-group">
        <el-select v-model="filterType" placeholder="选择类型" clearable @change="debouncedFetchPointHistory">
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

    <el-table :data="pointHistory" :loading="loading" style="width: 100%; margin-top: 20px">
      <el-table-column prop="change_time" label="时间" width="180">
        <template #default="scope">
          {{ scope.row?.change_time ? formatDateTime(scope.row.change_time) : '--' }}
        </template>
      </el-table-column>
      <el-table-column prop="change_type" label="类型" width="120">
        <template #default="scope">
          {{ getChangeTypeText(scope.row?.change_type || 'unknown') }}
        </template>
      </el-table-column>
      <el-table-column prop="points_change" label="积分变动" width="120">
        <template #default="scope">
          <span :class="(scope.row?.points_change || 0) >= 0 ? 'positive' : 'negative'">
            {{ (scope.row?.points_change || 0) >= 0 ? '+' : '' }}{{ scope.row?.points_change || 0 }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="说明">
        <template #default="scope">
          {{ scope.row?.description || '--' }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
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
const loading = ref(false)

// 请求控制
let historyController: AbortController | null = null
let statisticsController: AbortController | null = null
let fetchHistoryTimer: number | null = null

// 获取积分历史
const fetchPointHistory = async () => {
  // 防止重复请求
  if (loading.value) {
    console.log('Request already in progress, skipping...')
    return
  }
  
  // 取消之前的请求
  if (historyController) {
    historyController.abort()
  }
  
  historyController = new AbortController()
  loading.value = true
  
  try {
    console.log('Fetching point history...');
    const response = await request.get<PointHistoryResponse>('/points/history', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        type: filterType.value || undefined
      },
      signal: historyController.signal
    });
    
    console.log('Point history response:', response);
    
    if (response && response.code === 200) {
      const { items = [], total: totalCount = 0, total_points = 0 } = response.data || {};
      
      // 验证数据完整性
      const validItems = Array.isArray(items) ? items.filter(item => {
        try {
          return item && 
                 typeof item === 'object' && 
                 'points_change' in item &&
                 'change_type' in item &&
                 'description' in item;
        } catch (e) {
          console.warn('Invalid item detected:', item, e);
          return false;
        }
      }).map(item => {
        try {
          // 确保数据类型正确
          return {
            ...item,
            points_change: typeof item.points_change === 'number' ? item.points_change : parseFloat(item.points_change) || 0,
            change_type: String(item.change_type || 'unknown'),
            description: String(item.description || '--'),
            change_time: String(item.change_time || ''),
            history_id: typeof item.history_id === 'number' ? item.history_id : parseInt(String(item.history_id)) || 0,
            user_id: typeof item.user_id === 'number' ? item.user_id : parseInt(String(item.user_id)) || 0,
            related_id: item.related_id || null
          } as PointHistoryItem;
        } catch (e) {
          console.warn('Error processing item:', item, e);
          return {
            points_change: 0,
            change_type: 'unknown',
            description: '数据错误',
            change_time: '',
            history_id: 0,
            user_id: 0,
            related_id: null
          } as PointHistoryItem;
        }
      }) : [];
      
      pointHistory.value = validItems;
      total.value = Math.max(0, totalCount || 0);
      totalPoints.value = Math.max(0, total_points || 0);
      
      console.log(`Loaded ${validItems.length} valid items out of ${items.length} total`);
    } else {
      console.warn('Invalid point history response:', response);
      pointHistory.value = [];
      total.value = 0;
      totalPoints.value = 0;
      // 不显示错误提示，可能是管理员账户没有积分记录
    }
  } catch (error: any) {
    // 忽略被取消的请求
    if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
      console.log('Point history request was cancelled');
      return;
    }
    
    console.error('Error fetching point history:', error);
    pointHistory.value = [];
    total.value = 0;
    totalPoints.value = 0;
    // 静默处理错误，避免对管理员用户造成困扰
  } finally {
    loading.value = false
  }
}

// 防抖的获取积分历史函数
const debouncedFetchPointHistory = () => {
  if (fetchHistoryTimer) {
    clearTimeout(fetchHistoryTimer)
  }
  
  fetchHistoryTimer = window.setTimeout(() => {
    fetchPointHistory()
  }, 500) // 增加到500ms防抖间隔
}

// 获取积分统计
const fetchPointsStatistics = async () => {
  // 取消之前的请求
  if (statisticsController) {
    statisticsController.abort()
  }
  
  statisticsController = new AbortController()
  
  try {
    console.log('Fetching point statistics...');
    const response = await request.get<PointStatisticsResponse>('/points/statistics', {
      signal: statisticsController.signal
    });
    
    console.log('Point statistics response:', response);
    
    if (response && response.code === 200 && response.data) {
      totalPoints.value = response.data.total_points || 0;
      monthlyPoints.value = response.data.monthly_points || 0;
      lastMonthPoints.value = response.data.last_month_points || 0;
    } else {
      console.error('Invalid point statistics response:', response);
      // 对于管理员或没有积分记录的用户，设置默认值
      monthlyPoints.value = 0;
      lastMonthPoints.value = 0;
    }
  } catch (error: any) {
    // 忽略被取消的请求
    if (error.name === 'AbortError' || error.code === 'ERR_CANCELED') {
      console.log('Point statistics request was cancelled');
      return;
    }
    
    console.error('Error fetching point statistics:', error);
    // 对于管理员或没有积分记录的用户，设置默认值
    monthlyPoints.value = 0;
    lastMonthPoints.value = 0;
  }
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  debouncedFetchPointHistory()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  debouncedFetchPointHistory()
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

onUnmounted(() => {
  // 清理请求控制器和定时器
  if (historyController) {
    historyController.abort()
  }
  if (statisticsController) {
    statisticsController.abort()
  }
  if (fetchHistoryTimer) {
    window.clearTimeout(fetchHistoryTimer)
  }
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