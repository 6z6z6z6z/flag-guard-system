from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models_pymysql import User, PointHistory
from db_connection import db
from utils.route_utils import (
    APIResponse, validate_required_fields, validate_student_id,
    validate_phone_number, handle_exceptions, validate_json_request,
    role_required
)

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
@handle_exceptions
def get_user_profile():
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
    
    user = User.get_by_id(int(user_id))
    if not user:
        return APIResponse.error("User not found", 404)
    
    user_data = {
        "username": user['username'],
        "name": user['name'],
        "student_id": user['student_id'],
        "college": user['college'],
        "height": user['height'],
        "weight": user['weight'],
        "shoe_size": user['shoe_size'],
        "total_points": user['total_points'],
        "role": user['role'],
        "phone_number": user['phone_number']
    }
    
    current_app.logger.info(f"Successfully retrieved profile for user: {user['username']}")
    return APIResponse.success(data=user_data)

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
@validate_json_request
@handle_exceptions
def update_user_profile():
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
    user = User.get_by_id(int(user_id))
    
    if not user:
        return APIResponse.error("User not found", 404)
    
    data = request.get_json()
    
    # 只允许更新特定字段
    height = user['height']
    weight = user['weight']
    shoe_size = user['shoe_size']
    
    if 'height' in data:
        height = data['height']
    if 'weight' in data:
        weight = data['weight']
    if 'shoe_size' in data:
        shoe_size = data['shoe_size']
    
    # 更新用户信息
    updated_user = User.update(
        user_id=int(user_id),
        name=user['name'],
        college=user['college'],
        role=user['role'],
        phone_number=user['phone_number'],
        height=height,
        weight=weight,
        shoe_size=shoe_size
    )
    
    return APIResponse.success(data={
        "height": updated_user['height'],
        "weight": updated_user['weight'],
        "shoe_size": updated_user['shoe_size']
    })

@users_bp.route('/points/history', methods=['GET'])
@jwt_required()
@handle_exceptions
def get_user_points_history():
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
    user = User.get_by_id(int(user_id))
    
    if not user:
        return APIResponse.error("User not found", 404)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取所有积分历史记录
    all_history = PointHistory.list_by_user(int(user_id))
    
    # 手动分页
    total = len(all_history)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    # 获取当前页的记录
    current_page_items = all_history[start_idx:end_idx] if start_idx < total else []
    
    return APIResponse.success(data={
        "items": current_page_items,
        "total": total,
        "pages": total_pages,
        "current_page": page
    })

@users_bp.route('/search', methods=['GET'])
@jwt_required()
@handle_exceptions
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
    
    # 搜索用户名、姓名或学号包含关键词的用户
    users = User.search(query)
    
    return APIResponse.success(data=users)

@users_bp.route('/points/all', methods=['GET'])
@jwt_required()
@role_required('superadmin', 'admin')
@handle_exceptions
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
      - name: sort
        in: query
        type: string
        default: points_desc
        description: 排序方式，可选值：points_desc, points_asc, name_asc, name_desc
    responses:
      200:
        description: 成功获取用户积分列表
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort', 'points_desc')
    
    # 获取所有用户
    all_users = User.list_all()
    
    # 根据排序参数对用户进行排序
    if sort_by == 'points_desc':
        all_users.sort(key=lambda u: float(u['total_points'] or 0), reverse=True)
    elif sort_by == 'points_asc':
        all_users.sort(key=lambda u: float(u['total_points'] or 0))
    elif sort_by == 'name_asc':
        all_users.sort(key=lambda u: u['name'])
    elif sort_by == 'name_desc':
        all_users.sort(key=lambda u: u['name'], reverse=True)
    
    # 手动分页
    total = len(all_users)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    # 获取当前页的用户
    current_page_users = all_users[start_idx:end_idx] if start_idx < total else []
    
    # 提取需要的字段，确保包含手机号
    result_users = []
    for user in current_page_users:
        result_users.append({
            'user_id': user['user_id'],
            'username': user['username'],
            'name': user['name'],
            'student_id': user['student_id'],
            'college': user['college'],
            'total_points': user['total_points'],
            'role': user['role'],
            'phone_number': user['phone_number']
        })
    
    return APIResponse.success(data={
        'items': result_users,
        'total': total,
        'pages': total_pages,
        'current_page': page
    })

@users_bp.route('', methods=['GET'])
@jwt_required()
@role_required('superadmin', 'admin')
@handle_exceptions
def get_users():
    """
    获取所有用户（仅管理员）
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
        description: 搜索关键词
    responses:
      200:
        description: 成功获取用户列表
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    query = request.args.get('query', '')
    
    # 根据查询条件获取用户
    all_users = User.search(query) if query else User.list_all()
    
    # 手动分页
    total = len(all_users)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    # 获取当前页的用户
    current_page_users = all_users[start_idx:end_idx] if start_idx < total else []
    
    return APIResponse.success(data={
        'items': current_page_users,
        'total': total,
        'pages': total_pages,
        'current_page': page
    })

@users_bp.route('', methods=['POST'])
@jwt_required()
@role_required('superadmin')
@validate_json_request
@handle_exceptions
def create_user():
    """
    创建用户（仅超级管理员）
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
              enum: [member, admin]
            phone_number:
              type: string
    responses:
      201:
        description: 创建成功
      400:
        description: 参数错误
    """
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['username', 'password', 'name', 'student_id', 'college', 'role']
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
    
    # 创建用户
    user = User.create(
        username=data['username'],
        password=data['password'],
        role=data['role'],
        name=data['name'],
        student_id=data['student_id'],
        college=data['college'],
        phone_number=data.get('phone_number')
    )
    
    if not user:
        return APIResponse.error("Failed to create user", 500)
    
    return APIResponse.success(data=User.to_dict(user), msg="User created successfully", code=201)

@users_bp.route('/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@role_required('superadmin')
@validate_json_request
@handle_exceptions
def update_user_role(user_id):
    """
    更新用户角色（仅超级管理员）
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            role:
              type: string
              enum: [member, admin, superadmin]
    responses:
      200:
        description: 更新成功
      400:
        description: 参数错误
      404:
        description: 用户不存在
    """
    data = request.get_json()
    
    # 验证角色参数
    if 'role' not in data or data['role'] not in ['member', 'admin', 'superadmin']:
        return APIResponse.error("Invalid role", 400)
    
    # 获取用户
    user = User.get_by_id(user_id)
    if not user:
        return APIResponse.error("User not found", 404)
    
    # 更新用户角色
    updated_user = User.update(
        user_id=user_id,
        name=user['name'],
        college=user['college'],
        role=data['role'],
        phone_number=user['phone_number'],
        height=user['height'],
        weight=user['weight'],
        shoe_size=user['shoe_size']
    )
    
    if not updated_user:
        return APIResponse.error("Failed to update user role", 500)
    
    return APIResponse.success(data={"role": updated_user['role']})

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
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
        required: true
        type: integer
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
      404:
        description: 用户不存在
    """
    data = request.get_json()
    
    # 获取用户
    user = User.get_by_id(user_id)
    if not user:
        return APIResponse.error("User not found", 404)
    
    # 验证手机号格式
    if data.get('phone_number'):
        is_valid, error_msg = validate_phone_number(data['phone_number'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
    
    # 更新字段
    name = data.get('name', user['name'])
    college = data.get('college', user['college'])
    phone_number = data.get('phone_number', user['phone_number'])
    
    # 更新用户
    updated_user = User.update(
        user_id=user_id,
        name=name,
        college=college,
        role=user['role'],
        phone_number=phone_number,
        height=user['height'],
        weight=user['weight'],
        shoe_size=user['shoe_size']
    )
    
    if not updated_user:
        return APIResponse.error("Failed to update user", 500)
    
    return APIResponse.success(data=User.to_dict(updated_user)) 