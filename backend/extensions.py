from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS

# 数据库
db = SQLAlchemy()

# JWT认证
jwt = JWTManager()

# 数据库迁移
migrate = Migrate()

cors = CORS()

def init_extensions(app):
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    # 配置 JWT
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        app.logger.debug(f"JWT user_identity_lookup called with user: {user}")
        if isinstance(user, str):
            return user
        return str(user.user_id) if user else None

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        app.logger.debug(f"JWT user_lookup_callback called with jwt_data: {jwt_data}")
        identity = jwt_data["sub"]
        if not identity:
            app.logger.warning("No identity found in JWT data")
            return None
        from models import User
        user = User.query.get(int(identity))
        app.logger.debug(f"Found user: {user.username if user else None}")
        return user

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        app.logger.warning(f"Expired token detected: {jwt_payload}")
        return {"msg": "Token has expired", "code": 401}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        app.logger.warning(f"Invalid token detected: {error_string}")
        return {"msg": "Invalid token", "code": 401}, 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error_string):
        app.logger.warning(f"Unauthorized access: {error_string}")
        return {"msg": "Missing token", "code": 401}, 401