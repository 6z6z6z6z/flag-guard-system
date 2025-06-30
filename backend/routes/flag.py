from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import FlagRecord, User, PointHistory
from extensions import db
from datetime import datetime
from sqlalchemy import desc
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, role_required
)

bp = Blueprint('flag', __name__)

@bp.route('/records', methods=['POST'])
@jwt_required()
@validate_json_request
@handle_exceptions
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
    data = request.get_json()
    
    # 验证必要字段
    required_fields = ['date', 'type', 'photo_url']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    # 验证类型
    if data['type'] not in ['raise', 'lower']:
        return APIResponse.error("Invalid flag operation type", 400)
    
    try:
        # 创建记录
        record = FlagRecord(
            user_id=get_jwt_identity(),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            type=data['type'],
            photo_url=data['photo_url'],
            status='pending'
        )
        
        db.session.add(record)
        db.session.commit()
        return APIResponse.success(
            data=record.to_dict(),
            msg="升降旗记录创建成功",
            code=200
        )
    except ValueError as e:
        return APIResponse.error(f"Invalid date format: {str(e)}", 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create flag record: {str(e)}")
        return APIResponse.error("Failed to create record", 500)

@bp.route('/records', methods=['GET'])
@jwt_required()
@handle_exceptions
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
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    query = FlagRecord.query.filter_by(user_id=get_jwt_identity())
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(desc(FlagRecord.date))\
        .paginate(page=page, per_page=per_page)
    
    return APIResponse.success(data={
        "items": [item.to_dict() for item in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    })

@bp.route('/records/review', methods=['GET'])
@jwt_required()
@role_required('admin')
@handle_exceptions
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
    current_app.logger.info("Entering get_flag_records_for_review function")
    current_app.logger.info(f"Current user ID: {get_jwt_identity()}")
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    current_app.logger.info(f"Query parameters: page={page}, per_page={per_page}, status={status}")
    
    query = FlagRecord.query
    if status:
        query = query.filter_by(status=status)
    
    pagination = query.order_by(desc(FlagRecord.date))\
        .paginate(page=page, per_page=per_page)
    
    current_app.logger.info(f"Found {pagination.total} records")
    
    # 获取所有记录的用户信息
    items = []
    for item in pagination.items:
        record_dict = item.to_dict()
        user = User.query.get(item.user_id)
        if user:
            record_dict['user'] = {
                'name': user.name,
                'student_id': user.student_id
            }
        items.append(record_dict)
    
    current_app.logger.info(f"Returning {len(items)} records")
    
    return APIResponse.success(data={
        "items": items,
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page
    })

@bp.route('/records/<int:record_id>/approve', methods=['POST'])
@jwt_required()
@role_required('admin')
@handle_exceptions
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
    record = FlagRecord.query.get_or_404(record_id)
    current_app.logger.info(f"Processing flag record approval for record_id: {record_id}")
    
    if record.status != 'pending':
        current_app.logger.warning(f"Record {record_id} is already reviewed with status: {record.status}")
        return APIResponse.error("Record already reviewed", 400)
    
    try:
        # 更新记录状态
        record.status = 'approved'
        record.reviewed_at = datetime.utcnow()
        record.reviewer_id = get_jwt_identity()
        
        # 计算并添加积分
        points = current_app.config.get('FLAG_POINTS', 5)
        flag_type_text = '升旗' if record.type == 'raise' else '降旗'
        current_app.logger.info(f"Awarding {points} points for flag record {record_id}")
        
        # 更新记录积分
        record.points_awarded = float(points)
        current_app.logger.info(f"Record points_awarded set to: {record.points_awarded}")
        
        # 更新用户总积分
        record_user = User.query.get(record.user_id)
        if record_user:
            record_user.total_points = (record_user.total_points or 0) + points
        
        # 创建积分历史记录
        point_history = PointHistory(
            user_id=record.user_id,
            points_change=points,
            change_type='flag',
            description=f'完成{record.date.strftime("%Y-%m-%d")}的{flag_type_text}任务',
            related_id=record_id
        )
        db.session.add(point_history)
        
        # 保存所有变更
        db.session.commit()
        current_app.logger.info(f"Successfully approved flag record {record_id} and updated user points.")
        return APIResponse.success(msg="审核成功")
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during flag approval for record {record_id}: {str(e)}")
        return APIResponse.error("审核操作失败", 500)

@bp.route('/records/<int:record_id>/reject', methods=['POST'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def reject_flag_record(record_id):
    """
    审核拒绝升降旗记录
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
        description: 操作成功
      403:
        description: 权限不足
      404:
        description: 记录不存在
    """
    record = FlagRecord.query.get_or_404(record_id)
    
    if record.status != 'pending':
        return APIResponse.error("Record already reviewed", 400)
    
    record.status = 'rejected'
    record.reviewed_at = datetime.utcnow()
    record.reviewer_id = get_jwt_identity()
    db.session.commit()
    
    return APIResponse.success(msg="操作成功")