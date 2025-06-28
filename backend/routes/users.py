from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, PointHistory
from extensions import db
from sqlalchemy import or_, func
from utils.route_utils import (
    APIResponse, validate_required_fields, validate_student_id,
    validate_phone_number, handle_exceptions, validate_json_request,
    log_operation, role_required
)

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
@handle_exceptions
@log_operation('get_profile')
def get_profile():
    """
    获取用户个人信息
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    responses:
      200:
        description: 成功获取个人信息
      404:
        description: 用户不存在
    """
    user_id = get_jwt_identity()
    current_app.logger.info(f"Getting profile for user_id: {user_id}")
    
    user = User.query.get(user_id)
    if not user:
        return APIResponse.error("User not found", 404)
    
    user_data = {
        "username": user.username,
        "name": user.name,
        "student_id": user.student_id,
        "college": user.college,
        "height": user.height,
        "weight": user.weight,
        "shoe_size": user.shoe_size,
        "total_points": user.total_points,
        "role": user.role,
        "phone_number": user.phone_number
    }
    
    current_app.logger.info(f"Successfully retrieved profile for user: {user.username}")
    return APIResponse.success(data=user_data)

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
@validate_json_request
@handle_exceptions
@log_operation('update_profile')
def update_profile():
    """
    更新用户个人信息
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            height:
              type: integer
            weight:
              type: number
            shoe_size:
              type: integer
    responses:
      200:
        description: 更新成功
      400:
        description: 参数错误
      404:
        description: 用户不存在
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return APIResponse.error("User not found", 404)
    
    data = request.get_json()
    
    # 只允许更新特定字段
    allowed_fields = {'height', 'weight', 'shoe_size'}
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    db.session.commit()
    return APIResponse.success(data={
        "height": user.height,
        "weight": user.weight,
        "shoe_size": user.shoe_size
    })

@users_bp.route('/points/history', methods=['GET'])
@jwt_required()
@handle_exceptions
@log_operation('get_points_history')
def get_points_history():
    """
    获取用户积分历史
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
    responses:
      200:
        description: 成功获取积分历史
      404:
        description: 用户不存在
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return APIResponse.error("User not found", 404)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取分页的积分历史记录
    pagination = PointHistory.query.filter_by(user_id=user_id)\
        .order_by(PointHistory.change_time.desc())\
        .paginate(page=page, per_page=per_page)
    
    return APIResponse.success(data={
        "items": [item.to_dict() for item in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    })

@users_bp.route('/search', methods=['GET'])
@jwt_required()
@handle_exceptions
@log_operation('search_users')
def search_users():
    """
    搜索用户
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: query
        in: query
        type: string
        required: true
        description: 搜索关键词（用户名、姓名或学号）
    responses:
      200:
        description: 成功获取用户列表
    """
    query = request.args.get('query', '')
    if not query:
        return APIResponse.success(data=[])
        
    search_term = f'%{query.lower()}%'
    
    # 搜索用户名、姓名或学号包含关键词的用户
    users = User.query.filter(
        or_(
            func.lower(User.username).like(search_term),
            func.lower(User.name).like(search_term),
            func.lower(User.student_id).like(search_term)
        )
    ).limit(10).all()
    
    return APIResponse.success(data=[user.to_dict() for user in users])

@users_bp.route('/points/all', methods=['GET'])
@jwt_required()
@role_required('superadmin', 'admin')
@handle_exceptions
@log_operation('get_all_users_points')
def get_all_users_points():
    """
    获取所有用户的积分（仅管理员）
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
      - name: query
        in: query
        type: string
        description: 搜索关键词（用户名、姓名或学号）
    responses:
      200:
        description: 成功获取用户积分列表
      403:
        description: 权限不足
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = request.args.get('query', '')
    
    # 构建查询
    user_query = User.query
    if query:
        user_query = user_query.filter(
            (User.username.ilike(f'%{query}%')) |
            (User.name.ilike(f'%{query}%')) |
            (User.student_id.ilike(f'%{query}%'))
        )
    
    # 分页查询
    pagination = user_query.order_by(User.total_points.desc())\
        .paginate(page=page, per_page=per_page)
    
    return APIResponse.success(data={
        "items": [user.to_dict() for user in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    })

@users_bp.route('', methods=['POST'])
@jwt_required()
@role_required('superadmin')
@validate_json_request
@handle_exceptions
@log_operation('create_user')
def create_user():
    """
    创建新用户（仅管理员）
    ---
    tags:
      - 用户
    security:
      - Bearer: []
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
            phone_number:
              type: string
    responses:
      201:
        description: 用户创建成功
      400:
        description: 参数错误
      403:
        description: 权限不足
    """
    data = request.get_json()
    
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
    
    # 检查角色是否有效
    role = data.get('role', 'member')
    if role not in ['admin', 'member']:
        return APIResponse.error(f"Invalid role: {role}", 400)
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return APIResponse.error("Username already exists", 400)
    
    # 检查学号是否已存在
    if User.query.filter_by(student_id=data['student_id']).first():
        return APIResponse.error("Student ID already exists", 400)
    
    try:
        user = User(
            username=data['username'],
            name=data['name'],
            student_id=data['student_id'],
            college=data['college'],
            role=data.get('role', 'member'),
            phone_number=data.get('phone_number')
        )
        if not user.set_password(data['password']):
            return APIResponse.error("Failed to set password", 500)
        
        db.session.add(user)
        db.session.commit()
        
        return APIResponse.success(
            data=user.to_dict(),
            msg="User created successfully",
            code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating user: {str(e)}")
        return APIResponse.error("Error creating user", 500)

@users_bp.route('/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@role_required('superadmin')
@validate_json_request
@handle_exceptions
@log_operation('update_user_role')
def update_user_role(user_id):
    """
    更新用户角色（仅管理员）
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            role:
              type: string
              enum: [admin, member]
    responses:
      200:
        description: 角色更新成功
      400:
        description: 参数错误
      403:
        description: 权限不足
      404:
        description: 用户不存在
    """
    data = request.get_json()
    
    if 'role' not in data:
        return APIResponse.error("Role is required", 400)
    
    if data['role'] not in ['admin', 'member']:
        return APIResponse.error("Invalid role", 400)
    
    user = User.query.get(user_id)
    if not user:
        return APIResponse.error("User not found", 404)
    
    new_role = data.get('role')
    if not new_role or new_role not in ['admin', 'member']:
        return APIResponse.error("Invalid or missing role. Can only set to 'admin' or 'member'.", 400)
    
    # 防止最后一个超级管理员将自己降级
    if user.user_id == get_jwt_identity() and user.role == 'superadmin' and new_role != 'superadmin':
        return APIResponse.error("Superadmin cannot demote themselves.", 400)

    try:
        user.role = new_role
        db.session.commit()
        return APIResponse.success(data=user.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user role: {str(e)}")
        return APIResponse.error("Error updating user role", 500)

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
@log_operation('update_user')
def update_user(user_id):
    """
    更新用户信息（仅管理员）
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            college:
              type: string
            phone_number:
              type: string
    responses:
      200:
        description: 更新成功
      400:
        description: 参数错误
      403:
        description: 权限不足
      404:
        description: 用户不存在
    """
    data = request.get_json()
    user = User.query.get(user_id)
    
    if not user:
        return APIResponse.error("User not found", 404)

    # 如果有角色变更，则拒绝，因为此端点不能用于更改角色
    if 'role' in data and data['role'] != user.role:
        return APIResponse.error("Cannot change role via this endpoint. Use the dedicated /role endpoint.", 403)
        
    # 更新允许的字段
    allowed_fields = ['username', 'name', 'student_id', 'college', 'phone_number']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    db.session.commit()
    return APIResponse.success(data=user.to_dict()) 