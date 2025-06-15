<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2 class="login-title">国旗护卫队管理系统</h2>
      </template>
      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        label-width="80px"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" block>
            登录
          </el-button>
        </el-form-item>
        <div class="register-link">
          <router-link to="/register">没有账号？立即注册</router-link>
        </div>
      </el-form>
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

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true
    
    // 登录
    const loginResult = await userStore.login(loginForm.username, loginForm.password)
    console.log('Login result:', loginResult)
    
    // 确保token已经设置
    const currentToken = userStore.getToken()
    console.log('Current token after login:', currentToken)
    
    if (!currentToken) {
      throw new Error('登录失败：未获取到token')
    }

    // 获取用户信息
    try {
      await userStore.getUserInfo()
      const userInfo = userStore.userInfo
      console.log('User info after login:', userInfo)
      
      // 显示成功消息
      ElMessage({
        type: 'success',
        message: '登录成功',
        duration: 2000
      })

      // 根据用户角色跳转到不同页面
      if (userInfo) {
        if (userInfo.role === 'admin' || userInfo.role === 'captain') {
          router.replace('/dashboard')
        } else {
          router.replace('/profile')
        }
      } else {
        router.replace('/')
      }
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      ElMessage.error(error.response?.data?.msg || '获取用户信息失败，请重新登录')
      userStore.logout()
      return
    }
  } catch (error: any) {
    console.error('登录失败:', error)
    // 统一处理错误消息
    const errorMessage = error.response?.data?.msg || error.message || '登录失败，请检查用户名和密码'
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.login-card {
  width: 400px;
}

.login-title {
  text-align: center;
  margin: 0;
  color: #409eff;
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