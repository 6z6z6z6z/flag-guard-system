<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <h3>个人信息</h3>
          <el-button type="primary" @click="handleEdit" v-if="!isEditing">
            编辑信息
          </el-button>
          <div v-else>
            <el-button type="success" @click="handleSave">保存</el-button>
            <el-button @click="handleCancel">取消</el-button>
          </div>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="userForm"
        :rules="rules"
        label-width="100px"
        :disabled="!isEditing"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="userForm.name" disabled />
        </el-form-item>
        <el-form-item label="学号" prop="student_id">
          <el-input v-model="userForm.student_id" disabled />
        </el-form-item>
        <el-form-item label="学院" prop="college">
          <el-input v-model="userForm.college" disabled />
        </el-form-item>
        <el-form-item label="手机号" prop="phone_number">
          <el-input v-model="userForm.phone_number" disabled />
        </el-form-item>
        <el-form-item label="身高(cm)" prop="height">
          <el-input-number
            v-model="userForm.height"
            :min="140"
            :max="220"
            :precision="0"
          />
        </el-form-item>
        <el-form-item label="体重(kg)" prop="weight">
          <el-input-number
            v-model="userForm.weight"
            :min="35"
            :max="150"
            :precision="1"
          />
        </el-form-item>
        <el-form-item label="鞋码" prop="shoe_size">
          <el-input-number
            v-model="userForm.shoe_size"
            :min="34"
            :max="48"
            :precision="0"
          />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import request from '../utils/request'

const formRef = ref<FormInstance>()
const isEditing = ref(false)

const userForm = ref({
  username: '',
  name: '',
  student_id: '',
  college: '',
  height: 170,
  weight: 60,
  shoe_size: 40,
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
      height: height || 170,
      weight: weight || 60,
      shoe_size: shoe_size || 40,
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
    await request.put('/users/profile', {
      height: userForm.value.height,
      weight: userForm.value.weight,
      shoe_size: userForm.value.shoe_size
    })
    ElMessage.success('保存成功')
    isEditing.value = false
  } catch (error) {
    ElMessage.error('保存失败')
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

.profile-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}
</style> 