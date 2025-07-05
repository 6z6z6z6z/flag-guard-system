from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models_pymysql import User
from utils.route_utils import (
    APIResponse, validate_required_fields, validate_student_id,
    validate_phone_number, handle_exceptions, validate_json_request
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@validate_json_request
@handle_exceptions
def register():
    """
    用户注册
    ---
    tags:
      - 认证
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
            name:
              type: string
            student_id:
              type: string
            college:
              type: string
            role:
              type: string
              enum: [admin, member]
              default: member
            phone_number:
              type: string
              pattern: "^\\d{10,15}$"
    responses:
      201:
        description: 注册成功
      400:
        description: 用户名已存在
    """
    data = request.get_json()
    current_app.logger.info(f"Registration attempt received: {data.get('username')}")
    
    # 验证必填字段
    required_fields = ['username', 'password', 'name', 'student_id', 'college']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    # 验证学号格式
    is_valid, error_msg = validate_student_id(data['student_id'])
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    # 验证手机号格式
    if data.get('phone_number'):
        is_valid, error_msg = validate_phone_number(data['phone_number'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
    
    # 检查用户名是否已存在
    if User.get_by_username(data['username']):
        return APIResponse.error("Username already exists", 400)
    
    # 检查学号是否已存在
    if User.get_by_student_id(data['student_id']):
        return APIResponse.error("Student ID already exists", 400)
    
    try:
        # 检查是否是第一个用户
        all_users = User.list_all()
        is_first_user = len(all_users) == 0
        
        user_role = 'superadmin' if is_first_user else 'member'

        user = User.create(
            username=data['username'],
            password=data['password'],
            role=user_role,
            name=data['name'],
            student_id=data['student_id'],
            college=data['college'],
            phone_number=data.get('phone_number')
        )
        
        if not user:
            return APIResponse.error("Failed to create user", 500)
        
        current_app.logger.info(f"User {user['username']} registered successfully")
        
        # 直接返回成功信息，不生成 token
        return APIResponse.success(msg="User created successfully", code=201)
        
    except Exception as db_error:
        current_app.logger.error(f"Database error during registration: {str(db_error)}")
        return APIResponse.error(str(db_error), 500)

@auth_bp.route('/login', methods=['POST'])
@validate_json_request
@handle_exceptions
def login():
    """
    用户登录
    ---
    tags:
      - 认证
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: 登录成功
      401:
        description: 用户名或密码错误
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    current_app.logger.info(f"Login attempt received for username: {username}")
    
    # 验证必填字段
    if not username or not password:
        current_app.logger.warning("Login attempt failed: Missing username or password")
        return APIResponse.error("Username and password are required", 400)
    
    # 查找用户
    user = User.get_by_username(username)
    if not user:
        current_app.logger.warning(f"Login attempt failed: User not found - {username}")
        return APIResponse.error("Invalid username or password", 401)
    
    # 验证密码
    if not User.check_password(user, password):
        current_app.logger.warning(f"Login attempt failed: Invalid password for user - {username}")
        return APIResponse.error("Invalid username or password", 401)
    
    try:
        # 生成 token，确保 user_id 是字符串
        access_token = create_access_token(identity=str(user['user_id']))
        current_app.logger.info(f"User {username} logged in successfully")
        
        return APIResponse.success(
            data={
                "token": f"Bearer {access_token}",
                "user": {
                    "id": user['user_id'],
                    "username": user['username'],
                    "name": user['name'],
                    "role": user['role']
                }
            },
            msg="Login successful",
            code=200
        )
    except Exception as e:
        current_app.logger.error(f"Token creation error for user {username}: {str(e)}")
        return APIResponse.error("Error creating access token", 500)

@auth_bp.route('/info', methods=['GET'])
@jwt_required()
def get_user_info():
    """
    获取当前登录用户信息
    ---
    tags:
      - 认证
    security:
      - Bearer: []
    responses:
      200:
        description: 成功获取用户信息
      404:
        description: 用户不存在
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.error('Invalid token', 401)
            
        user = User.get_by_id(int(user_id))
        if not user:
            return APIResponse.error('用户不存在', 404)
            
        # 返回所有关键信息
        user_data = {
            'id': user['user_id'],
            'username': user['username'],
            'name': user['name'],
            'role': user['role'],
            'college': user['college'],
            'student_id': user['student_id'],
            'phone_number': user['phone_number'],
            'total_points': user['total_points'],
            'height': user['height'],
            'weight': user['weight'],
            'shoe_size': user['shoe_size']
        }
        return APIResponse.success(data=user_data)
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {str(e)}")
        return APIResponse.error('获取用户信息失败', 500)

@auth_bp.route('/check', methods=['GET'])
@jwt_required()
def check_token():
    """
    检查token是否有效
    """
    return APIResponse.success(msg="Token is valid")