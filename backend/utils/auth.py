from functools import wraps
from flask import jsonify, g, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError
from models_pymysql import User

def login_required(fn):
    """验证用户是否登录的装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # 记录调试信息
            current_app.logger.debug(f"Authenticating user_id: {user_id}")
            
            user = User.get_by_id(int(user_id))
            if not user:
                current_app.logger.warning(f"User not found for user_id: {user_id}")
                return jsonify({'error': '用户不存在'}), 401
                
            g.user = user
            return fn(*args, **kwargs)
            
        except NoAuthorizationError:
            current_app.logger.warning("No authorization header found")
            return jsonify({'error': '请先登录'}), 401
            
        except InvalidHeaderError as e:
            current_app.logger.warning(f"Invalid authorization header: {str(e)}")
            return jsonify({'error': '无效的认证信息'}), 401
            
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': '认证失败'}), 401
            
    return wrapper

def admin_required(fn):
    """验证用户是否为管理员的装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # 记录调试信息
            current_app.logger.debug(f"Authenticating admin user_id: {user_id}")
            
            user = User.get_by_id(int(user_id))
            if not user:
                current_app.logger.warning(f"User not found for user_id: {user_id}")
                return jsonify({'error': '用户不存在'}), 401
                
            if not User.is_admin(user):
                current_app.logger.warning(f"Non-admin user attempted admin action: {user_id}")
                return jsonify({'error': '权限不足'}), 403
                
            g.user = user
            return fn(*args, **kwargs)
            
        except NoAuthorizationError:
            current_app.logger.warning("No authorization header found")
            return jsonify({'error': '请先登录'}), 401
            
        except InvalidHeaderError as e:
            current_app.logger.warning(f"Invalid authorization header: {str(e)}")
            return jsonify({'error': '无效的认证信息'}), 401
            
        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': '认证失败'}), 401
            
    return wrapper 