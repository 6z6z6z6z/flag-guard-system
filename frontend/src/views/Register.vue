<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <h2 class="register-title">用户注册</h2>
      </template>
      <el-form
        ref="formRef"
        :model="registerForm"
        :rules="rules"
        label-width="80px"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input 
            v-model="registerForm.name" 
            placeholder="请输入真实姓名"
            @input="handleInput('name')"
          />
        </el-form-item>
        <el-form-item label="学号" prop="student_id">
          <el-input v-model="registerForm.student_id" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="学院" prop="college">
          <el-input v-model="registerForm.college" placeholder="请输入学院" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="registerForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="队长" value="captain" />
            <el-option label="队员" value="member" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" block>
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <el-button v-if="showReturnButton" @click="router.push('/login')" block>返回登录</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const formRef = ref<FormInstance>()
const showReturnButton = ref(false)

const registerForm = reactive({
  username: '',
  password: '',
  name: '',
  student_id: '',
  college: '',
  role: 'member'
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  student_id: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { pattern: /^[A-Z]{2}\d{8}$/, message: '学号格式为2个大写字母+8个数字', trigger: 'blur' }
  ],
  college: [{ required: true, message: '请输入学院', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const handleRegister = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    const res = await userStore.register(registerForm)
    if (res.status === 201) {
      ElMessage({
        type: 'success',
        message: '注册成功',
        duration: 2000
      })
      setTimeout(() => {
        showReturnButton.value = true
      }, 1000)
    } else {
      ElMessage.error(res.data?.msg || '注册失败，请重试')
    }
  } catch (error: any) {
    if (error.response?.data?.msg) {
      ElMessage.error(error.response.data.msg)
    } else if (error.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('注册失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

const handleInput = (field: keyof typeof registerForm) => {
  registerForm[field] = registerForm[field].toString().trim()
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.register-card {
  width: 400px;
}

.register-title {
  text-align: center;
  margin: 0;
  color: #409eff;
}
</style>