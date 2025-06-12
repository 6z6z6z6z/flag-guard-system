# 在文件顶部添加
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from flask import Flask, jsonify, g, request, current_app, send_from_directory
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
from extensions import db, jwt, migrate
from flasgger import Swagger
from models import User, OperationLog
from flask_cors import CORS
from cli import init_db, drop_db, create_admin, list_users, cleanup_records, backup_db, check_system, reset_password, export_data
from flask_migrate import Migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # 配置日志
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
    
    # Swagger配置
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs"
    }
    Swagger(app, config=swagger_config)
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    migrate = Migrate(app, db)
    
    # 配置 CORS
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
    
    # 请求日志中间件
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
    
    # 操作日志中间件
    def log_operation(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                if hasattr(g, 'user') and g.user:
                    log = OperationLog(
                        user_id=g.user.user_id,
                        endpoint=request.endpoint,
                        method=request.method,
                        ip_address=request.remote_addr
                    )
                    db.session.add(log)
                    db.session.commit()
                return result
            except Exception as e:
                app.logger.error(f'Operation error: {str(e)}')
                raise
        return decorated_function
    
    # 配置JWT
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return str(user_id)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.filter_by(user_id=identity).one_or_none()
    
# 初始化数据库并创建默认管理员
    with app.app_context():
        db.create_all()
    
    # 创建默认管理员用户
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
            username='admin',
            role='admin',
            name='管理员',
            student_id='0000000000',
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


    # 注册蓝图
    from routes.auth import auth_bp
    from routes.file import file_bp
    from routes.flag import flag_bp
    from routes.training import training_bp
    from routes.event import event_bp
    from routes.dashboard import dashboard_bp
    from routes.records import records_bp
    from routes.users import users_bp
    from routes.points import bp as points_bp
    from routes.trainings import bp as trainings_bp
    from routes.events import bp as events_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(file_bp, url_prefix='/api')
    app.register_blueprint(flag_bp, url_prefix='/api')
    app.register_blueprint(training_bp, url_prefix='/api')
    app.register_blueprint(event_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(records_bp, url_prefix='/api')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(points_bp, url_prefix='/api/points')
    app.register_blueprint(trainings_bp, url_prefix='/api/trainings')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    
    # 配置静态文件服务
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # 添加静态文件服务
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        except Exception as e:
            app.logger.error(f"Error serving file {filename}: {str(e)}")
            return jsonify({'error': 'File not found'}), 404
    
    # 确保上传目录存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        app.logger.info(f"Created upload directory: {app.config['UPLOAD_FOLDER']}")
    
    # 注册CLI命令
    app.cli.add_command(init_db)
    app.cli.add_command(drop_db)
    app.cli.add_command(create_admin)
    app.cli.add_command(list_users)
    app.cli.add_command(cleanup_records)
    app.cli.add_command(backup_db)
    app.cli.add_command(check_system)
    app.cli.add_command(reset_password)
    app.cli.add_command(export_data)
    
    # 错误处理
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
    
    # 初始化数据库
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
            username='admin',
            role='admin',
            name='管理员',
            student_id='0000000000',
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

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)