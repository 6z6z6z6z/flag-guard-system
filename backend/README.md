# Flag Guard System Backend

## 系统概述

Flag Guard System是一个用于管理旗队的系统，支持以下功能：

- 用户管理
- 训练管理
- 活动管理
- 升降旗记录
- 积分管理
- 文件上传

## 技术栈

- Python 3.9+
- Flask 框架
- PyMySQL 数据库连接
- MySQL 数据库
- JWT 认证 (Flask-JWT-Extended)
- Swagger API 文档 (Flasgger)
- CORS 支持 (Flask-CORS)
- 代码质量工具 (Black, Flake8)
- 测试框架 (pytest)

## 数据库迁移说明

本系统已从SQLAlchemy迁移至PyMySQL直接连接MySQL数据库。主要变更如下：

1. 使用`db_connection.py`管理数据库连接
2. 使用`models_pymysql.py`替代原来的`models.py`
3. 将SQL语句独立到`sql/queries.py`中
4. 数据库Schema定义在`sql/schema.sql`中

## 项目结构

- `app.py` - 应用入口
- `config.py` - 配置文件
- `extensions.py` - 扩展初始化
- `db_connection.py` - 数据库连接管理
- `models_pymysql.py` - 数据模型
- `sql/` - SQL相关文件
  - `queries.py` - SQL查询语句
  - `schema.sql` - 数据库架构
- `routes/` - 路由模块
  - `auth.py` - 认证路由
  - `users.py` - 用户路由
  - `users_delete.py` - 用户删除路由
  - `trainings.py` - 训练路由
  - `events.py` - 活动路由
  - `flag.py` - 升降旗路由
  - `points.py` - 积分路由
  - `dashboard.py` - 仪表盘路由
  - `file.py` - 文件路由
- `utils/` - 工具函数
  - `auth.py` - 认证工具
  - `export.py` - 数据导出工具
  - `pagination.py` - 分页工具
  - `route_utils.py` - 路由工具
  - `time_utils.py` - 时间工具
  - `upload.py` - 文件上传工具
- `middleware/` - 中间件
  - `logging.py` - 日志中间件
- `uploads/` - 上传文件存储目录
- `instance/` - 实例配置和数据
  - `logs/` - 日志文件目录

## 运行方法

1. 创建并激活虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置环境变量（可选）：

创建`.env`文件，包含以下内容：

```
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=system
MYSQL_PORT=3306
```

4. 初始化数据库：

```bash
flask --app app.py init-db
```

5. 创建管理员用户：

```bash
flask --app app.py create-user <用户名> <密码> <姓名> <学号> --role superadmin
```

6. 运行应用：

```bash
python app.py
```

## API文档

启动应用后，访问 `/apidocs` 可以查看Swagger API文档。

## 命令行工具

- `flask --app app.py init-db` - 初始化数据库
- `flask --app app.py drop-db --yes` - 删除数据库(谨慎使用)
- `flask --app app.py create-user <用户名> <密码> <姓名> <学号> --role <角色>` - 创建用户
- `flask --app app.py delete-user <用户名>` - 删除用户
- `flask --app app.py list-users` - 列出所有用户
- `flask --app app.py cleanup-records --days <天数>` - 清理过期记录
- `flask --app app.py backup-db <备份文件名>` - 备份数据库
- `flask --app app.py check-system` - 检查系统状态
- `flask --app app.py reset-password <用户名> <新密码>` - 重置用户密码
- `flask --app app.py export-data <输出文件>` - 导出数据

## 开发说明

### 代码质量
- 使用 Black 格式化代码
- 使用 Flake8 检查代码规范
- 使用 pytest 进行单元测试

### 测试
```bash
pytest
pytest --cov  # 运行测试并生成覆盖率报告
```

### 部署
生产环境推荐使用 Gunicorn 部署：
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 环境配置
- 开发环境：设置 `DEBUG=True`
- 生产环境：设置 `DEBUG=False`，配置安全的 SECRET_KEY
- 数据库：确保 MySQL 服务正常运行
- 日志：应用日志存储在 `instance/logs/` 目录

## 许可证

MIT License 