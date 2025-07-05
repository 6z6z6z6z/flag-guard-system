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
              :src="getImageUrl(scope.row.photo_url)"
              :preview-src-list="[getImageUrl(scope.row.photo_url)]"
              :preview-teleported="true"
              :z-index="9999"
              fit="cover"
              class="table-image"
              style="z-index: 9999"
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
    console.log('Fetching flag records for review...')
    const response = await request.get('/flag/records/review', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
        status: filterStatus.value
      }
    })
    console.log('Response:', response)
    
    if (response.code === 200 && response.data) {
      // 兼容不同的响应格式
      let responseData = response.data;
      
      // 检查是否有 items 字段，如果没有但 data 字段有 items，使用 data 中的 items
      if (!responseData.items && responseData.data && responseData.data.items) {
        responseData = responseData.data;
      }
      
      // 确保有 items 字段
      if (responseData.items && Array.isArray(responseData.items)) {
        records.value = responseData.items.map((item: any) => {
          // 防止空记录
          if (!item) {
            console.error('Encountered null or undefined item in response');
            return {
              record_id: 0,
              date: new Date().toISOString().split('T')[0],
              type: 'raise',
              status: 'pending',
              photo_url: '',
              points_awarded: 0,
              reviewing: false,
              user: { name: 'Unknown', student_id: '' }
            };
          }
          
          // 添加调试信息
          console.log('Processing record:', item);
          
          // 确保每条记录都有基本字段
          const processedItem = {
            ...item,
            reviewing: false,
            record_id: item.record_id || 0,
            date: item.date || new Date().toISOString().split('T')[0],
            type: item.type || 'raise',
            status: item.status || 'pending',
            photo_url: item.photo_url || '',
            points_awarded: item.points_awarded !== undefined ? item.points_awarded : 0,
            user: item.user || {
              name: item.user_name || 'Unknown User',
              student_id: item.student_id || ''
            }
          };
          
          // 修复 photo_url
          if (processedItem.photo_url) {
            // 如果图片URL不是http开头或斜杠开头，添加前缀
            if (!processedItem.photo_url.startsWith('http') && !processedItem.photo_url.startsWith('/')) {
              processedItem.photo_url = `/uploads/${processedItem.photo_url}`;
            } else if (processedItem.photo_url.startsWith('/api/uploads/')) {
              // 如果URL是/api/uploads/开头，去掉/api前缀
              processedItem.photo_url = processedItem.photo_url.substring(4);
            }
          }
          
          return processedItem;
        });
        
        total.value = responseData.total || records.value.length;
        console.log('Records loaded:', records.value.length);
      } else {
        console.error('No items array in response:', responseData);
        ElMessage.error('获取记录失败：响应格式错误 - 缺少 items 数组');
        records.value = [];
        total.value = 0;
      }
    } else {
      console.error('Invalid response format:', response);
      ElMessage.error(response.msg || '获取记录失败：响应格式错误');
      records.value = [];
      total.value = 0;
    }
  } catch (error: any) {
    console.error('Error fetching records:', error)
    console.error('Error details:', {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    })
    ElMessage.error(error.response?.data?.msg || '获取记录失败')
    records.value = [];
    total.value = 0;
  }
}

// 审核通过
const handleApprove = async (record: any) => {
  record.reviewing = true
  try {
    const response = await request.post(`/flag/records/${record.record_id}/approve`)
    if (response.code === 200) {
      ElMessage.success(response.msg || '审核通过成功')
      fetchRecords()
    } else {
      ElMessage.error(response.msg || '审核操作失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '审核操作失败')
  } finally {
    record.reviewing = false
  }
}

// 审核拒绝
const handleReject = async (record: any) => {
  try {
    await ElMessageBox.confirm('确定要拒绝这条记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    record.reviewing = true
    const response = await request.post(`/flag/records/${record.record_id}/reject`)
    if (response.code === 200) {
      ElMessage.success(response.msg || '已拒绝')
      fetchRecords()
    } else {
      ElMessage.error(response.msg || '操作失败')
    }
  } catch (error: any) {
    if (error === 'cancel') {
      // 用户取消，不做任何事
      return
    }
    ElMessage.error(error.response?.data?.msg || '操作失败')
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

// 获取图片URL
const getImageUrl = (url: string) => {
  if (!url) return '';
  
  console.log('Processing image URL:', url);
  
  // 完整URL直接返回
  if (url.startsWith('http')) return url;
  
  // 后端返回的URL是 /api/uploads/xxx.jpg
  if (url.startsWith('/api/uploads/')) {
    // 去掉 /api 前缀，变成 /uploads/xxx.jpg
    console.log('Converting API URL:', url, '->', url.substring(4));
    return url.substring(4);
  }
  
  // 已经是 /uploads/ 开头的URL
  if (url.startsWith('/uploads/')) {
    return url;
  }
  
  // 对于历史数据，可能是相对路径或只有文件名
  if (url.includes('/')) {
    // 提取文件名
    const filename = url.split('/').pop();
    console.log('Extracted filename:', filename);
    return `/uploads/${filename}`;
  } else {
    // 直接是文件名
    console.log('Using filename directly:', url);
    return `/uploads/${url}`;
  }
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