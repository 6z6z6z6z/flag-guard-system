from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import Event, Training, EventRegistration, PointHistory
from extensions import db
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, role_required
)

bp = Blueprint('events', __name__)

@bp.route('/')
@jwt_required()
@handle_exceptions
def get_events():
    """
    获取活动列表
    ---
    tags:
      - 活动
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
        description: 活动列表
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Event.query.order_by(Event.time.desc())
    pagination = query.paginate(page=page, per_page=per_page)
    
    items = []
    for event in pagination.items:
        event_dict = event.to_dict()
        event_dict['trainings'] = [{
            'training_id': t.training_id,
            'name': t.name,
            'type': t.type
        } for t in event.trainings]
        
        # 检查当前用户是否已报名
        registration = EventRegistration.query.filter_by(
            event_id=event.event_id,
            user_id=get_jwt_identity()
        ).first()
        event_dict['is_registered'] = registration is not None
        event_dict['location'] = event.location or '未设置'
        
        items.append(event_dict)
    
    return APIResponse.success(data={
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@bp.route('/', methods=['POST'])
@jwt_required()
@role_required('admin')
@validate_json_request
@handle_exceptions
def create_event():
    """
    创建活动
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            time:
              type: string
              format: date-time
            uniform_required:
              type: string
            trainings:
              type: array
              items:
                type: integer
    responses:
      201:
        description: 活动创建成功
      400:
        description: 参数错误
      403:
        description: 权限不足
    """
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'time']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    try:
        # 创建活动
        event = Event(
            name=data['name'],
            time=datetime.fromisoformat(data['time'].replace('Z', '+00:00')),
            location=data.get('location'),
            uniform_required=data.get('uniform_required'),
            created_by=get_jwt_identity()
        )
        db.session.add(event)
        
        # 关联训练
        if data.get('trainings'):
            trainings = Training.query.filter(Training.training_id.in_(data['trainings'])).all()
            event.trainings.extend(trainings)
        
        db.session.commit()
        return APIResponse.success(
            data=event.to_dict(),
            msg="活动创建成功",
            code=201
        )
    except ValueError as e:
        return APIResponse.error(f"Invalid date format: {str(e)}", 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create event: {str(e)}")
        return APIResponse.error("Failed to create event", 500)

@bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
@validate_json_request
@handle_exceptions
def update_event(event_id):
    """
    更新活动
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    parameters:
      - name: event_id
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
            time:
              type: string
              format: date-time
            uniform_required:
              type: string
            trainings:
              type: array
              items:
                type: integer
    responses:
      200:
        description: 活动更新成功
      400:
        description: 参数错误或活动已过期
      403:
        description: 权限不足
      404:
        description: 活动不存在
    """
    event = Event.query.get_or_404(event_id)
    
    # 检查是否为过期活动
    if event.time < datetime.utcnow():
        return APIResponse.error("不能修改已过期的活动", 400)
    
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'time']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    try:
        # 更新基本信息
        event.name = data['name']
        event.time = datetime.fromisoformat(data['time'].replace('Z', '+00:00'))
        event.location = data.get('location')
        event.uniform_required = data.get('uniform_required')
        
        # 更新关联训练
        event.trainings = []
        if data.get('trainings'):
            trainings = Training.query.filter(Training.training_id.in_(data['trainings'])).all()
            event.trainings.extend(trainings)
        
        db.session.commit()
        return APIResponse.success(data=event.to_dict())
    except ValueError as e:
        return APIResponse.error(f"Invalid date format: {str(e)}", 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update event: {str(e)}")
        return APIResponse.error("Failed to update event", 500)

@bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def delete_event(event_id):
    """
    删除活动
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 活动删除成功
      403:
        description: 权限不足
      404:
        description: 活动不存在
    """
    event = Event.query.get_or_404(event_id)
    
    try:
        # 先删除所有相关的报名记录
        registrations = EventRegistration.query.filter_by(event_id=event_id).all()
        for registration in registrations:
            db.session.delete(registration)
        
        # 删除活动
        db.session.delete(event)
        db.session.commit()
        
        return APIResponse.success(msg="活动删除成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete event: {str(e)}")
        return APIResponse.error("Failed to delete event", 500)

@bp.route('/<int:event_id>/register', methods=['POST'])
@jwt_required()
@handle_exceptions
def register_for_event(event_id):
    """
    报名参加活动
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      201:
        description: 报名成功
      404:
        description: 活动不存在
      409:
        description: 用户已报名
      410:
        description: 活动已过期
    """
    event = Event.query.get_or_404(event_id)
    user_id = get_jwt_identity()
    
    # 检查活动是否已过期
    if event.time < datetime.utcnow():
        return APIResponse.error("活动已过期，无法报名", 410)
    
    # 检查用户是否已报名
    existing_registration = EventRegistration.query.filter_by(
        event_id=event_id, user_id=user_id
    ).first()
    
    if existing_registration:
        return APIResponse.error(msg="您已报名该活动", code=409)
    
    try:
        # 创建报名记录
        registration = EventRegistration(event_id=event_id, user_id=user_id)
        db.session.add(registration)
        db.session.commit()
        
        return APIResponse.success(
            msg="报名成功", 
            data={'registration_id': registration.registration_id}, 
            code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to register for event: {str(e)}")
        return APIResponse.error(msg="报名时发生错误", code=500)

@bp.route('/<int:event_id>/register', methods=['DELETE'])
@jwt_required()
@handle_exceptions
def cancel_event_registration(event_id):
    """
    取消活动报名
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 成功取消活动报名
      404:
        description: 未找到有效的报名记录
    """
    user_id = get_jwt_identity()
    
    # 查找注册记录
    registration = EventRegistration.query.filter_by(
        event_id=event_id,
        user_id=user_id,
        status='registered'
    ).first_or_404()
    
    try:
        # 删除报名记录
        db.session.delete(registration)
        db.session.commit()
        return APIResponse.success(msg="成功取消活动报名")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to cancel event registration: {str(e)}")
        return APIResponse.error("Failed to cancel registration", 500)

@bp.route('/<int:event_id>/registrations', methods=['GET'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def get_event_registrations(event_id):
    """
    获取活动报名人员名单
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 报名人员名单
      403:
        description: 权限不足
      404:
        description: 活动不存在
    """
    event = Event.query.get_or_404(event_id)
    
    # 获取所有报名记录，按创建时间排序
    registrations = EventRegistration.query.filter_by(event_id=event_id).order_by(EventRegistration.created_at.desc()).all()
    
    # 获取报名用户信息
    registration_list = []
    for reg in registrations:
        user = reg.user
        registration_list.append({
            'registration_id': reg.registration_id,
            'user_id': user.user_id,
            'username': user.username,
            'name': user.name,
            'student_id': user.student_id,
            'college': user.college,
            'height': user.height,
            'weight': user.weight,
            'shoe_size': user.shoe_size,
            'phone_number': user.phone_number,
            'status': reg.status,
            'created_at': reg.created_at.isoformat() if reg.created_at else None
        })
    
    return APIResponse.success(data=registration_list)

@bp.route('/<int:event_id>/points', methods=['POST'])
@jwt_required()
@role_required('admin')
@validate_json_request
@handle_exceptions
def add_event_points(event_id):
    """
    添加活动积分
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
      - name: points
        in: query
        type: integer
        required: true
    responses:
      200:
        description: 活动积分添加成功
      400:
        description: 参数错误或活动已过期
      403:
        description: 权限不足
      404:
        description: 活动不存在
    """
    event = Event.query.get_or_404(event_id)
    user_id = get_jwt_identity()
    
    # 检查活动时间是否已过
    if event.time < datetime.utcnow():
        return APIResponse.error("活动已过期", 400)
    
    points = request.args.get('points', 0, type=int)
    
    try:
        # 添加积分记录
        history = PointHistory(
            user_id=user_id,
            points_change=points,
            change_type='event',
            description=f'参加活动：{event.name}（{"出勤" if attendance_status == "present" else "迟到" if attendance_status == "late" else "早退" if attendance_status == "early_leave" else "未到"}）',
            related_id=event_id
        )
        db.session.add(history)
        db.session.commit()
        
        return APIResponse.success(msg="活动积分添加成功")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to add event points: {str(e)}")
        return APIResponse.error("Failed to add event points", 500) 