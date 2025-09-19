<template>
  <div class="login-bg" style="background-image: url('/login-bg.jpg')">
    <div class="header-container">
      <img src="/logo.png" alt="Logo" class="header-logo" />
      <span class="header-title">中国科学技术大学 校学生国旗护卫队</span>
    </div>
    <div class="login-container">
      <h2 class="login-title">国旗护卫队管理系统</h2>
      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="请输入用户名" 
            :prefix-icon="UserIcon"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            :prefix-icon="LockIcon"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-button native-type="submit" :loading="loading" size="large" block>
            登录
          </el-button>
        </el-form-item>
        <div class="register-link">
          <router-link to="/register">没有账号？立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useUserStore } from '../stores/user'
import { User as UserIcon, Lock as LockIcon } from '@element-plus/icons-vue'

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
        if (userInfo.role === 'admin' || userInfo.role === 'captain' || userInfo.role === 'superadmin') {
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
.login-bg {
  position: relative;
  width: 100vw;
  height: 100vh;
  /* background-image is now an inline style */
  background-repeat: no-repeat;
  background-position: center center;
  background-size: cover;
  display: flex;
  align-items: center;
  justify-content: center; /* 居中以适配移动端 */
  padding: 16px;
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
  color:rgba(20, 59, 211, 0.566);
  font-family: 'Ma Shan Zheng', cursive;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.login-container {
  width: 100%;
  max-width: 360px; 
  background: rgba(255, 255, 255, 0.98);
  border-radius: 12px;
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.login-title {
  text-align: center;
  margin: 0 0 20px 0;
  color: #333;
  font-weight: 600;
  font-size: 20px;
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

.login-container .el-button {
  width: 100%; /* Force button to be full-width */
  background-color: rgb(53, 152, 219);
  color: #ffffff;
  border: none;
}

.login-container .el-button:hover,
.login-container .el-button:focus {
  background-color: rgb(43, 132, 199); /* A slightly darker shade for hover */
  color: #ffffff;
}

@media (max-width: 768px) {
  .header-container {
    top: 16px;
    left: 16px;
    gap: 10px;
  }
  .header-logo {
    width: 48px;
    height: 48px;
  }
  .header-title {
    font-size: 20px;
  }
}
</style> 