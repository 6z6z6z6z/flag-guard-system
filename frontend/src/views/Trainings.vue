<template>
  <div class="trainings-container">
    <div class="header-controls">
      <h1 class="page-title">训练列表</h1>
      <el-button v-if="isAdmin" type="primary" @click="showCreateDialog" :icon="Plus">
        创建训练
      </el-button>
    </div>
    <el-divider />

    <div class="content-area" v-loading="loading">
      <el-row :gutter="20" v-if="trainings.length > 0">
        <el-col :xs="24" :sm="12" :md="8" v-for="training in trainings" :key="training.training_id" class="training-col">
          <el-card class="training-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="training-name">{{ training.name }}</span>
                <el-tag :type="getTrainingStatus(training).type" size="small">
                  {{ getTrainingStatus(training).text }}
                </el-tag>
              </div>
            </template>
            <div class="card-body">
              <p><el-icon><Calendar /></el-icon> <strong>时间：</strong>{{ formatDateTimeRange(training.start_time, training.end_time) }}</p>
              <p><el-icon><Location /></el-icon> <strong>地点：</strong>{{ training.location }}</p>
              <p><el-icon><Star /></el-icon> <strong>积分：</strong>{{ training.points }}</p>
            </div>
            <div class="card-footer">
              <div class="user-actions">
                <!-- 用户操作 -->
                <el-button
                  v-if="!training.is_registered && getTrainingStatus(training).text === '未开始'"
                  type="success"
                  size="small"
                  @click="handleRegister(training)"
                  round
                >
                  报名参加
                </el-button>
                <el-button
                  v-else-if="training.is_registered && getTrainingStatus(training).text === '未开始'"
                  type="danger"
                  size="small"
                  @click="handleCancelRegister(training)"
                  round
                >
                  取消报名
                </el-button>
                <el-tag v-else-if="training.is_registered" type="info" size="small">已报名</el-tag>
              </div>

              <!-- 管理员操作 -->
              <div class="admin-actions" v-if="isAdmin">
                 <el-button type="primary" link @click="handleEdit(training)">编辑</el-button>
                 <el-button type="danger" link @click="handleDelete(training.training_id)">删除</el-button>
                 <el-button type="info" link @click="handleViewRegistrations(training)">查看报名</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-else description="暂无训练"></el-empty>
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑训练' : '创建训练'"
      width="500px"
      @close="resetForm"
      :body-style="{ padding: '20px 60px' }"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="训练名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入训练名称" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择开始日期时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            placeholder="选择结束日期时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="积分" prop="points">
          <el-input-number v-model="form.points" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="地点" prop="location">
          <el-input v-model="form.location" placeholder="请输入训练地点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 报名名单对话框 -->
    <el-dialog
      v-model="registrationsDialogVisible"
      title="报名名单"
      width="80%"
      @close="currentTraining = null"
    >
      <el-table :data="currentRegistrations" style="width: 100%" v-loading="registrationsLoading">
        <el-table-column prop="student_id" label="学号" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="college" label="学院" />
        <el-table-column prop="created_at" label="报名时间">
          <template #default="{ row }">
            {{ formatRegistrationTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="attendance_status" label="出勤状态">
          <template #default="{ row }">
            <el-select 
              v-model="row.attendance_status" 
              placeholder="考勤状态"
              style="width: 120px;"
              :disabled="isAttendanceDisabled"
            >
              <el-option label="出勤" value="present"></el-option>
              <el-option label="缺勤" value="absent"></el-option>
              <el-option label="迟到" value="late"></el-option>
              <el-option label="早退" value="early_leave"></el-option>
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="points_awarded" label="获得积分">
          <template #default="{ row }">
            {{ row.points_awarded || 0 }}
          </template>
        </el-table-column>
      </el-table>
       <template #footer>
        <span class="dialog-footer">
          <el-button @click="registrationsDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="submitAttendance" 
            :loading="isSubmitting"
            :disabled="isAttendanceDisabled || isSubmitting"
          >
            确认考勤
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue';
import { useUserStore } from '@/stores/user';
import { ElMessage, ElMessageBox } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';
import axios from 'axios';
import { Plus, Calendar, Location, Star } from '@element-plus/icons-vue';

interface Training {
  training_id: number;
  name: string;
  start_time: string;
  end_time: string;
  points: number;
  location: string;
  is_registered?: boolean;
}

interface Registration {
    user_id: number;
    student_id: string;
    name: string;
    college: string;
    created_at: string;
    attendance_status: 'present' | 'absent' | 'late' | 'early_leave' | null;
    points_awarded: number | null;
    status: string;
}

const api = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1:5000/api',
});

api.interceptors.request.use(config => {
  const userStore = useUserStore();
  const token = userStore.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const userStore = useUserStore();
const isAdmin = computed(() => userStore.userInfo?.role === 'admin');

const trainings = ref<Training[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();
const form = reactive({
  training_id: null as number | null,
  name: '',
  start_time: null as Date | null,
  end_time: null as Date | null,
  points: 1,
  location: '',
});

const rules = reactive<FormRules>({
  name: [{ required: true, message: '请输入训练名称', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  points: [{ required: true, message: '请输入积分', trigger: 'blur' }],
  location: [{ required: true, message: '请输入地点', trigger: 'blur' }],
});

const getTrainingStatus = (training: Training) => {
  const now = new Date();
  const startTime = new Date(training.start_time);
  const endTime = new Date(training.end_time);

  if (now > endTime) {
    return { text: '已结束', type: 'info' as const };
  }
  if (now >= startTime && now <= endTime) {
    return { text: '进行中', type: 'success' as const };
  }
  return { text: '未开始', type: 'warning' as const };
};

const resetForm = () => {
  form.training_id = null;
  form.name = '';

  const startDate = new Date();
  const endDate = new Date(startDate.getTime() + 60 * 60 * 1000); // 1 hour later
  form.start_time = startDate;
  form.end_time = endDate;
  
  form.points = 1;
  form.location = '';
  isEdit.value = false;
};

const fetchTrainings = async () => {
  loading.value = true;
  try {
    const response = await api.get('/trainings/', {
      params: {
        page: currentPage.value,
        per_page: pageSize.value,
      },
    });
    if (response.data && response.data.data && response.data.data.items) {
      trainings.value = response.data.data.items;
      total.value = response.data.data.total;
    } else {
      trainings.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('Failed to fetch trainings:', error);
    ElMessage.error('获取训练列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSizeChange = (val: number) => {
  pageSize.value = val;
  fetchTrainings();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  fetchTrainings();
};

const showCreateDialog = () => {
  resetForm();
  dialogVisible.value = true;
};

const handleEdit = (training: Training) => {
  isEdit.value = true;
  form.training_id = training.training_id;
  form.name = training.name;
  form.start_time = new Date(training.start_time);
  form.end_time = new Date(training.end_time);
  form.points = training.points;
  form.location = training.location;
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (valid) {
      if (!form.start_time || !form.end_time) return;

      if (new Date(form.end_time) <= new Date(form.start_time)) {
        ElMessage.error('结束时间必须晚于开始时间');
        return;
      }
      
      const payload = {
        name: form.name,
        start_time: form.start_time,
        end_time: form.end_time,
        points: form.points,
        location: form.location,
        training_id: form.training_id,
      };

      const url = isEdit.value ? `/trainings/${payload.training_id}` : '/trainings/';
      const method = isEdit.value ? 'put' : 'post';
      try {
        await api[method](url, payload);
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功');
        dialogVisible.value = false;
        fetchTrainings();
      } catch (error) {
        console.error('Failed to save training:', error);
        ElMessage.error('操作失败');
      }
    }
  });
};

const handleDelete = async (trainingId: number) => {
  await ElMessageBox.confirm('确定要删除这个训练吗?', '警告', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  });
  try {
    await api.delete(`/trainings/${trainingId}`);
    ElMessage.success('删除成功');
    fetchTrainings();
  } catch (error) {
    console.error('Failed to delete training:', error);
    ElMessage.error('删除失败');
  }
};

const handleRegister = async (training: Training) => {
  try {
    await api.post(`/trainings/${training.training_id}/register`);
    ElMessage.success('报名成功');
    fetchTrainings();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '报名失败');
  }
};

const handleCancelRegister = async (training: Training) => {
  try {
    await api.delete(`/trainings/${training.training_id}/register`);
    ElMessage.success('取消报名成功');
    fetchTrainings();
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '取消报名失败');
  }
};

const registrationsDialogVisible = ref(false);
const currentRegistrations = ref<Registration[]>([]);
const registrationsLoading = ref(false);
const currentTrainingId = ref<number | null>(null);
const currentTraining = ref<Training | null>(null);
const isSubmitting = ref(false);
const isAttendanceConfirmed = ref(false);

const isAttendanceDisabled = computed(() => {
  if (!currentTraining.value) return true;
  if (isAttendanceConfirmed.value) return true;
  return new Date(currentTraining.value.start_time) > new Date();
});

const handleViewRegistrations = async (training: Training) => {
  currentTraining.value = training;
  currentTrainingId.value = training.training_id;
  registrationsLoading.value = true;
  registrationsDialogVisible.value = true;
  
  try {
    const response = await api.get(`/trainings/${training.training_id}/registrations`);
    if (response.data && response.data.data) {
      const regs = response.data.data as Registration[];
      currentRegistrations.value = regs;
      isAttendanceConfirmed.value = regs.some(r => r.attendance_status);
    } else {
      currentRegistrations.value = [];
      isAttendanceConfirmed.value = false;
    }
  } catch (error) {
    console.error('Failed to fetch registrations:', error);
    ElMessage.error('获取报名列表失败');
  } finally {
    registrationsLoading.value = false;
  }
};

const submitAttendance = async () => {
  if (!currentTraining.value?.training_id) return;
  isSubmitting.value = true;

  const payload = {
    attendance_records: currentRegistrations.value.map(reg => ({
      user_id: reg.user_id,
      attendance_status: reg.attendance_status
    }))
  };

  try {
    await api.post(`/trainings/${currentTraining.value.training_id}/attendance`, payload);
    ElMessage.success('考勤状态更新成功');
    registrationsDialogVisible.value = false;
  } catch (error) {
    console.error('Failed to submit attendance:', error);
    ElMessage.error('更新考勤失败');
  } finally {
    isSubmitting.value = false;
  }
};

const formatDateTimeRange = (start: string, end: string) => {
  if (!start) return 'N/A';
  
  const startDate = new Date(start);
  const startDateTime = startDate.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).replace(/,/g, '');

  if (!end) {
    return startDateTime;
  }

  const endDate = new Date(end);
  const endTime = endDate.toLocaleString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });

  return `${startDateTime} - ${endTime}`;
};

const formatRegistrationTime = (timeStr: string) => {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', { hour12: false });
};

onMounted(() => {
  fetchTrainings();
});
</script>

<style scoped>
.trainings-container {
  padding: 20px;
}

.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
}

.content-area {
  margin-top: 20px;
}

.training-col {
  margin-bottom: 20px;
}

.training-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.training-name {
  font-weight: bold;
}

.card-body {
  flex-grow: 1;
}

.card-body p {
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.card-body .el-icon {
  color: #409EFF;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.user-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.admin-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>