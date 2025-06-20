<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '200px'">
      <div class="logo">
        <img src="/logo.png" alt="系统Logo" />
        <div v-show="!isCollapse" class="logo-text">
          <p>中国科学技术大学</p>
          <p>校学生国旗护卫队</p>
        </div>
      </div>
      <el-menu
        :default-active="$route.path"
        class="el-menu-vertical"
        :collapse="isCollapse"
        router
      >
        <el-menu-item index="/dashboard" v-if="isAdmin">
          <el-icon><DataLine /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/events">
          <el-icon><Calendar /></el-icon>
          <template #title>活动列表</template>
        </el-menu-item>
        <el-menu-item index="/trainings">
          <el-icon><List /></el-icon>
          <template #title>训练列表</template>
        </el-menu-item>
        <el-menu-item index="/flag-records">
          <el-icon><Document /></el-icon>
          <template #title>升降旗记录</template>
        </el-menu-item>
        <el-menu-item index="/points">
          <el-icon><Star /></el-icon>
          <template #title>积分记录</template>
        </el-menu-item>
        <el-menu-item index="/points-manage" v-if="isAdmin">
          <el-icon><Edit /></el-icon>
          <template #title>积分管理</template>
        </el-menu-item>
        <el-menu-item index="/users" v-if="isAdmin">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title>个人信息</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>国旗护卫队管理系统</h2>
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              {{ userStore.userInfo?.name }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import {
  DataLine,
  Calendar,
  Document,
  User,
  ArrowDown,
  List,
  Star,
  Edit
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)

// 计算属性：判断是否为管理员
const isAdmin = computed(() => {
  return userStore.userInfo?.role === 'admin'
})

const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
}

.el-menu {
  border-right: none;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  padding: 0 20px;
}

.header-content {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 15px;
  color: white;
  font-size: 18px;
  font-weight: bold;
}

.logo img {
  max-height: 40px;
  max-width: 40px;
  margin-right: 10px;
}

.logo-text {
  color: white;
  line-height: 1.3;
  font-family: "Microsoft YaHei", "微软雅黑", "SimHei", "黑体", sans-serif;
}

.logo-text p {
  margin: 0;
  font-weight: 600;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
}

.logo-text p:first-child {
  font-size: 15px;
}

.logo-text p:last-child {
  font-size: 13px;
}
</style> 