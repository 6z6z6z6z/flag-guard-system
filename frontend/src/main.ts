import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局错误处理
app.config.errorHandler = (err: unknown, instance: any, info: string) => {
  if (err instanceof Error && err.message?.includes('ResizeObserver loop')) {
    return
  }
  console.error('Global error:', err)
  console.error('Error info:', info)
}

// 处理 ResizeObserver 错误
const originalConsoleError = console.error
console.error = (...args) => {
  if (args[0]?.includes?.('ResizeObserver loop')) {
    return
  }
  originalConsoleError.apply(console, args)
}

// 使用插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

// 等待路由准备就绪后再挂载应用
router.isReady().then(() => {
  app.mount('#app')
}) 