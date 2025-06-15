<template>
  <div class="flag-records-container">
    <!-- 提交升降旗记录表单 -->
    <el-card class="submit-card">
      <template #header>
        <div class="card-header">
          <h3>提交升降旗记录</h3>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="flagForm"
        :rules="rules"
        label-width="100px"
        :disabled="submitting"
      >
        <el-form-item label="日期" prop="date">
          <el-date-picker
            v-model="flagForm.date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="flagForm.type">
            <el-radio :value="'raise'">升旗</el-radio>
            <el-radio :value="'lower'">降旗</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="照片" prop="photo_url">
          <el-upload
            class="upload-demo"
            action="/api/files/upload"
            :http-request="customUpload"
            :before-upload="beforeUpload"
            :show-file-list="false"
          >
            <el-button type="primary">点击上传</el-button>
            <template #tip>
              <div class="el-upload__tip">
                只能上传jpg/png文件，且不超过2MB
              </div>
            </template>
          </el-upload>
          <div v-if="flagForm.photo_url" class="preview-image">
            <img :src="getImageUrl(flagForm.photo_url)" alt="预览图" />
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="submitRecord" :loading="submitting">
            提交记录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 历史记录列表 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <h3>历史记录</h3>
          <el-radio-group v-model="filterStatus" @change="fetchRecords">
            <el-radio-button :value="'all'">全部</el-radio-button>
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
        <el-table-column prop="points_awarded" label="获得积分" width="100">
          <template #default="scope">
            <span v-if="scope.row.status === 'approved'">
              {{ scope.row.points_awarded }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="照片" width="120">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="handlePreview(row.photo_url)"
            >
              查看照片
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="reviewed_at" label="审核时间" width="180">
          <template #default="scope">
            {{ scope.row.reviewed_at ? formatDateTime(scope.row.reviewed_at) : '-' }}
          </template>
        </el-table-column>
        <!-- 添加提交者信息列 -->
        <el-table-column v-if="userStore.isAdmin" label="提交者" width="180">
          <template #default="scope">
            {{ scope.row.user?.name }} ({{ scope.row.user?.student_id }})
          </template>
        </el-table-column>
        <!-- 添加审核操作列 -->
        <el-table-column v-if="userStore.isAdmin" label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'pending'"
              type="success"
              size="small"
              @click="handleApprove(scope.row)"
            >
              通过
            </el-button>
            <el-button
              v-if="scope.row.status === 'pending'"
              type="danger"
              size="small"
              @click="handleReject(scope.row)"
            >
              拒绝
            </el-button>
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

    <el-dialog
      v-model="previewVisible"
      title="照片预览"
      width="50%"
      :append-to-body="true"
      :modal-append-to-body="true"
      :destroy-on-close="true"
      :z-index="3000"
    >
      <div class="preview-container">
        <img :src="previewUrl" alt="预览图片" class="preview-image" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FormInstance, FormRules, UploadProps } from 'element-plus'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 照片预览相关
const previewVisible = ref(false)
const previewUrl = ref('')

// 表单数据
const flagForm = ref({
  date: '',
  type: 'raise',
  photo_url: ''
})

// 表单验证规则
const rules: FormRules = {
  date: [
    { required: true, message: '请选择日期', trigger: 'change' }
  ],
  type: [
    { required: true, message: '请选择类型', trigger: 'change' }
  ],
  photo_url: [
    { required: true, message: '请上传照片', trigger: 'change' }
  ]
}

// 历史记录相关
const records = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('all')

// 获取图片URL
const getImageUrl = (url: string) => {
  if (!url) return ''
  if (url.startsWith('http')) return url

  // 后端返回的URL是 /api/uploads/xxx.jpg
  // 我们需要把它变成 /uploads/xxx.jpg 以便代理
  if (url.startsWith('/api/uploads/')) {
    return url.substring(4) // 去掉 /api
  }
  
  if (url.startsWith('/uploads/')) {
    return url
  }

  // 对于历史数据，可能没有前缀
  return `/uploads/${url.split('/').pop()}`
}

// 上传相关方法
const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

const customUpload = async (options: any) => {
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    
    const response = await request.post('/files/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data && response.data.url) {
      flagForm.value.photo_url = response.data.url
      ElMessage.success('上传成功')
    } else {
      ElMessage.error('上传失败')
    }
  } catch (error: any) {
    console.error('Upload error:', error)
    ElMessage.error(error.response?.data?.error || '上传失败')
  }
}

// 提交记录
const submitRecord = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const response = await request.post('/flag/records', flagForm.value)
        if (response.code === 200) {
          ElMessage.success(response.msg || '提交成功')
          // 重置表单
          formRef.value?.resetFields()
          flagForm.value.photo_url = ''
          // 刷新历史记录
          await fetchRecords()
        } else {
          ElMessage.error(response.msg || '提交失败')
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.msg || '提交失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 获取记录列表
const fetchRecords = async () => {
  try {
    console.log('Starting fetchRecords')
    console.log('Current user info:', userStore.userInfo)
    console.log('Is admin:', userStore.isAdmin)
    
    const params: {
      page: number;
      per_page: number;
      status?: string;
    } = {
      page: currentPage.value,
      per_page: pageSize.value
    }
    if (filterStatus.value !== 'all') {
      params.status = filterStatus.value
    }
    
    // 根据用户角色选择不同的API端点
    const endpoint = userStore.isAdmin ? '/flag/records/review' : '/flag/records'
    console.log('Fetching records from endpoint:', endpoint, 'with params:', params)
    
    const response = await request.get(endpoint, { params })
    console.log('Response:', response)
    
    if (response && response.data) {
      records.value = response.data.items || []
      total.value = response.data.total || 0
      console.log('Updated records:', records.value)
      console.log('Total records:', total.value)
    } else {
      console.error('Invalid response format:', response)
      ElMessage.error('获取记录失败：响应格式错误')
    }
  } catch (error: any) {
    console.error('Error fetching records:', error)
    ElMessage.error(error.message || '获取记录失败')
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
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  // 添加8小时时区偏移
  date.setHours(date.getHours() + 8)
  return date.toLocaleDateString()
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  // 添加8小时时区偏移
  date.setHours(date.getHours() + 8)
  return date.toLocaleString()
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

// 审核相关方法
const handleApprove = async (record: any) => {
  try {
    const response = await request.post(`/flag/records/${record.record_id}/approve`)
    if (response.code === 200) {
      ElMessage.success(response.msg || '审核通过成功')
      await fetchRecords()
    } else {
      ElMessage.error(response.msg || '审核失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '审核失败')
  }
}

const handleReject = async (record: any) => {
  try {
    const response = await request.post(`/flag/records/${record.record_id}/reject`)
    if (response.code === 200) {
      ElMessage.success(response.msg || '已拒绝该记录')
      await fetchRecords()
    } else {
      ElMessage.error(response.msg || '操作失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '操作失败')
  }
}

// 预览照片
const handlePreview = (url: string) => {
  previewUrl.value = getImageUrl(url)
  previewVisible.value = true
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.flag-records-container {
  padding: 20px;
}

.submit-card,
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

.preview-image {
  margin-top: 10px;
}

.preview-image img {
  max-width: 200px;
  max-height: 200px;
  object-fit: contain;
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

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}
</style> 