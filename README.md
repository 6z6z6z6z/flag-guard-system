# Flag-Guard-System: 校学生国旗护卫队管理系统

`Flag-Guard-System` 是一个功能完备的全栈Web应用，旨在为校学生国旗护卫队提供一个高效、直观的活动与成员管理解决方案。系统内置了用户管理、训练日程、活动组织、积分激励等核心模块，采用现代化的技术栈构建，前端基于 Vue.js，后端则由 Flask 驱动。

## ✨ 核心功能

- **👤 用户管理**: 基于角色的权限控制（成员、管理员、超级管理员），支持用户注册、登录、个人资料管理和用户删除。
- **🏋️ 训练管理**: 创建、编辑和管理训练日程，支持训练报名、出勤记录和训练审核功能。
- **🎉 活动管理**: 组织团队活动，支持活动创建、报名管理，并可将活动与特定训练项目关联。
- **⭐ 积分系统**: 为参与训练、升降旗等活动的用户授予积分，提供积分记录查询和手动积分调整功能。
- **🏁 升降旗管理**: 记录和审核升降旗活动，追踪成员参与情况。
- **📊 管理仪表盘**: 为管理员提供系统数据概览，包括用户统计、活动概况、训练数据等。
- **📁 文件上传**: 支持图片文件上传和管理功能。
- **🔌 RESTful API**: 提供完整的API接口，支持Swagger文档自动生成。

## 🛠️ 技术栈

|              | 技术                                                                  |
| ------------ | --------------------------------------------------------------------- |
| **后端**     | Python 3, Flask, PyMySQL, Flask-JWT-Extended, Flasgger (Swagger)   |
| **前端**     | Vue 3 (Composition API), TypeScript, Element Plus, Pinia, Vue Router, Axios |
| **数据库**   | MySQL                                                                 |
| **开发工具** | Node.js, npm, pip, virtualenv, Black, Flake8, pytest               |

## 🚀 本地部署指南

请遵循以下步骤在您的本地环境中运行此项目。

### 准备工作

- 确保您的电脑已安装 [Node.js](https://nodejs.org/) (v16+ 版本)
- 确保您的电脑已安装 [Python](https://www.python.org/) (v3.9+ 版本)
- 确保您的电脑已安装并运行 [MySQL](https://www.mysql.com/) 服务

### 后端服务启动

```bash
# 1. 进入后端项目目录
cd backend

# 2. 创建并激活 Python 虚拟环境
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
# python3 -m venv venv
# source venv/bin/activate

# 3. 安装所有依赖
pip install -r requirements.txt

# 4. 配置数据库连接
#    - 首先，在您的 MySQL 中创建一个新的数据库 (例如 `system`)。
#    - 然后，打开 `backend/config.py` 文件，修改数据库连接配置：
#      MYSQL_HOST、MYSQL_USER、MYSQL_PASSWORD、MYSQL_DATABASE 等参数
#      或者创建 `.env` 文件设置环境变量

# 5. 初始化数据库并创建超级管理员账号
#    请将 <...> 部分替换为您想要的信息
flask --app app.py drop-db --yes
flask --app app.py init-db
flask --app app.py create-user <用户名> <密码> <姓名> <学号(如:PB23000000)> --role superadmin

# 6. 启动后端开发服务器
python app.py
```

### 前端服务启动

```bash
# 1. 打开一个新的终端，进入前端项目目录
cd frontend

# 2. 安装所有依赖
npm install

# 3. 启动前端开发服务器
npm run serve
```

当所有步骤完成后，您可以通过浏览器访问 `http://localhost:8080` 来查看运行中的项目。

## 📁 项目结构

```
system/
├── backend/            # Flask 后端源代码
│   ├── app.py          # 应用主文件
│   ├── cli.py          # 自定义 Flask 命令
│   ├── config.py       # 配置文件
│   ├── extensions.py   # 扩展初始化
│   ├── db_connection.py # 数据库连接管理
│   ├── models_pymysql.py # 数据模型
│   ├── sql/            # SQL相关文件
│   │   ├── queries.py   # SQL查询语句
│   │   └── schema.sql   # 数据库架构
│   ├── routes/         # API 路由蓝图
│   │   ├── auth.py      # 认证路由
│   │   ├── dashboard.py # 仪表盘路由
│   │   ├── events.py    # 活动管理路由
│   │   ├── file.py      # 文件上传路由
│   │   ├── flag.py      # 升降旗管理路由
│   │   ├── points.py    # 积分管理路由
│   │   ├── trainings.py # 训练管理路由
│   │   ├── users.py     # 用户管理路由
│   │   └── users_delete.py # 用户删除路由
│   ├── utils/          # 工具函数
│   │   ├── auth.py      # 认证工具
│   │   ├── export.py    # 数据导出工具
│   │   ├── pagination.py # 分页工具
│   │   ├── route_utils.py # 路由工具
│   │   ├── time_utils.py # 时间工具
│   │   └── upload.py    # 文件上传工具
│   ├── middleware/     # 中间件
│   │   └── logging.py   # 日志中间件
│   └── uploads/        # 文件上传目录
├── frontend/           # Vue.js 前端源代码
│   ├── src/
│   │   ├── components/ # 可复用组件
│   │   │   └── ECharts.vue # 图表组件
│   │   ├── layout/     # 布局组件
│   │   │   └── index.vue # 主布局
│   │   ├── router/     # 路由配置
│   │   │   └── index.ts
│   │   ├── stores/     # Pinia 状态管理
│   │   │   ├── dashboard.ts
│   │   │   ├── event.ts
│   │   │   ├── training.ts
│   │   │   └── user.ts
│   │   ├── types/      # TypeScript 类型定义
│   │   ├── utils/      # 工具函数
│   │   │   ├── format.ts
│   │   │   ├── formatDate.ts
│   │   │   └── request.ts
│   │   ├── views/      # 页面视图
│   │   │   ├── Dashboard.vue     # 仪表盘
│   │   │   ├── EventManage.vue   # 活动管理
│   │   │   ├── Events.vue        # 活动列表
│   │   │   ├── FlagRecords.vue   # 升降旗记录
│   │   │   ├── FlagReview.vue    # 升降旗审核
│   │   │   ├── Login.vue         # 登录页面
│   │   │   ├── Points.vue        # 积分记录
│   │   │   ├── PointsManage.vue  # 积分管理
│   │   │   ├── Profile.vue       # 个人资料
│   │   │   ├── Register.vue      # 注册页面
│   │   │   ├── TrainingAttendance.vue # 训练出勤
│   │   │   ├── TrainingReview.vue # 训练审核
│   │   │   ├── Trainings.vue     # 训练列表
│   │   │   └── Users.vue         # 用户管理
│   │   └── styles/     # 样式文件
│   └── package.json
└── README.md           # 本文档
```

## 🔧 CLI 工具

系统提供了丰富的命令行工具用于管理和维护：

```bash
# 数据库管理
flask --app app.py init-db              # 初始化数据库
flask --app app.py drop-db --yes        # 删除数据库

# 用户管理
flask --app app.py create-user <用户名> <密码> <姓名> <学号> --role <角色>
flask --app app.py delete-user <用户名>
flask --app app.py list-users            # 列出所有用户
flask --app app.py reset-password <用户名> <新密码>

# 系统维护
flask --app app.py cleanup-records --days <天数>  # 清理历史记录
flask --app app.py backup-db <备份文件名>          # 备份数据库
flask --app app.py check-system                   # 系统检查
flask --app app.py export-data <输出文件>         # 导出数据
```

## 📊 API 文档

后端集成了 Swagger 文档，启动服务器后可访问：
- API 文档：`http://localhost:5000/apidocs`
- API 规范：`http://localhost:5000/apispec.json`

## 🚀 开发特性

### 数据库架构
- 采用 PyMySQL 直接连接 MySQL 数据库
- 支持数据库连接池和事务管理
- 完整的数据库 Schema 定义 (`sql/schema.sql`)
- SQL 查询语句模块化管理 (`sql/queries.py`)

### 安全特性
- JWT Token 认证机制
- 基于角色的权限控制 (RBAC)
- CORS 跨域配置
- 请求参数验证和错误处理

### 开发工具
- 代码格式化：Black
- 代码检查：Flake8  
- 测试框架：pytest
- API 文档：Swagger/Flasgger

### 日志系统
- 结构化日志记录
- 请求/响应日志追踪
- 错误日志和异常处理

## 许可证

MIT 
