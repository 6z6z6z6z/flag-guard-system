# Flag Guard System Frontend

## 项目概述

Flag Guard System 前端是基于 Vue 3 + TypeScript 构建的现代化单页应用(SPA)，为校学生国旗护卫队管理系统提供直观的用户界面。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **UI库**: Element Plus + Element Plus Icons
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **构建工具**: Vue CLI 5
- **代码规范**: ESLint + TypeScript ESLint

## 功能模块

### 核心页面
- **登录/注册** (`Login.vue`, `Register.vue`) - 用户认证
- **仪表盘** (`Dashboard.vue`) - 数据概览和统计
- **个人资料** (`Profile.vue`) - 用户信息管理

### 用户管理
- **用户列表** (`Users.vue`) - 用户查看和管理

### 训练管理
- **训练列表** (`Trainings.vue`) - 训练计划查看和管理
- **训练出勤** (`TrainingAttendance.vue`) - 出勤记录管理
- **训练审核** (`TrainingReview.vue`) - 训练申请审核

### 活动管理
- **活动列表** (`Events.vue`) - 活动查看和参与
- **活动管理** (`EventManage.vue`) - 活动创建和编辑

### 升降旗管理
- **升降旗记录** (`FlagRecords.vue`) - 记录查看
- **升降旗审核** (`FlagReview.vue`) - 申请审核

### 积分系统
- **积分记录** (`Points.vue`) - 积分历史查看
- **积分管理** (`PointsManage.vue`) - 积分调整和统计

## 项目结构

```
src/
├── App.vue              # 根组件
├── main.ts              # 应用入口
├── shims-vue.d.ts       # Vue TypeScript 声明
├── env.d.ts             # 环境变量类型声明
├── assets/              # 静态资源
│   └── login-bg.jpg     # 登录背景图
├── components/          # 可复用组件
│   └── ECharts.vue      # 图表组件
├── layout/              # 布局组件
│   └── index.vue        # 主布局
├── router/              # 路由配置
│   └── index.ts         # 路由定义
├── stores/              # Pinia 状态管理
│   ├── dashboard.ts     # 仪表盘状态
│   ├── event.ts         # 活动状态
│   ├── training.ts      # 训练状态
│   └── user.ts          # 用户状态
├── styles/              # 全局样式
│   └── index.css        # 样式定义
├── types/               # TypeScript 类型定义
│   ├── api.ts           # API 接口类型
│   ├── element-plus.d.ts # Element Plus 类型扩展
│   ├── env.d.ts         # 环境类型
│   └── training.ts      # 训练相关类型
├── utils/               # 工具函数
│   ├── format.ts        # 数据格式化
│   ├── formatDate.ts    # 日期格式化
│   └── request.ts       # HTTP 请求封装
└── views/               # 页面组件
    ├── 404.vue          # 404 错误页
    ├── Dashboard.vue    # 仪表盘
    ├── EventManage.vue  # 活动管理
    ├── Events.vue       # 活动列表
    ├── FlagRecords.vue  # 升降旗记录
    ├── FlagReview.vue   # 升降旗审核
    ├── Login.vue        # 登录页
    ├── Points.vue       # 积分记录
    ├── PointsManage.vue # 积分管理
    ├── Profile.vue      # 个人资料
    ├── Records.vue      # 记录页面
    ├── Register.vue     # 注册页
    ├── TrainingAttendance.vue # 训练出勤
    ├── TrainingReview.vue     # 训练审核
    ├── Trainings.vue    # 训练列表
    └── Users.vue        # 用户管理
```

## 开发环境设置

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run serve
```
开发服务器将在 `http://localhost:8080` 启动，支持热重载。

### 构建生产版本
```bash
npm run build
```

### 代码检查和修复
```bash
npm run lint
```

## 开发特性

### 路由权限控制
- 基于用户角色的路由守卫
- 支持 member、admin、captain、superadmin 角色
- 动态菜单生成

### 状态管理
- 使用 Pinia 进行状态管理
- 模块化设计：用户、仪表盘、活动、训练状态分离
- 数据持久化支持

### HTTP 请求
- Axios 二次封装，支持请求/响应拦截
- 自动 JWT Token 处理
- 统一错误处理和提示

### UI 组件
- Element Plus 组件库
- 响应式设计支持
- 自定义主题样式

### TypeScript 支持
- 完整的类型定义
- API 接口类型安全
- 开发时类型检查

## 配置说明

### 环境变量
项目支持通过环境变量配置后端 API 地址等信息。

### 代理配置
开发环境下，前端代理配置在 `vue.config.js` 中设置，用于解决跨域问题。

## 许可证

MIT License
