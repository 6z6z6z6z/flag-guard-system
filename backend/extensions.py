from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

# 数据库
db = SQLAlchemy()

# JWT认证
jwt = JWTManager()

# 数据库迁移
migrate = Migrate()