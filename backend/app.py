# 在文件顶部添加
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from flask import Flask, jsonify, g, request, current_app, send_from_directory, make_response
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from extensions import db, jwt, migrate, init_extensions
from flasgger import Swagger
from models import User, OperationLog
from flask_cors import CORS
from cli import init_db, drop_db, create_admin, list_users, cleanup_records, backup_db, check_system, reset_password, export_data, init_cli
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from datetime import timedelta
from routes.auth import auth_bp
from routes.users import users_bp
from routes.trainings import bp as trainings_bp
from routes.events import bp as events_bp
from routes.points import bp as points_bp
from routes import register_blueprints

# 创建配置字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 初始化CORS
cors = CORS()

def setup_logging(app):
    """配置日志"""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('应用启动')
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
    console_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG)

def setup_swagger(app):
    """配置Swagger文档"""
    swagger_config = {
        "headers": [],
        "specs": [{
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs"
    }
    Swagger(app, config=swagger_config)

def setup_cors(app):
    """配置CORS"""
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": app.config['CORS_METHODS'],
            "allow_headers": app.config['CORS_ALLOW_HEADERS'],
            "expose_headers": app.config['CORS_EXPOSE_HEADERS'],
            "supports_credentials": app.config['CORS_SUPPORTS_CREDENTIALS'],
            "max_age": app.config['CORS_MAX_AGE']
        }
    })
    
    # 添加CORS预检请求处理
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
            response.headers.add("Access-Control-Allow-Headers", ", ".join(app.config['CORS_ALLOW_HEADERS']))
            response.headers.add("Access-Control-Allow-Methods", ", ".join(app.config['CORS_METHODS']))
            response.headers.add("Access-Control-Allow-Credentials", "true")
            response.headers.add("Access-Control-Max-Age", str(app.config['CORS_MAX_AGE']))
            return response

def setup_error_handlers(app):
    """配置错误处理器"""
    @app.errorhandler(400)
    def bad_request_error(error):
        app.logger.warning(f'Bad request: {str(error)}')
        return jsonify({'msg': 'Bad request', 'error': str(error)}), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.warning(f'Unauthorized: {str(error)}')
        return jsonify({'msg': 'Unauthorized', 'error': str(error)}), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f'Forbidden: {str(error)}')
        return jsonify({'msg': 'Forbidden', 'error': str(error)}), 403

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'Not found: {str(error)}')
        return jsonify({'msg': 'Not found', 'error': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal server error: {str(error)}')
        return jsonify({'msg': 'Internal server error', 'error': str(error)}), 500

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        db.session.rollback()
        app.logger.error(f'Database error: {str(error)}')
        return jsonify({'msg': 'Database error', 'error': str(error)}), 500

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        app.logger.error(f'HTTP error: {str(error)}')
        return jsonify({'msg': error.name, 'error': str(error)}), error.code

def setup_middleware(app):
    """配置中间件"""
    @app.before_request
    def log_request_info():
        g.start_time = time.time()
        if request.endpoint and 'static' not in request.endpoint:
            app.logger.info(f'Request: {request.method} {request.url} from {request.remote_addr}')
    
    @app.after_request
    def log_response_info(response):
        if request.endpoint and 'static' not in request.endpoint:
            duration = time.time() - g.start_time
            app.logger.info(f'Response: {response.status} in {duration:.2f}s')
        return response

def create_admin_user(app):
    """创建默认管理员用户"""
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                role='admin',
                name='管理员',
                student_id='AD00000000',
                college='学院',
                height=170,
                weight=60,
                shoe_size=42,
                total_points=0.0,
                phone_number='00000000000'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info('Default admin user created.')
        else:
            app.logger.info('Default admin user already exists.')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['JSON_AS_ASCII'] = False
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化扩展
    init_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册CLI命令
    init_cli(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)