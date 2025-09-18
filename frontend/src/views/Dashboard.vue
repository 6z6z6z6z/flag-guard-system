<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col>
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><User /></div>
          <div class="stat-content">
            <div class="stat-title">总用户数</div>
            <div class="stat-value">{{ dashboardStore.stats.total_users }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col>
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><Calendar /></div>
          <div class="stat-content">
            <div class="stat-title">训练总数</div>
            <div class="stat-value">{{ dashboardStore.stats.total_trainings }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col>
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><Clock /></div>
          <div class="stat-content">
            <div class="stat-title">待审核</div>
            <div class="stat-value">{{ dashboardStore.stats.pending_records }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col>
        <el-card shadow="hover" class="stat-card">
           <div class="stat-icon"><Trophy /></div>
          <div class="stat-content">
            <div class="stat-title">活动总数</div>
            <div class="stat-value">{{ dashboardStore.stats.total_events }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col>
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon"><Star /></div>
          <div class="stat-content">
            <div class="stat-title">总积分</div>
            <div class="stat-value">{{ dashboardStore.stats.total_points }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 待审核记录和最近活动 -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>待审核记录</span>
              <!-- <el-button type="primary" link @click="viewAllPending">查看全部</el-button> -->
            </div>
          </template>
          <el-table :data="dashboardStore.pendingTasks" style="width: 100%" :max-height="300" v-loading="dashboardStore.loading">
            <el-table-column prop="type" label="类型" width="100">
               <template #default="{ row }">
                <el-tag :type="getTypeTag(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="user_name" label="用户" />
            <el-table-column prop="details" label="详情" />
            <el-table-column prop="time" label="时间">
              <template #default="{ row }">{{ formatDateTime(row.time) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
              <el-button type="primary" link @click="viewAllEvents">查看全部</el-button>
            </div>
          </template>
          <el-table :data="dashboardStore.recentEvents" style="width: 100%" v-loading="dashboardStore.loading">
            <el-table-column prop="name" label="活动名称" />
            <el-table-column prop="location" label="地点" />
            <el-table-column prop="time" label="活动时间">
              <template #default="{ row }">
                {{ formatActivityTime(row.time) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusTag(getEventStatus(row.time))">{{ getEventStatus(row.time) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'
import { User, Calendar, Clock, Star, Trophy } from '@element-plus/icons-vue'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const dashboardStore = useDashboardStore()

const getTypeTag = (type: string) => {
  const types: Record<string, string> = {
    '升降旗': 'info',
    '训练': 'warning',
  }
  return types[type] || 'primary'
}

const getStatusTag = (status: string) => {
  const statuses: Record<string, string> = {
    '已结束': 'info',
    '未开始': 'success',
  }
  return statuses[status] || 'info'
}

const getEventStatus = (eventTime: string) => {
  if (!eventTime) return '未知'
  return new Date(eventTime) > new Date() ? '未开始' : '已结束'
}

const viewAllEvents = () => {
  router.push('/events')
}

const formatActivityTime = (timeStr: string) => {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  // Add 8 hours for timezone adjustment
  date.setHours(date.getHours() + 8);
  return date.toISOString().replace('T', ' ').substring(0, 16);
};

onMounted(() => {
  dashboardStore.fetchDashboardData()
})
</script>

<style scoped>
.text-fix {
  position: relative;
  top: 6px;
}
.dashboard {
  padding: 20px;
}
.stat-row {
  display: flex;
}
.stat-row > .el-col {
  flex: 1;
}
.mt-20 {
  margin-top: 40px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 16px;
  color: #fff;
  border-radius: 8px;
  height: 100%;
}
.stat-card:nth-child(5n+1) { background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%); }
.stat-card:nth-child(5n+2) { background: linear-gradient(135deg, #FAD961 0%, #F76B1C 100%); }
.stat-card:nth-child(5n+3) { background: linear-gradient(135deg, #EA4C89 0%, #F47C7C 100%); }
.stat-card:nth-child(5n+4) { background: linear-gradient(135deg, #89216B 0%, #DA4453 100%); }
.stat-card:nth-child(5n+5) { background: linear-gradient(135deg, #16A085 0%, #F4D03F 100%); }
.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  font-size: 36px;
  margin-bottom: 12px;
  opacity: 0.8;
}
.stat-content {
  text-align: center;
}
.stat-title {
  font-size: 14px;
  margin-bottom: 4px;
  opacity: 0.9;
}
.stat-value {
  font-size: 22px;
  font-weight: bold;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.clickable {
  cursor: pointer;
}
.clickable:hover {
  transform: translateY(-5px);
  transition: transform 0.3s ease;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 12px;
  }
  .stat-row {
    flex-direction: column;
    gap: 12px;
  }
  .mt-20 {
    margin-top: 20px;
  }
  :deep(.el-col) {
    width: 100% !important;
  }
  :deep(.el-table__body-wrapper),
  :deep(.el-table__header-wrapper) {
    overflow-x: auto;
  }
}
</style> 