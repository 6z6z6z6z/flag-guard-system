from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, PointHistory
from extensions import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
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
    try:
        # 获取JWT中的用户ID
        user_id = get_jwt_identity()
        current_app.logger.info(f"Getting profile for user_id: {user_id}")
        
        if not user_id:
            current_app.logger.warning("No user_id found in JWT token")
            return jsonify({"msg": "Invalid token"}), 401
        
        # 查询用户
        user = User.query.get(user_id)
        
        if not user:
            current_app.logger.warning(f"User not found for user_id: {user_id}")
            return jsonify({"msg": "User not found"}), 404
        
        # 返回用户信息
        user_data = {
            "username": user.username,
            "name": user.name,
            "student_id": user.student_id,
            "college": user.college,
            "height": user.height,
            "weight": user.weight,
            "shoe_size": user.shoe_size,
            "total_points": user.total_points,
            "role": user.role
        }
        
        current_app.logger.info(f"Successfully retrieved profile for user: {user.username}")
        return jsonify({
            "msg": "success",
            "data": user_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({"msg": str(e)}), 500

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
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
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        data = request.get_json()
        
        # 只允许更新特定字段
        allowed_fields = {'height', 'weight', 'shoe_size'}
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        return jsonify({
            "msg": "success",
            "data": {
                "height": user.height,
                "weight": user.weight,
                "shoe_size": user.shoe_size
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 500

@users_bp.route('/points/history', methods=['GET'])
@jwt_required()
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
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 获取分页的积分历史记录
        pagination = PointHistory.query.filter_by(user_id=user_id)\
            .order_by(PointHistory.change_time.desc())\
            .paginate(page=page, per_page=per_page)
        
        return jsonify({
            "msg": "success",
            "data": {
                "items": [item.to_dict() for item in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page
            }
        }), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@users_bp.route('/search', methods=['GET'])
@jwt_required()
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
    try:
        query = request.args.get('query', '')
        if not query:
            return jsonify([]), 200
            
        # 搜索用户名、姓名或学号包含关键词的用户
        users = User.query.filter(
            (User.username.ilike(f'%{query}%')) |
            (User.name.ilike(f'%{query}%')) |
            (User.student_id.ilike(f'%{query}%'))
        ).limit(10).all()
        
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        current_app.logger.error(f"Error searching users: {str(e)}")
        return jsonify({"msg": str(e)}), 500

@users_bp.route('/points/all', methods=['GET'])
@jwt_required()
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
    try:
        # 获取当前用户
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        
        if not current_user or current_user.role != 'admin':
            return jsonify({"msg": "权限不足"}), 403
            
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        query = request.args.get('query', '')
        
        # 构建查询
        user_query = User.query
        
        # 如果有搜索关键词，添加搜索条件
        if query:
            user_query = user_query.filter(
                (User.username.ilike(f'%{query}%')) |
                (User.name.ilike(f'%{query}%')) |
                (User.student_id.ilike(f'%{query}%'))
            )
        
        # 按积分降序排序
        user_query = user_query.order_by(User.total_points.desc())
        
        # 分页
        pagination = user_query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            "msg": "success",
            "data": {
                "items": [{
                    "user_id": user.user_id,
                    "username": user.username,
                    "name": user.name,
                    "student_id": user.student_id,
                    "college": user.college,
                    "total_points": user.total_points,
                    "role": user.role
                } for user in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": page
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error getting all users points: {str(e)}")
        return jsonify({"msg": str(e)}), 500

@users_bp.route('', methods=['POST'])
@jwt_required()
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
              enum: [admin, user]
              default: user
    responses:
      201:
        description: 用户创建成功
      400:
        description: 参数错误
      403:
        description: 权限不足
    """
    try:
        # 检查当前用户是否为管理员
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        
        if not current_user or current_user.role != 'admin':
            return jsonify({"msg": "权限不足"}), 403
            
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'password', 'name', 'student_id', 'college']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"msg": f"Missing required field: {field}"}), 400
                
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"msg": "Username already exists"}), 400
            
        # 检查学号是否已存在
        if User.query.filter_by(student_id=data['student_id']).first():
            return jsonify({"msg": "Student ID already exists"}), 400
            
        # 创建新用户
        user = User(
            username=data['username'],
            name=data['name'],
            student_id=data['student_id'],
            college=data['college'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "msg": "success",
            "data": {
                "user_id": user.user_id,
                "username": user.username,
                "name": user.name,
                "student_id": user.student_id,
                "college": user.college,
                "role": user.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating user: {str(e)}")
        return jsonify({"msg": str(e)}), 500 