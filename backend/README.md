# 校国旗护卫队管理系统后端

## 项目说明
这是一个基于 Flask 的校国旗护卫队管理系统后端，提供用户管理、活动管理、训练管理、升降旗记录等功能。

## 功能特性
- 用户认证与授权
- 活动管理
- 训练管理
- 升降旗记录
- 积分系统
- 文件上传
- API 文档（Swagger）

## 技术栈
- Python 3.8+
- Flask
- SQLAlchemy
- JWT
- Swagger

## 安装说明

1. 克隆项目
```bash
git clone <repository-url>
cd backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
复制 `.env.example` 为 `.env` 并修改配置：
```bash
cp .env.example .env
```

5. 初始化数据库
```bash
flask init-db
```

6. 创建管理员用户
```bash
flask create-admin <username> <password> <name> <student_id>
```

## 运行项目

1. 启动开发服务器
```bash
flask run
```

2. 访问 API 文档
```
http://localhost:5000/apidocs
```

## 命令行工具

系统提供以下命令行工具：

- `flask init-db`: 初始化数据库
- `flask drop-db`: 删除所有数据库表
- `flask create-admin`: 创建管理员用户
- `flask list-users`: 列出所有用户
- `flask cleanup-records`: 清理旧记录
- `flask backup-db`: 备份数据库
- `flask check-system`: 检查系统状态
- `flask reset-password`: 重置用户密码
- `flask export-data`: 导出系统数据

## 项目结构
```
backend/
├── app.py              # 应用入口
├── config.py           # 配置文件
├── extensions.py       # Flask扩展
├── models.py           # 数据模型
├── cli.py             # 命令行工具
├── requirements.txt    # 项目依赖
├── .env               # 环境变量
├── routes/            # 路由模块
├── utils/             # 工具函数
├── middleware/        # 中间件
├── uploads/           # 上传文件目录
└── logs/              # 日志目录
```

## 开发指南

1. 代码风格
- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查

2. 测试
```bash
pytest
```

3. 数据库迁移
```bash
flask db migrate -m "migration message"
flask db upgrade
```

## 部署说明

1. 生产环境配置
- 修改 `.env` 文件中的环境变量
- 设置 `FLASK_ENV=production`
- 配置数据库连接
- 设置安全的密钥

2. 使用 Gunicorn 运行
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证
MIT License 