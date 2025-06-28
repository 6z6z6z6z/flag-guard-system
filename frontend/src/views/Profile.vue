<template>
  <div class="profile-container">
    <div class="header-controls">
      <h1 class="page-title">个人信息</h1>
      <div class="actions">
        <el-button type="primary" @click="handleEdit" v-if="!isEditing" :icon="Edit">
          编辑信息
        </el-button>
        <div v-else>
          <el-button type="success" @click="handleSave" :loading="isSaving" :icon="Select">
            保存
          </el-button>
          <el-button @click="handleCancel" :icon="CloseBold">
            取消
          </el-button>
        </div>
      </div>
    </div>
    <el-divider />

    <div class="profile-content-wrapper">
      <el-card class="profile-card" shadow="never">
        <div class="profile-header">
          <el-avatar :size="60" :icon="UserFilled" class="profile-avatar" />
          <div class="profile-header-info">
            <span class="profile-name">{{ userForm.name }}</span>
            <el-tag size="small" effect="light" round>{{ userRole }}</el-tag>
          </div>
        </div>

        <el-divider content-position="left">基础信息</el-divider>
        
        <div class="info-section">
          <el-form label-width="100px" label-position="right">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="用户名">
                  <span class="info-text">{{ userForm.username }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="姓名">
                  <span class="info-text">{{ userForm.name }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="学号">
                  <span class="info-text">{{ userForm.student_id }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="学院">
                  <span class="info-text">{{ userForm.college }}</span>
                </el-form-item>
              </el-col>
               <el-col :span="8">
                <el-form-item label="手机号">
                  <span class="info-text">{{ userForm.phone_number }}</span>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>

        <el-divider content-position="left">身体数据</el-divider>

        <div class="info-section">
          <el-form
            ref="formRef"
            :model="userForm"
            :rules="rules"
            label-width="100px"
            label-position="right"
          >
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="身高(cm)" prop="height">
                  <el-input-number v-if="isEditing" v-model="userForm.height" :min="140" :max="220" :precision="0" controls-position="right" style="width: 100%;"/>
                  <span v-else class="info-text">{{ userForm.height }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="体重(kg)" prop="weight">
                  <el-input-number v-if="isEditing" v-model="userForm.weight" :min="35" :max="150" :precision="1" controls-position="right" style="width: 100%;" />
                  <span v-else class="info-text">{{ userForm.weight }}</span>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="鞋码" prop="shoe_size">
                  <el-input-number v-if="isEditing" v-model="userForm.shoe_size" :min="34" :max="48" :precision="0" controls-position="right" style="width: 100%;"/>
                  <span v-else class="info-text">{{ userForm.shoe_size }}</span>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import request from '../utils/request'
import { useUserStore } from '@/stores/user'
import { Edit, Select, CloseBold, UserFilled } from '@element-plus/icons-vue'

const formRef = ref<FormInstance>()
const isEditing = ref(false)
const isSaving = ref(false)
const userStore = useUserStore()

const userRole = computed(() => {
  const role = userStore.userInfo?.role
  if (role === 'superadmin') return '超级管理员'
  if (role === 'admin') return '管理员'
  if (role === 'member') return '队员'
  return '未知'
})

const userForm = ref({
  username: '',
  name: '',
  student_id: '',
  college: '',
  height: null as number | null,
  weight: null as number | null,
  shoe_size: null as number | null,
  phone_number: ''
})

const rules = {
  height: [
    { required: true, message: '请输入身高', trigger: 'blur' },
    { type: 'number', min: 140, max: 220, message: '身高范围在 140-220cm 之间', trigger: 'blur' }
  ],
  weight: [
    { required: true, message: '请输入体重', trigger: 'blur' },
    { type: 'number', min: 35, max: 150, message: '体重范围在 35-150kg 之间', trigger: 'blur' }
  ],
  shoe_size: [
    { required: true, message: '请输入鞋码', trigger: 'blur' },
    { type: 'number', min: 34, max: 48, message: '鞋码范围在 34-48 之间', trigger: 'blur' }
  ]
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await request.get('/auth/info')
    const { username, name, student_id, college, height, weight, shoe_size, phone_number } = response.data
    userForm.value = {
      username,
      name,
      student_id,
      college,
      height: height || null,
      weight: weight || null,
      shoe_size: shoe_size || null,
      phone_number: phone_number || ''
    }
  } catch (error) {
    ElMessage.error('获取用户信息失败')
  }
}

// 编辑信息
const handleEdit = () => {
  isEditing.value = true
}

// 保存信息
const handleSave = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    isSaving.value = true
    await request.put('/users/profile', {
      height: userForm.value.height,
      weight: userForm.value.weight,
      shoe_size: userForm.value.shoe_size
    })
    ElMessage.success('保存成功')
    isEditing.value = false
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 取消编辑
const handleCancel = () => {
  isEditing.value = false
  fetchUserInfo()
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
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

.profile-content-wrapper {
  max-width: 900px;
  margin: 20px auto;
}

.profile-card {
  border: 1px solid var(--el-border-color-lighter);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 10px 20px 10px;
}

.profile-avatar {
  background-color: var(--el-color-primary-light-7);
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.profile-header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-name {
  font-size: 22px;
  font-weight: 500;
}

.info-section {
  padding: 10px;
}

.info-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style> 