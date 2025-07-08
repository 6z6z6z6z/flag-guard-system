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
    
    # 确保返回的用户信息格式一致
    result_users = []
    for user in users:
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
    
    return APIResponse.success(data=result_users)

@users_bp.route('/by_id', methods=['GET'])
@jwt_required()
@handle_exceptions
def get_user_by_id():
    """
    根据用户ID获取用户
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: query
        type: integer
        required: true
        description: 用户ID
    responses:
      200:
        description: 成功获取用户
      404:
        description: 用户不存在
    """
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return APIResponse.error("用户ID不能为空", 400)
    
    user = User.get_by_id(user_id)
    if not user:
        return APIResponse.error("用户不存在", 404)
    
    return APIResponse.success(data=User.to_dict(user))

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
      - name: query
        in: query
        type: string
        description: 搜索关键词（用户名、姓名或学号）
    responses:
      200:
        description: 成功获取用户积分列表
    """
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort', 'points_desc')
    search_query = request.args.get('query', '')
    
    # 根据搜索条件获取用户
    all_users = User.search(search_query) if search_query else User.list_all()
    
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

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('superadmin')
@handle_exceptions
def delete_user_endpoint(user_id):
    """
    删除用户（仅超级管理员）
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
    responses:
      200:
        description: 删除成功
      403:
        description: 权限不足
      404:
        description: 用户不存在
      500:
        description: 服务器错误
    """
    # 获取当前用户身份
    current_user_id = get_jwt_identity()
    
    # 不允许删除自己
    if int(current_user_id) == user_id:
        return APIResponse.error("不能删除自己的账号", 403)
    
    # 获取用户
    user = User.get_by_id(user_id)
    if not user:
        return APIResponse.error("用户不存在", 404)
    
    # 不允许删除超级管理员
    if user['role'] == 'superadmin':
        return APIResponse.error("不能删除超级管理员账号", 403)
    
    try:
        # 直接执行SQL删除相关记录
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 删除用户的积分历史记录
            cursor.execute("DELETE FROM point_history WHERE user_id = %s", (user_id,))
            point_history_count = cursor.rowcount
            
            # 2. 删除用户的训练报名记录
            cursor.execute("DELETE FROM training_registrations WHERE user_id = %s", (user_id,))
            training_reg_count = cursor.rowcount
            
            # 3. 删除用户的活动报名记录
            cursor.execute("DELETE FROM event_registrations WHERE user_id = %s", (user_id,))
            event_reg_count = cursor.rowcount
            
            # 4. 删除用户的升降旗记录
            cursor.execute("DELETE FROM flag_records WHERE user_id = %s", (user_id,))
            flag_records_count = cursor.rowcount
            
            # 5. 最后删除用户本身
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            user_count = cursor.rowcount
            
            # 提交事务
            conn.commit()
            
            # 记录删除结果
            current_app.logger.info(f"User {user['username']} (ID: {user_id}) deleted successfully")
            current_app.logger.info(f"Deleted: {point_history_count} point history records, "
                                   f"{training_reg_count} training registrations, "
                                   f"{event_reg_count} event registrations, "
                                   f"{flag_records_count} flag records")
            
            return APIResponse.success(msg="用户删除成功")
            
        except Exception as e:
            # 回滚事务
            conn.rollback()
            current_app.logger.error(f"Error during user deletion: {str(e)}")
            return APIResponse.error(f"删除用户失败: {str(e)}", 500)
        finally:
            cursor.close()
            
    except Exception as e:
        current_app.logger.error(f"Failed to connect to database: {str(e)}")
        return APIResponse.error("数据库连接失败", 500)

# 添加新的用户删除路由，直接使用原生SQL实现
@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@jwt_required()
@role_required('superadmin')
@handle_exceptions
def direct_delete_user(user_id):
    """
    删除用户（仅超级管理员）- 替代路由
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
    responses:
      200:
        description: 删除成功
      403:
        description: 权限不足
      404:
        description: 用户不存在
      500:
        description: 服务器错误
    """
    # 获取当前用户身份
    current_user_id = get_jwt_identity()
    
    current_app.logger.info(f"尝试删除用户 ID: {user_id}, 操作者 ID: {current_user_id}")
    
    # 不允许删除自己
    if int(current_user_id) == user_id:
        return APIResponse.error("不能删除自己的账号", 403)
    
    # 获取用户
    user = User.get_by_id(user_id)
    if not user:
        return APIResponse.error("用户不存在", 404)
    
    # 不允许删除超级管理员
    if user['role'] == 'superadmin':
        return APIResponse.error("不能删除超级管理员账号", 403)
    
    conn = None
    cursor = None
    try:
        # 获取数据库连接和游标
        conn = db.connect()
        cursor = conn.cursor()
        
        # 开始删除用户相关数据
        # 1. 删除用户的积分历史记录
        cursor.execute("DELETE FROM point_history WHERE user_id = %s", (user_id,))
        point_history_count = cursor.rowcount
        current_app.logger.info(f"已删除 {point_history_count} 条积分历史记录")
        
        # 2. 删除用户的训练报名记录
        cursor.execute("DELETE FROM training_registrations WHERE user_id = %s", (user_id,))
        training_reg_count = cursor.rowcount
        current_app.logger.info(f"已删除 {training_reg_count} 条训练报名记录")
        
        # 3. 删除用户的活动报名记录
        cursor.execute("DELETE FROM event_registrations WHERE user_id = %s", (user_id,))
        event_reg_count = cursor.rowcount
        current_app.logger.info(f"已删除 {event_reg_count} 条活动报名记录")
        
        # 4. 删除用户的升降旗记录
        cursor.execute("DELETE FROM flag_records WHERE user_id = %s", (user_id,))
        flag_records_count = cursor.rowcount
        current_app.logger.info(f"已删除 {flag_records_count} 条升降旗记录")
        
        # 5. 最后删除用户本身
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        user_count = cursor.rowcount
        
        if user_count == 0:
            current_app.logger.error(f"用户 {user_id} 在最终删除阶段未找到")
            conn.rollback()
            return APIResponse.error("用户不存在或已被删除", 404)
        
        # 提交事务
        conn.commit()
        
        current_app.logger.info(f"成功删除用户 {user['username']} (ID: {user_id})")
        
        # 返回成功响应
        return APIResponse.success(msg="用户删除成功")
        
    except Exception as e:
        # 发生错误，回滚事务
        if conn:
            conn.rollback()
        current_app.logger.error(f"删除用户时发生错误: {str(e)}")
        return APIResponse.error(f"删除用户失败: {str(e)}", 500)
    
    finally:
        # 关闭游标
        if cursor:
            cursor.close()

# 添加最简单的用户删除路由
@users_bp.route('/delete_user', methods=['POST'])
@jwt_required()
@role_required('superadmin')
@handle_exceptions
def simple_delete_user():
    """
    删除用户（仅超级管理员）- 最简单的实现
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
            user_id:
              type: integer
              description: 要删除的用户ID
    responses:
      200:
        description: 删除成功
      403:
        description: 权限不足
      404:
        description: 用户不存在
      500:
        description: 服务器错误
    """
    current_app.logger.info("收到删除用户请求")
    
    # 解析请求数据
    data = request.get_json()
    if not data or 'user_id' not in data:
        current_app.logger.error("缺少user_id参数")
        return APIResponse.error("缺少用户ID", 400)
    
    user_id = data.get('user_id')
    current_app.logger.info(f"尝试删除用户ID: {user_id}")
    
    # 获取当前用户身份
    current_user_id = get_jwt_identity()
    
    # 不允许删除自己
    if int(current_user_id) == int(user_id):
        return APIResponse.error("不能删除自己的账号", 403)
    
    # 获取用户
    user = User.get_by_id(int(user_id))
    if not user:
        return APIResponse.error("用户不存在", 404)
    
    # 不允许删除超级管理员
    if user['role'] == 'superadmin':
        return APIResponse.error("不能删除超级管理员账号", 403)
    
    try:
        conn = db.connect()
        cursor = conn.cursor()
        
        # 开始删除用户相关数据
        # 1. 删除用户的积分历史记录
        cursor.execute("DELETE FROM point_history WHERE user_id = %s", (user_id,))
        point_history_count = cursor.rowcount
        current_app.logger.info(f"已删除 {point_history_count} 条积分历史记录")
        
        # 2. 删除用户的训练报名记录
        cursor.execute("DELETE FROM training_registrations WHERE user_id = %s", (user_id,))
        training_reg_count = cursor.rowcount
        current_app.logger.info(f"已删除 {training_reg_count} 条训练报名记录")
        
        # 3. 删除用户的活动报名记录
        cursor.execute("DELETE FROM event_registrations WHERE user_id = %s", (user_id,))
        event_reg_count = cursor.rowcount
        current_app.logger.info(f"已删除 {event_reg_count} 条活动报名记录")
        
        # 4. 删除用户的升降旗记录
        cursor.execute("DELETE FROM flag_records WHERE user_id = %s", (user_id,))
        flag_records_count = cursor.rowcount
        current_app.logger.info(f"已删除 {flag_records_count} 条升降旗记录")
        
        # 5. 最后删除用户本身
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        user_count = cursor.rowcount
        
        # 提交事务
        conn.commit()
        cursor.close()
        
        if user_count == 0:
            current_app.logger.error(f"用户 {user_id} 在最终删除阶段未找到")
            return APIResponse.error("用户删除失败", 500)
        
        current_app.logger.info(f"成功删除用户 {user['username']} (ID: {user_id})")
        return APIResponse.success(msg="用户删除成功")
        
    except Exception as e:
        # 回滚事务
        if 'conn' in locals() and conn:
            conn.rollback()
        current_app.logger.error(f"删除用户时发生错误: {str(e)}")
        return APIResponse.error(f"删除用户失败: {str(e)}", 500) 