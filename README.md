# Team-Sys: 校学生国旗护卫队管理系统

`Team-Sys` 是一个功能完备的全栈Web应用，旨在为校学生国旗护卫队提供一个高效、直观的活动与成员管理解决方案。系统内置了用户管理、训练日程、活动组织、积分激励等核心模块，采用现代化的技术栈构建，前端基于 Vue.js，后端则由 Flask 驱动。

## ? 核心功能

- **? 用户管理**: 基于角色的权限控制（成员、管理员、超级管理员），支持用户信息的增删改查。
- **?? 训练管理**: 轻松创建、编辑和管理训练日程，追踪成员的报名与考勤情况。
- **? 活动管理**: 便捷地组织团队活动，并可将活动与特定的训练项目进行关联。
- **? 积分系统**: 为参与训练、升降旗等活动的用户授予积分，建立激励机制。
- **? 管理仪表盘**: 为管理员提供系统数据概览，包括待办事项、近期活动等，实现一站式管理。
- **? RESTful API**: 提供定义清晰的 API 接口，确保前后端数据通信的稳定与高效。

## ?? 技术栈

|              | 技术                                                                  |
| ------------ | --------------------------------------------------------------------- |
| **后端**     | Python 3, Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended        |
| **前端**     | Vue 3 (Composition API), TypeScript, Element Plus, Pinia, Vue Router, Axios |
| **数据库**   | MySQL                                                                 |
| **开发工具** | Node.js, npm, pip, virtualenv                                         |

## ? 本地部署指南

请遵循以下步骤在您的本地环境中运行此项目。

### 准备工作

- 确保您的电脑已安装 [Node.js](https://nodejs.org/) (v16+ 版本)
- 确保您的电脑已安装 [Python](https://www.python.org/) (v3.8+ 版本)
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
#    - 首先，在您的 MySQL 中创建一个新的数据库 (例如 `teamsys_db`)。
#    - 然后，打开 `backend/config.py` 文件，修改 `SQLALCHEMY_DATABASE_URI` 的值为您的数据库连接信息。
#      示例: 'mysql+pymysql://你的用户名:你的密码@127.0.0.1/teamsys_db'

# 5. 初始化数据库并创建超级管理员账号
#    请将 <...> 部分替换为您想要的信息
flask --app backend/app.py drop-db --yes
flask --app backend/app.py init-db
flask --app backend/app.py create-user <用户名> <密码> <姓名> <学号(如:PB23000000)> --role superadmin

# 6. 启动后端开发服务器
flask run
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

## ? 项目结构

```
system/
├── backend/            # Flask 后端源代码
│   ├── app.py          # 应用主文件
│   ├── cli.py          # 自定义 Flask 命令
│   ├── config.py       # 配置文件
│   ├── models.py       # 数据库模型
│   └── routes/         # API 路由蓝图
├── frontend/           # Vue.js 前端源代码
│   ├── src/
│   │   ├── components/ # 可复用组件
│   │   ├── stores/     # Pinia 状态管理
│   │   ├── views/      # 页面视图
│   │   └── ...
│   └── package.json
└── README.md           # 本文档
```

## 许可证

MIT 