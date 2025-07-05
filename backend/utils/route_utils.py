from functools import wraps
from flask import jsonify, current_app, request
from flask_jwt_extended import get_jwt_identity
from models_pymysql import User
import logging

logger = logging.getLogger(__name__)

class APIResponse:
    """API响应处理类"""
    @staticmethod
    def success(data=None, msg="success", code=200):
        """成功响应"""
        try:
            response = {
                "msg": msg,
                "code": code
            }
            if data is not None:
                # 确保数据可以被JSON序列化
                if isinstance(data, dict):
                    # 处理字典中的浮点数
                    for key, value in data.items():
                        if isinstance(value, float):
                            data[key] = float(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and 'points_change' in item:
                                    item['points_change'] = float(item['points_change'])
                response["data"] = data
            logger.info(f"API Response: {response}")
            return jsonify(response), code
        except Exception as e:
            logger.error(f"Error in APIResponse.success: {str(e)}", exc_info=True)
            return jsonify({
                "msg": "Internal server error",
                "code": 500
            }), 500

    @staticmethod
    def error(msg="error", code=400, data=None):
        """错误响应"""
        try:
            response = {
                "msg": msg,
                "code": code
            }
            if data is not None:
                response["data"] = data
            logger.error(f"API Error Response: {response}")
            return jsonify(response), code
        except Exception as e:
            logger.error(f"Error in APIResponse.error: {str(e)}", exc_info=True)
            return jsonify({
                "msg": "Internal server error",
                "code": 500
            }), 500

def validate_required_fields(data, required_fields):
    """验证必填字段"""
    if not data:
        return False, "No input data provided"
    
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None

def validate_student_id(student_id):
    """验证学号格式"""
    if not User.validate_student_id(student_id):
        return False, "Invalid student ID format. It must be 2 uppercase letters followed by 8 digits."
    return True, None

def validate_phone_number(phone_number):
    """验证手机号格式"""
    if phone_number and not phone_number.isdigit():
        return False, "Invalid phone number format"
    return True, None

def role_required(*roles):
    """角色权限检查装饰器，允许多个角色"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_app.logger.info("=== Role Check Start ===")
            current_app.logger.info(f"Required roles: {roles}")
            
            try:
                # 获取当前用户ID
                user_id = get_jwt_identity()
                current_app.logger.info(f"JWT Identity (user_id): {user_id}")
                
                if not user_id:
                    current_app.logger.warning("No user_id found in JWT token")
                    return jsonify({
                        'message': 'Missing token',
                        'code': 401
                    }), 401
                
                # 查找用户
                user = User.get_by_id(int(user_id))
                current_app.logger.info(f"User found: {user['username'] if user else 'None'}")
                
                if not user:
                    current_app.logger.warning(f"User not found for ID: {user_id}")
                    return jsonify({
                        'message': 'User not found',
                        'code': 401
                    }), 401
                
                # 检查用户角色
                current_app.logger.info(f"User role: {user['role']}, Required roles: {roles}")
                if user['role'] not in roles:
                    current_app.logger.warning(f"Permission denied: User role '{user['role']}' not in required roles {roles}")
                    return jsonify({
                        'message': 'Permission denied',
                        'code': 403
                    }), 403
                
                current_app.logger.info("=== Role Check Passed ===")
                return fn(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error in role_required decorator: {str(e)}")
                current_app.logger.error(f"Error type: {type(e)}")
                current_app.logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
                return jsonify({
                    'message': 'Internal server error',
                    'code': 500
                }), 500
                
        return wrapper
    return decorator

def handle_exceptions(f):
    """异常处理装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return APIResponse.error("Internal server error", 500)
    return wrapper

def validate_json_request(f):
    """JSON请求验证装饰器"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        current_app.logger.info("=== JSON Request Validation ===")
        current_app.logger.info(f"Request Content-Type: {request.headers.get('Content-Type')}")
        current_app.logger.info(f"Request headers: {dict(request.headers)}")
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request path: {request.path}")
        
        if not request.is_json:
            current_app.logger.warning("Invalid Content-Type: Request is not JSON")
            return APIResponse.error("Content-Type must be application/json", 400)
            
        try:
            data = request.get_json()
            current_app.logger.info(f"Request data: {data}")
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error parsing JSON: {str(e)}")
            return APIResponse.error("Invalid JSON data", 400)
    return wrapper 