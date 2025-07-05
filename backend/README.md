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
- JWT 认证

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
  - `trainings.py` - 训练路由
  - `events.py` - 活动路由
  - `flag.py` - 升降旗路由
  - `points.py` - 积分路由
  - `file.py` - 文件路由
- `utils/` - 工具函数
- `middleware/` - 中间件
- `uploads/` - 上传文件存储目录
- `instance/` - 实例配置和数据

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
flask init-db
```

5. 创建管理员用户：

```bash
flask create-user -u admin -p password -r superadmin -n Admin -s ADMIN001 -c College
```

6. 运行应用：

```bash
flask run
```

## API文档

启动应用后，访问 `/apidocs` 可以查看Swagger API文档。

## 命令行工具

- `flask init-db` - 初始化数据库
- `flask drop-db` - 删除数据库(谨慎使用)
- `flask create-user` - 创建用户
- `flask delete-user` - 删除用户
- `flask list-users` - 列出所有用户
- `flask cleanup-records` - 清理过期记录
- `flask backup-db` - 备份数据库
- `flask check-system` - 检查系统状态
- `flask reset-password` - 重置用户密码

## 项目说明

1. 项目结构
- 使用 Black 格式化代码
- 使用 Flake8 检查代码

2. 测试
```bash
pytest
```

3. 数据库迁移
```bash
flask db migrate -m "migration message"
flask db upgrade
```

4. 项目说明
- 修改 `.env` 文件中的配置
- 设置 `FLASK_ENV=production`
- 备份数据库
- 确保所有敏感信息加密

5. 使用 Gunicorn 部署
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

6. 贡献项目
- Fork 项目
- 提供支持
- 提交 Pull Request

7. 项目验证
MIT License 