<template>
  <el-container class="layout-container" :class="{ 'is-mobile': isMobile }">
    <el-aside :width="isCollapse ? '64px' : '220px'" :class="{ 'mobile-open': isMobile && mobileMenuOpen }">
      <div class="logo">
        <img src="/logo.png" alt="系统Logo" />
        <transition name="logo-fade">
          <div v-if="!isCollapse" class="logo-text">
            <p>中国科学技术大学</p>
            <p>校学生国旗护卫队</p>
          </div>
        </transition>
      </div>
      <el-menu
        :default-active="$route.path"
        class="el-menu-vertical"
        :collapse="isMobile ? false : isCollapse"
        router
      >
        <el-menu-item index="/dashboard" v-if="isAdmin">
          <el-icon><DataLine /></el-icon>
          <template #title><span class="menu-title">仪表盘</span></template>
        </el-menu-item>
        <el-menu-item index="/events">
          <el-icon><Calendar /></el-icon>
          <template #title><span class="menu-title">活动列表</span></template>
        </el-menu-item>
        <el-menu-item index="/trainings">
          <el-icon><List /></el-icon>
          <template #title><span class="menu-title">训练列表</span></template>
        </el-menu-item>
        <el-menu-item index="/flag-records">
          <el-icon><Document /></el-icon>
          <template #title><span class="menu-title">升降旗记录</span></template>
        </el-menu-item>
        <el-menu-item index="/points">
          <el-icon><Star /></el-icon>
          <template #title><span class="menu-title">积分记录</span></template>
        </el-menu-item>
        <el-menu-item index="/points-manage" v-if="isAdmin">
          <el-icon><Edit /></el-icon>
          <template #title><span class="menu-title">积分管理</span></template>
        </el-menu-item>
        <el-menu-item index="/users" v-if="isAdmin">
          <el-icon><Avatar /></el-icon>
          <template #title><span class="menu-title">用户管理</span></template>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title><span class="menu-title">个人信息</span></template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-left">
          <el-icon class="collapse-icon" @click="toggleMenu">
            <component :is="(isMobile ? !mobileMenuOpen : !isCollapse) ? 'Expand' : 'Fold'" />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path ? { path: item.path } : undefined">
              {{ item.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <span class="user-name">{{ userStore.userInfo?.name }}</span>
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
    <!-- 移动端抽屉遮罩层 -->
    <div v-if="isMobile && mobileMenuOpen" class="mobile-mask" @click="mobileMenuOpen = false"></div>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute, RouteLocationMatched } from 'vue-router'
import { useUserStore } from '../stores/user'
import {
  DataLine,
  Calendar,
  Document,
  User,
  ArrowDown,
  List,
  Star,
  Edit,
  Avatar,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)
const breadcrumbs = ref<RouteLocationMatched[]>([])
const isMobile = ref(false)
const mobileMenuOpen = ref(false)

const getBreadcrumbs = () => {
  const staticItem = { path: '', meta: { title: '国旗护卫队管理系统' } } as RouteLocationMatched

  const matched = route.matched.filter(item => item.meta && item.meta.title)
  
  breadcrumbs.value = [staticItem, ...matched]
}

watch(
  () => route.path,
  () => {
    getBreadcrumbs()
  }
)

let handleResize: (() => void) | null = null

onMounted(() => {
  getBreadcrumbs()
  handleResize = () => {
    isMobile.value = window.innerWidth < 768
    if (isMobile.value) {
      isCollapse.value = true
    }
  }
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (handleResize) window.removeEventListener('resize', handleResize)
})

// 计算属性：判断是否为管理员或超级管理员
const isAdmin = computed(() => {
  const role = userStore.userInfo?.role
  return role === 'admin' || role === 'superadmin'
})

const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

// 菜单在移动端与桌面端的切换逻辑
const toggleMenu = () => {
  if (isMobile.value) {
    mobileMenuOpen.value = !mobileMenuOpen.value
  } else {
    isCollapse.value = !isCollapse.value
  }
}

// 路由变更时，如果在移动端则自动关闭抽屉
watch(() => route.path, () => {
  if (isMobile.value) mobileMenuOpen.value = false
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #f7f8fa;
  border-right: 1px solid #e8e8e8;
  transition: width 0.3s;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 220px;
}

.el-menu {
  border-right: none;
  background-color: transparent;
  margin-top: 10px;
}

.el-menu-item {
  height: 50px;
  line-height: 50px;
  margin: 0 6px 0 2px;
  border-radius: 6px;
  color: #606266;
  transition: all 0.2s;
  position: relative;
}

.el-menu-item .el-icon {
  font-size: 18px;
}

.el-menu-item:hover {
  background-color: #f0f2f5;
  color: #2d8cf0;
}

.el-menu-item.is-active {
  background-color: rgba(121, 187, 255, 0.15);
  color: #79bbff;
  font-weight: bold;
}

.el-menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 24px;
  background-color: #79bbff;
  border-radius: 2px;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.header-left, .header-right {
  display: flex;
  align-items: center;
}

.collapse-icon {
  font-size: 22px;
  cursor: pointer;
  margin-right: 15px;
}

.el-breadcrumb :deep(.el-breadcrumb__inner) {
  font-weight: normal;
}

.el-breadcrumb :deep(.el-breadcrumb__item:first-child .el-breadcrumb__inner) {
  font-weight: bold;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-weight: 500;
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
  color: #303133;
  font-size: 18px;
  font-weight: bold;
}

.logo img {
  max-height: 40px;
  max-width: 40px;
  margin-right: 10px;
}

.logo-text {
  color: #303133;
  line-height: 1.3;
  font-family: "Microsoft YaHei", "微软雅黑", "SimHei", "黑体", sans-serif;
  white-space: nowrap;
  overflow: hidden;
}

.logo-text p {
  margin: 0;
  font-weight: 600;
  text-shadow: none;
}

.logo-text p:first-child {
  font-size: 15px;
}

.logo-text p:last-child {
  font-size: 13px;
}

.logo-fade-enter-active,
.logo-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
  transition-delay: 0.1s;
}

.logo-fade-enter-from,
.logo-fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.menu-title {
  display: inline-block;
  opacity: 1;
  transform: translateX(0);
  transition: opacity 0.2s ease, transform 0.2s ease;
  transition-delay: 0.1s;
}

.el-menu--collapse .menu-title {
  opacity: 0;
  transform: translateX(-10px);
  transition-delay: 0s;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .el-header {
    padding: 0 12px;
  }
  .el-main {
    padding: 12px;
  }
  .logo-text {
    display: none;
  }
  .el-breadcrumb {
    display: none;
  }
  .collapse-icon {
    margin-right: 8px;
  }
  /* 侧边栏改为抽屉 */
  .el-aside {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 2000;
    width: 220px !important;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    background-color: #f7f8fa;
  }
  .el-aside.mobile-open {
    transform: translateX(0);
  }
  .mobile-mask {
    position: fixed;
    left: 0;
    top: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.3);
    z-index: 1999;
  }
}
</style> 