# 国旗护卫队管理系统

这是一个用于管理国旗护卫队日常训练、活动和升旗记录的系统。

## 功能特点

- 用户管理：支持管理员和普通用户角色
- 训练管理：创建、报名、审核训练活动
- 活动管理：创建、报名、审核其他活动
- 升旗记录：记录和审核升旗活动
- 积分系统：自动计算和记录用户积分
- 文件上传：支持上传相关文件

## 技术栈

### 后端
- Python 3.8+
- Flask
- SQLAlchemy
- JWT认证
- Flask-Migrate

### 前端
- Vue 3
- TypeScript
- Element Plus
- Pinia
- Vue Router

## 安装和运行

### 后端

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 初始化数据库：
```bash
python create_tables.py
```

5. 运行服务器：
```bash
python app.py
```

### 前端

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 运行开发服务器：
```bash
npm run serve
```

4. 构建生产版本：
```bash
npm run build
```

## 默认账户

- 管理员账户：
  - 用户名：admin
  - 密码：admin123

## 许可证

MIT 