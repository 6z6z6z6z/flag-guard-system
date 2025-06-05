<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>总用户数</span>
            </div>
          </template>
          <div class="card-content">
            <h2>{{ stats.totalUsers }}</h2>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>今日活动</span>
            </div>
          </template>
          <div class="card-content">
            <h2>{{ stats.todayEvents }}</h2>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>待审核记录</span>
            </div>
          </template>
          <div class="card-content">
            <h2>{{ stats.pendingRecords }}</h2>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>总积分</span>
            </div>
          </template>
          <div class="card-content">
            <h2>{{ stats.totalPoints }}</h2>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
            </div>
          </template>
          <el-table :data="recentEvents" style="width: 100%">
            <el-table-column prop="name" label="活动名称" />
            <el-table-column prop="time" label="时间" />
            <el-table-column prop="status" label="状态" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>待审核记录</span>
            </div>
          </template>
          <el-table :data="pendingRecords" style="width: 100%">
            <el-table-column prop="user" label="用户" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="date" label="日期" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '../utils/request'

const stats = ref({
  totalUsers: 0,
  todayEvents: 0,
  pendingRecords: 0,
  totalPoints: 0
})

const recentEvents = ref([])
const pendingRecords = ref([])

const fetchDashboardData = async () => {
  try {
    const response = await request.get('/dashboard')
    if (response.data && response.data.data) {
      const { stats: dashboardStats } = response.data.data
      stats.value = {
        totalUsers: dashboardStats.total_users || 0,
        todayEvents: dashboardStats.total_events || 0,
        pendingRecords: dashboardStats.total_flags || 0,
        totalPoints: dashboardStats.total_trainings || 0
      }
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  text-align: center;
  padding: 20px 0;
}

.card-content h2 {
  margin: 0;
  font-size: 24px;
  color: #409eff;
}
</style> 