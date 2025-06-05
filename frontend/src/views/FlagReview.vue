<template>
  <div class="flag-review-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>升降旗记录审核</h3>
          <el-radio-group v-model="filterStatus" @change="fetchRecords">
            <el-radio-button :value="'pending'">待审核</el-radio-button>
            <el-radio-button :value="'approved'">已通过</el-radio-button>
            <el-radio-button :value="'rejected'">已拒绝</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="records" style="width: 100%">
        <el-table-column prop="date" label="日期" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.date) }}
          </template>
        </el-table-column>
        <el-table-column prop="user.name" label="提交人" width="120" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            {{ scope.row.type === 'raise' ? '升旗' : '降旗' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="照片" width="120">
          <template #default="scope">
            <el-image
              v-if="scope.row.photo_url"
              :src="scope.row.photo_url"
              :preview-src-list="[scope.row.photo_url]"
              fit="cover"
              class="table-image"
            />
            <span v-else>无照片</span>
          </template>
        </el-table-column>
        <el-table-column prop="reviewed_at" label="审核时间" width="180">
          <template #default="scope">
            {{ scope.row.reviewed_at ? formatDateTime(scope.row.reviewed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button-group v-if="scope.row.status === 'pending'">
              <el-button
                type="success"
                size="small"
                @click="handleApprove(scope.row)"
                :loading="scope.row.reviewing"
              >
                通过
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleReject(scope.row)"
                :loading="scope.row.reviewing"
              >
                拒绝
              </el-button>
            </el-button-group>
            <el-tag
              v-else-if="scope.row.status === 'approved'"
              type="success"
              effect="plain"
            >
              已通过 ({{ scope.row.points_awarded }}分)
            </el-tag>
            <el-tag
              v-else
              type="danger"
              effect="plain"
            >
              已拒绝
            </el-tag>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

// 列表数据
const records = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('pending')

// 获取记录列表
const fetchRecords = async () => {
  try {
    const response = await request.get('/flag/records/review', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        status: filterStatus.value
      }
    })
    records.value = response.data.items.map((item: any) => ({
      ...item,
      reviewing: false
    }))
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取记录失败')
  }
}

// 审核通过
const handleApprove = async (record: any) => {
  try {
    record.reviewing = true
    await request.post(`/flag/records/${record.record_id}/approve`)
    ElMessage.success('审核通过成功')
    fetchRecords()
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    record.reviewing = false
  }
}

// 审核拒绝
const handleReject = async (record: any) => {
  try {
    const result = await ElMessageBox.confirm(
      '确定要拒绝这条记录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (result === 'confirm') {
      record.reviewing = true
      await request.post(`/flag/records/${record.record_id}/reject`)
      ElMessage.success('已拒绝')
      fetchRecords()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    record.reviewing = false
  }
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchRecords()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchRecords()
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString()
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

// 获取状态标签类型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return textMap[status] || status
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.flag-review-container {
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

.table-image {
  width: 80px;
  height: 60px;
  cursor: pointer;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style> 