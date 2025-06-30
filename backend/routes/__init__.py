from flask import Flask
from routes.auth import auth_bp
from routes.users import users_bp
from routes.trainings import bp as trainings_bp
from routes.events import bp as events_bp
from routes.points import bp as points_bp
from routes.flag import bp as flag_bp
from routes.dashboard import dashboard_bp
from routes.file import file_bp

def register_blueprints(app: Flask):
    # 注册所有蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(trainings_bp, url_prefix='/api/trainings')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(points_bp, url_prefix='/api/points')
    app.register_blueprint(flag_bp, url_prefix='/api/flag')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(file_bp, url_prefix='/api/files')
    
    # 注册错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'code': 404, 'msg': '请求的资源不存在'}, 404
        
    @app.errorhandler(500)
    def internal_error(error):
        return {'code': 500, 'msg': '服务器内部错误'}, 500
        
    @app.errorhandler(403)
    def forbidden(error):
        return {'code': 403, 'msg': '没有权限访问该资源'}, 403
        
    @app.errorhandler(401)
    def unauthorized(error):
        return {'code': 401, 'msg': '未登录或登录已过期'}, 401 