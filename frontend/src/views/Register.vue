<template>
  <div class="page-bg" style="background-image: url('/login-bg.jpg')">
    <div class="header-container">
      <img src="/logo.png" alt="Logo" class="header-logo" />
      <span class="header-title">中国科学技术大学 校学生国旗护卫队</span>
    </div>

    <div class="form-wrapper">
      <el-card class="register-card">
        <template #header>
          <h2 class="register-title">用户注册</h2>
        </template>
        <el-form
          ref="formRef"
          :model="registerForm"
          :rules="rules"
          label-width="80px"
          @submit.prevent="handleSubmit"
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
          <el-form-item label="手机号" prop="phone_number">
            <el-input v-model="registerForm.phone_number" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" native-type="submit" :loading="loading" block>
              注册
            </el-button>
          </el-form-item>
        </el-form>
        <div class="register-link">
          <router-link to="/login">已有账号？立即登录</router-link>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const loading = ref(false)
const formRef = ref<FormInstance>()
const userStore = useUserStore()

const registerForm = reactive({
  username: '',
  password: '',
  name: '',
  student_id: '',
  college: '',
  phone_number: '',
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
  phone_number: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^\d{11}$/, message: '手机号格式不正确', trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    loading.value = true
    await formRef.value.validate()
    
    // 注册
    await userStore.register(registerForm)
    
    // 注册成功，显示确认对话框
    ElMessageBox.confirm(
      '注册成功！是否立即登录？',
      '提示',
      {
        confirmButtonText: '立即登录',
        cancelButtonText: '稍后登录',
        type: 'success',
        showClose: false,
        closeOnClickModal: false,
        closeOnPressEscape: false
      }
    ).then(() => {
      // 用户点击"立即登录"，跳转到登录页
      router.push('/login')
    }).catch(() => {
      // 用户点击"稍后登录"，清空表单
      formRef.value?.resetFields()
    })
  } catch (error: any) {
    console.error('注册失败:', error)
    // 显示错误消息，但不跳转
    ElMessage({
      type: 'error',
      message: error.response?.data?.msg || '注册失败，请稍后重试',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

const handleInput = (field: keyof typeof registerForm) => {
  registerForm[field] = registerForm[field].toString().trim()
}
</script>

<style scoped>
.page-bg {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-repeat: no-repeat;
  background-position: center center;
  background-size: cover;
  display: flex;
  align-items: center;
  justify-content: flex-end; /* A- Move content to the right */
}

.header-container {
  position: absolute;
  top: 5vh;
  left: 5vw;
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-logo {
  width: 65px;
  height: 65px;
}

.header-title {
  font-size: 30px;
  font-weight: normal;
  color: rgba(20, 59, 211, 0.566);
  font-family: 'Ma Shan Zheng', cursive;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* B- Wrapper to position the card */
.form-wrapper {
  margin-right: 5vw;
}

/* C- Original styles, slightly adjusted */
.register-card {
  width: 380px; 
  background: rgba(255, 255, 255, 0.98);
  border-radius: 8px;
  border: none; 
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
 
}


.register-title {
  text-align: center;
  margin: 0;
  color: #333;
  font-weight: 600;
  font-size: 22px;
}

.register-link {
  text-align: center;
  margin-top: 16px;
}

.register-link a {
  color: #409eff;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>