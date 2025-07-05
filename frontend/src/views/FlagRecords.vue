<template>
  <div class="flag-records-container">
    <div class="header-controls">
      <h1 class="page-title">升降旗记录</h1>
      <div class="actions">
        <el-radio-group v-model="filterStatus" @change="fetchRecords" class="filter-buttons">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="pending">待审核</el-radio-button>
          <el-radio-button value="approved">已通过</el-radio-button>
          <el-radio-button value="rejected">已拒绝</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Plus" @click="showSubmitDialog">
          上传记录
        </el-button>
      </div>
    </div>
    <el-divider></el-divider>
    <div class="content-area" v-loading="loading">
      <el-row :gutter="20" v-if="records.length > 0">
        <el-col :xs="24" :sm="12" :md="8" v-for="record in records" :key="record.record_id" class="record-col">
          <el-card class="record-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="record-date">{{ formatDate(record.date) }}</span>
                <el-tag :type="getStatusType(record.status)">
                  {{ getStatusText(record.status) }}
                </el-tag>
              </div>
            </template>
            <div class="card-body">
              <p><el-icon><Flag /></el-icon> <strong>类型：</strong> {{ record.type === 'raise' ? '升旗' : '降旗' }}</p>
              <p v-if="userStore.isAdmin"><el-icon><User /></el-icon> <strong>提交人：</strong> {{ record.user?.name || 'N/A' }}</p>
              <p><el-icon><Star /></el-icon> <strong>积分：</strong> {{ record.status === 'approved' ? record.points_awarded : '-' }}</p>
              <p><el-icon><Picture /></el-icon> <strong>照片：</strong>
                <el-button
                  type="primary"
                  link
                  @click="handlePreview(getImageUrl(record.photo_url))"
                  style="margin-left: 8px;"
                >
                  查看照片
                </el-button>
              </p>
            </div>
            <div class="card-footer" v-if="userStore.isAdmin && record.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(record)" round>通过</el-button>
              <el-button type="danger" size="small" @click="handleReject(record)" round>拒绝</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-else description="暂无记录"></el-empty>
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 提交记录对话框 -->
    <el-dialog
      v-model="submitDialogVisible"
      title="提交升降旗记录"
      width="500px"
      @close="resetForm"
    >
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
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="flagForm.type">
            <el-radio value="raise">升旗</el-radio>
            <el-radio value="lower">降旗</el-radio>
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
          <div v-if="flagForm.photo_url" class="preview-image-dialog">
            <img :src="getImageUrl(flagForm.photo_url)" alt="预览图" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="submitDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRecord" :loading="submitting">
            提交
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="previewVisible" title="照片预览" width="600px" center :body-style="{ padding: '0' }">
      <el-image
        style="width: 100%; height: auto;"
        :src="previewUrl"
        fit="contain"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { FormInstance, FormRules, UploadProps } from 'element-plus'
import { ElMessage } from 'element-plus'
import request from '../utils/request'
import { useUserStore } from '../stores/user'
import { Plus, Flag, User, Star, Picture } from '@element-plus/icons-vue'

const userStore = useUserStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const submitDialogVisible = ref(false)
const loading = ref(true)
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
const records = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filterStatus = ref('')  // 空字符串代表全部

const showSubmitDialog = () => {
  resetForm();
  submitDialogVisible.value = true;
};

const resetForm = () => {
  if(formRef.value) {
    formRef.value.resetFields();
  }
  flagForm.value = {
    date: '',
    type: 'raise',
    photo_url: ''
  };
};

const handlePreview = (url: string) => {
  previewUrl.value = url;
  previewVisible.value = true;
};

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
  const formData = new FormData()
  formData.append('file', options.file)

  try {
    console.log('Uploading file:', options.file.name);
    
    const response = await request.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    console.log('Upload response:', response);

    if (response.data && response.data.url) {
      flagForm.value.photo_url = response.data.url;
      console.log('Setting photo URL to:', response.data.url);
      ElMessage.success('上传成功');
    } else {
      console.error('Invalid upload response format:', response);
      ElMessage.error(response.msg || '上传失败');
    }
  } catch (error: any) {
    console.error('File upload error:', error);
    ElMessage.error(error.response?.data?.msg || '上传请求失败');
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
        if (response.code === 201 || response.code === 200) {
          ElMessage.success('提交成功，等待审核')
          submitDialogVisible.value = false;
          fetchRecords()
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

// 获取历史记录
const fetchRecords = async () => {
  loading.value = true;
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      status: filterStatus.value === 'all' ? undefined : filterStatus.value,
    }
    console.log('Fetching flag records with params:', params);
    
    const endpoint = userStore.isAdmin ? '/flag/records/review' : '/flag/records';
    console.log('Using endpoint:', endpoint);
    
    const response = await request.get(endpoint, { params })
    console.log('Flag records response:', response);
    
    if (response.code === 200 && response.data) {
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
              user: { name: 'Unknown', student_id: '' }
            };
          }
          
          // 确保每条记录都有正确的字段
          const processedItem = {
            ...item,
            // 修复可能的null值
            record_id: item.record_id || 0,
            date: item.date || new Date().toISOString().split('T')[0],
            type: item.type || 'raise',
            status: item.status || 'pending',
            photo_url: item.photo_url || '',
            points_awarded: item.points_awarded !== undefined ? item.points_awarded : 0,
            user: item.user || { name: item.user_name || 'Unknown', student_id: item.student_id || '' }
          };
          
          // 确保 photo_url 格式正确
          if (processedItem.photo_url) {
            processedItem.photo_url = getImageUrl(processedItem.photo_url);
          }
          
          console.log('Processed record:', processedItem);
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
    console.error('Error fetching records:', error);
    console.error('Error details:', {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    });
    ElMessage.error(error.response?.data?.msg || '获取记录失败');
    records.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

// 状态标签类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'pending': return 'warning'
    case 'approved': return 'success'
    case 'rejected': return 'error'
    default: return 'info'
  }
}

// 状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '待审核'
    case 'approved': return '已通过'
    case 'rejected': return '已拒绝'
    default: return '未知'
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 审核相关方法
const handleApprove = async (row: any) => {
  try {
    await request.post(`/flag/records/${row.record_id}/approve`);
    ElMessage.success('审核通过');
    fetchRecords();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '操作失败');
  }
};

const handleReject = async (row: any) => {
  try {
    await request.post(`/flag/records/${row.record_id}/reject`);
    ElMessage.success('操作成功');
    fetchRecords();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.msg || '操作失败');
  }
};

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchRecords()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchRecords()
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.flag-records-container {
  padding: 20px;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0; /* Adjusted to use divider for spacing */
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.actions {
  display: flex;
  align-items: center;
}

.filter-buttons {
  margin-right: 16px;
}

.content-area {
  margin-top: 0;
}

.record-col {
  margin-bottom: 20px;
}

.record-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-date {
  font-weight: bold;
}

.card-body {
  flex-grow: 1;
}

.card-body p {
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.card-body p .el-icon {
  color: #409EFF;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: auto;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.preview-image-dialog {
  margin-top: 10px;
  max-width: 200px;
  max-height: 200px;
}

.preview-image-dialog img {
  width: 100%;
  height: auto;
}

.add-button {
  /* Style for the add button if needed */
}
</style>