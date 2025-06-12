from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User
from extensions import db, jwt
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
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
    responses:
      201:
        description: 注册成功
      400:
        description: 用户名已存在
    """
    try:
        data = request.get_json()
        current_app.logger.info(f"Registration attempt received: {data.get('username')}")
        
        if not data:
            current_app.logger.warning("Registration attempt with no data")
            return jsonify({"msg": "No input data provided"}), 400
            
        # 验证必填字段
        required_fields = ['username', 'password', 'name', 'student_id', 'college']
        for field in required_fields:
            if not data.get(field):
                current_app.logger.warning(f"Registration attempt missing required field: {field}")
                return jsonify({"msg": f"Missing required field: {field}"}), 400
            
        # 验证学号格式
        if not User.validate_student_id(data['student_id']):
            current_app.logger.warning(f"Registration attempt with invalid student ID format: {data['student_id']}")
            return jsonify({"msg": "Invalid student ID format. It must be 2 uppercase letters followed by 8 digits."}), 400
            
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            current_app.logger.warning(f"Registration attempt failed: Username {data['username']} already exists")
            return jsonify({"msg": "Username already exists"}), 400
            
        # 检查学号是否已存在
        if User.query.filter_by(student_id=data['student_id']).first():
            current_app.logger.warning(f"Registration attempt failed: Student ID {data['student_id']} already exists")
            return jsonify({"msg": "Student ID already exists"}), 400
        
        try:
            user = User(
                username=data['username'],
                name=data['name'],
                student_id=data['student_id'],
                college=data['college'],
                role=data.get('role', 'member')  # 如果未指定角色，默认为队员
            )
            if not user.set_password(data['password']):
                raise Exception("Failed to set password")
                
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"User {user.username} registered successfully")
            
            return jsonify({"msg": "User created successfully"}), 201
            
        except Exception as db_error:
            current_app.logger.error(f"Database error during registration: {str(db_error)}")
            db.session.rollback()
            return jsonify({"msg": "Error creating user"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({"msg": "Internal server error"}), 500

@auth_bp.route('/login', methods=['POST'])
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
        description: 认证失败
    """
    try:
        current_app.logger.info("Login attempt received")
        data = request.get_json()
        
        if not data:
            current_app.logger.warning("Login attempt with no data")
            return jsonify({"msg": "No input data provided"}), 400
            
        current_app.logger.debug(f"Login attempt for username: {data.get('username')}")
        
        if not data.get('username') or not data.get('password'):
            current_app.logger.warning("Login attempt with missing credentials")
            return jsonify({"msg": "Missing username or password"}), 400
            
        user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            current_app.logger.warning(f"Login attempt failed: User {data['username']} not found")
            return jsonify({"msg": "Invalid username or password"}), 401
            
        # 记录密码验证结果
        password_check = user.check_password(data['password'])
        current_app.logger.debug(f"Password check result for user {data['username']}: {password_check}")
            
        if not password_check:
            current_app.logger.warning(f"Login attempt failed: Invalid password for user {data['username']}")
            return jsonify({"msg": "Invalid username or password"}), 401
        
        try:
            # Use user ID as token identity
            access_token = create_access_token(identity=str(user.user_id))
            current_app.logger.info(f"User {user.username} logged in successfully")
            
            response_data = {
                "msg": "success",
                "data": {
                    "token": f"Bearer {access_token}",
                    "user": {
                        "id": user.user_id,
                        "username": user.username,
                        "name": user.name,
                        "role": user.role,
                        "college": user.college,
                        "student_id": user.student_id,
                        "total_points": user.total_points
                    }
                }
            }
            current_app.logger.debug(f"Login response data: {response_data}")
            return jsonify(response_data), 200
        except Exception as token_error:
            current_app.logger.error(f"Token creation error: {str(token_error)}")
            return jsonify({"msg": "Error creating access token"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({"msg": "Internal server error"}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    获取用户个人信息
    ---
    tags:
      - 认证
    security:
      - Bearer: []
    responses:
      200:
        description: 成功获取个人信息
      401:
        description: 未认证
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"msg": "User not found"}), 404
            
        return jsonify({
            'username': user.username,
            'name': user.name,
            'role': user.role,
            'college': user.college,
            'total_points': user.total_points
        }), 200
    except Exception as e:
        current_app.logger.error(f"Profile error: {str(e)}")
        return jsonify({"msg": "Internal server error"}), 500

def role_required(role):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def wrapper(*args, **kwargs):
            try:
                current_user = User.query.get(get_jwt_identity())
                if not current_user:
                    return jsonify({"msg": "User not found"}), 404
                    
                if current_user.role != role:
                    return jsonify({"msg": "Insufficient permissions"}), 403
                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.error(f"Role check error: {str(e)}")
                return jsonify({"msg": "Internal server error"}), 500
        return wrapper
    return decorator