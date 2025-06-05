from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import FlagRecord, User, PointHistory
from extensions import db
from routes.auth import role_required
from datetime import datetime
from sqlalchemy import desc
from flask import current_app

flag_bp = Blueprint('flag', __name__)

@flag_bp.route('/flag/records', methods=['POST'])
@jwt_required()
def create_flag_record():
    """
    创建升降旗记录
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            date:
              type: string
              format: date
            type:
              type: string
              enum: [raise, lower]
            photo_url:
              type: string
    responses:
      201:
        description: 记录创建成功
      400:
        description: 参数错误
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    current_app.logger.info(f"Creating flag record for user {user_id}: {data}")
    
    # 验证必要字段
    required_fields = ['date', 'type', 'photo_url']
    if not all(field in data for field in required_fields):
        current_app.logger.warning(f"Missing required fields: {data}")
        return jsonify({"msg": "Missing required fields"}), 400
    
    # 验证类型
    if data['type'] not in ['raise', 'lower']:
        current_app.logger.warning(f"Invalid flag operation type: {data['type']}")
        return jsonify({"msg": "Invalid flag operation type"}), 400
    
    # 创建记录
    record = FlagRecord(
        user_id=user_id,
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        type=data['type'],
        photo_url=data['photo_url'],
        status='pending'
    )
    
    try:
        db.session.add(record)
        db.session.commit()
        current_app.logger.info(f"Flag record created successfully: {record.to_dict()}")
        return jsonify({
            "msg": "success",
            "data": record.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create flag record: {str(e)}")
        return jsonify({"msg": "Failed to create record"}), 500

@flag_bp.route('/flag/records', methods=['GET'])
@jwt_required()
def get_flag_records():
    """
    获取用户的升降旗记录
    ---
    tags:
      - 升降旗
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
      - name: status
        in: query
        type: string
        enum: [pending, approved, rejected]
    responses:
      200:
        description: 成功获取记录列表
    """
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    query = FlagRecord.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(desc(FlagRecord.date))\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        "data": {
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }
    }), 200

@flag_bp.route('/flag/records/review', methods=['GET'])
@jwt_required()
def get_flag_records_for_review():
    """
    获取所有升降旗记录（管理员用）
    ---
    tags:
      - 升降旗
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
      - name: status
        in: query
        type: string
        enum: [pending, approved, rejected]
    responses:
      200:
        description: 成功获取记录列表
      403:
        description: 权限不足
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user.is_admin():
        return jsonify({"msg": "Permission denied"}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    query = FlagRecord.query
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(desc(FlagRecord.date))\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        "data": {
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page
        }
    }), 200

@flag_bp.route('/flag/records/<int:record_id>/approve', methods=['POST'])
@jwt_required()
def approve_flag_record(record_id):
    """
    审核通过升降旗记录
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 审核成功
      403:
        description: 权限不足
      404:
        description: 记录不存在
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user.is_admin():
        return jsonify({"msg": "Permission denied"}), 403
    
    record = FlagRecord.query.get(record_id)
    if not record:
        return jsonify({"msg": "Record not found"}), 404
    
    if record.status != 'pending':
        return jsonify({"msg": "Record already reviewed"}), 400
    
    try:
        # 更新记录状态
        record.status = 'approved'
        record.reviewed_at = datetime.utcnow()
        record.reviewer_id = user_id
        
        # 计算并添加积分
        points = 0.5  # 统一设置为0.5分
        record.points_awarded = points
        
        # 更新用户总积分
        record_user = User.query.get(record.user_id)
        record_user.total_points += points
        
        # 创建积分历史记录
        point_history = PointHistory(
            user_id=record.user_id,
            points_change=points,
            change_type='flag',
            description=f'{"升旗" if record.type == "raise" else "降旗"}记录审核通过',
            related_id=record_id
        )
        
        db.session.add(point_history)
        db.session.commit()
        
        return jsonify({
            "msg": "success",
            "data": record.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to approve record"}), 500

@flag_bp.route('/flag/records/<int:record_id>/reject', methods=['POST'])
@jwt_required()
def reject_flag_record(record_id):
    """
    拒绝升降旗记录
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 拒绝成功
      403:
        description: 权限不足
      404:
        description: 记录不存在
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user.is_admin():
        return jsonify({"msg": "Permission denied"}), 403
    
    record = FlagRecord.query.get(record_id)
    if not record:
        return jsonify({"msg": "Record not found"}), 404
    
    if record.status != 'pending':
        return jsonify({"msg": "Record already reviewed"}), 400
    
    try:
        record.status = 'rejected'
        record.reviewed_at = datetime.utcnow()
        record.reviewer_id = user_id
        db.session.commit()
        
        return jsonify({
            "msg": "success",
            "data": record.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Failed to reject record"}), 500