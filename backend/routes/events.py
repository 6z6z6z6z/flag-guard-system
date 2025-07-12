from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models_pymysql import Event, Training, EventRegistration, PointHistory, User, EventTraining
from db_connection import db
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, role_required
)
from utils.time_utils import TimeUtils
from sql.queries import EVENT_QUERIES, EVENT_REGISTRATION_QUERIES, EVENT_TRAINING_QUERIES

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
    
    # 获取所有活动
    events = Event.list_all()
    
    # 手动分页
    total = len(events)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    # 获取当前页的活动
    current_page_events = events[start_idx:end_idx] if start_idx < total else []
    
    # 格式化活动数据
    items = []
    user_id = int(get_jwt_identity())
    
    for event in current_page_events:
        event_dict = Event.format_dict(event)
        
        # 获取关联的训练
        trainings_query = """
            SELECT t.training_id, t.name, t.status as type 
            FROM event_trainings et
            JOIN trainings t ON et.training_id = t.training_id
            WHERE et.event_id = %s
        """
        trainings = db.execute_query(trainings_query, (event['event_id'],))
        
        event_dict['trainings'] = trainings
        
        # 检查当前用户是否已报名
        registration = EventRegistration.get_by_event_and_user(event['event_id'], user_id)
        event_dict['is_registered'] = registration is not None
        event_dict['location'] = event['location'] or '未设置'
        
        items.append(event_dict)
    
    return APIResponse.success(data={
        'items': items,
        'total': total,
        'pages': total_pages,
        'current_page': page
    })

@bp.route('/', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
def create_event():
    """创建活动"""
    current_app.logger.info("=== 开始创建活动 ===")
    
    data = request.get_json()
    current_app.logger.info(f"接收到的完整数据: {data}")
    
    # 验证必填字段
    required_fields = ['name', 'time']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        current_app.logger.error(f"字段验证失败: {error_msg}")
        return APIResponse.error(error_msg, 400)
    
    try:
        # 记录接收到的原始数据
        current_app.logger.info(f"创建活动接收到的数据: {data}")
        
        # 解析前端传来的北京时间
        time_str = data['time']
        current_app.logger.info(f"原始时间字符串: {time_str}")
        
        parsed_time = TimeUtils.parse_frontend_time(time_str)
        if not parsed_time:
            return APIResponse.error('时间格式无效', 400)
            
        current_app.logger.info(f"解析后的北京时间: {parsed_time}")
        
        event = Event.create(
            name=data['name'],
            time=parsed_time,
            location=data.get('location'),
            uniform_required=data.get('uniform_required'),
            created_by=get_jwt_identity()
        )
        
        # 关联训练
        if data.get('trainings'):
            for training_id in data['trainings']:
                EventTraining.add(event['event_id'], training_id)
        
        return APIResponse.success(
            data=event,
            msg="活动创建成功",
            code=201
        )
    except ValueError as e:
        return APIResponse.error(f"Invalid date format: {str(e)}", 400)
    except Exception as e:
        current_app.logger.error(f"Failed to create event: {str(e)}")
        return APIResponse.error("Failed to create event", 500)

@bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'superadmin')
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
    event = Event.get_by_id(event_id)
    if not event:
        return APIResponse.error("活动不存在", 404)
    
    # 检查是否为过期活动（基于北京时间）
    event_time = TimeUtils.to_beijing_time(event['time'])
    current_beijing_time = TimeUtils.now_beijing()
    
    if event_time and event_time < current_beijing_time:
        return APIResponse.error("不能修改已过期的活动", 400)
    
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'time']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    try:
        # 解析前端传来的北京时间
        parsed_time = TimeUtils.parse_frontend_time(data['time'])
        if not parsed_time:
            return APIResponse.error('时间格式无效', 400)
        
        # 更新基本信息
        updated_event = Event.update(
            event_id=event_id,
            name=data['name'],
            time=parsed_time,
            location=data.get('location'),
            uniform_required=data.get('uniform_required')
        )
        
        # 更新关联训练
        # 先删除所有已关联的训练
        delete_trainings_query = "DELETE FROM event_trainings WHERE event_id = %s"
        db.execute_update(delete_trainings_query, (event_id,))
        
        # 添加新的关联训练
        if data.get('trainings'):
            for training_id in data['trainings']:
                EventTraining.add(event_id, training_id)
        
        return APIResponse.success(data=updated_event)
    except ValueError as e:
        return APIResponse.error(f"Invalid date format: {str(e)}", 400)
    except Exception as e:
        current_app.logger.error(f"Failed to update event: {str(e)}")
        return APIResponse.error("Failed to update event", 500)

@bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin', 'superadmin')
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
    event = Event.get_by_id(event_id)
    if not event:
        return APIResponse.error("活动不存在", 404)
    
    try:
        # 删除活动关联的训练记录
        delete_trainings_query = "DELETE FROM event_trainings WHERE event_id = %s"
        db.execute_update(delete_trainings_query, (event_id,))
        
        # 删除活动的报名记录
        delete_registrations_query = "DELETE FROM event_registrations WHERE event_id = %s"
        db.execute_update(delete_registrations_query, (event_id,))
        
        # 删除活动
        Event.delete(event_id)
        
        return APIResponse.success(msg="活动删除成功")
    except Exception as e:
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
      400:
        description: 已报名或活动已过期
      404:
        description: 活动不存在
    """
    user_id = int(get_jwt_identity())
    
    # 检查活动是否存在
    event = Event.get_by_id(event_id)
    if not event:
        return APIResponse.error("活动不存在", 404)
    
    # 检查是否为过期活动（基于北京时间）
    # 从数据库读取的时间是UTC时间，需要先转换为北京时间
    event_time = TimeUtils.from_db_to_beijing(event['time'])
    current_beijing_time = TimeUtils.now_beijing()
    
    current_app.logger.info(f"活动时间: {event_time}, 当前北京时间: {current_beijing_time}")
    
    if event_time and event_time < current_beijing_time:
        current_app.logger.warning(f"活动 {event_id} 已过期，活动时间: {event_time}, 当前时间: {current_beijing_time}")
        return APIResponse.error("不能报名已过期的活动", 400)
    
    # 检查是否已经报名
    existing_registration = EventRegistration.get_by_event_and_user(event_id, user_id)
    if existing_registration:
        current_app.logger.warning(f"用户 {user_id} 已经报名活动 {event_id}")
        return APIResponse.error("你已经报名参加此活动", 400)
    
    try:
        # 创建报名记录
        registration = EventRegistration.create(
            event_id=event_id,
            user_id=user_id
        )
        
        return APIResponse.success(
            data=registration,
            msg="报名成功",
            code=201
        )
    except Exception as e:
        current_app.logger.error(f"Failed to register for event: {str(e)}")
        return APIResponse.error("报名失败", 500)

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
        description: 取消报名成功
      400:
        description: 未报名或活动已过期
      404:
        description: 活动不存在
    """
    user_id = int(get_jwt_identity())
    
    # 检查活动是否存在
    event = Event.get_by_id(event_id)
    if not event:
        return APIResponse.error("活动不存在", 404)
    
    # 检查是否为过期活动（基于北京时间）
    event_time = TimeUtils.to_beijing_time(event['time'])
    current_beijing_time = TimeUtils.now_beijing()
    
    if event_time and event_time < current_beijing_time:
        return APIResponse.error("不能取消已过期活动的报名", 400)
    
    # 检查是否已经报名
    registration = EventRegistration.get_by_event_and_user(event_id, user_id)
    if not registration:
        return APIResponse.error("你未报名参加此活动", 400)
    
    try:
        # 删除报名记录
        EventRegistration.delete(registration['registration_id'])
        return APIResponse.success(msg="取消报名成功")
    except Exception as e:
        current_app.logger.error(f"Failed to cancel event registration: {str(e)}")
        return APIResponse.error("取消报名失败", 500)

@bp.route('/<int:event_id>/registrations', methods=['GET'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def get_event_registrations(event_id):
    """
    获取活动报名列表
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
        description: 报名列表
      403:
        description: 权限不足
      404:
        description: 活动不存在
    """
    # 检查活动是否存在
    event = Event.get_by_id(event_id)
    if not event:
        return APIResponse.error("活动不存在", 404)
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        # 获取活动的报名记录
        registrations = EventRegistration.list_by_event(event_id)
        
        # 检查每条记录，确保身高、体重、鞋码字段有值
        for reg in registrations:
            current_app.logger.info(f"单条报名记录数据: height={reg.get('height')}, weight={reg.get('weight')}, shoe_size={reg.get('shoe_size')}")
        
        # 确保数据格式化正确，特别注意身高、体重和鞋码字段
        formatted_registrations = []
        current_app.logger.info(f"活动 {event_id} 报名记录原始数据: {registrations}")
        
        for reg in registrations:
            # 确保每个注册记录包含所有必要的字段，确保身高、体重、鞋码字段存在
            formatted_reg = {
                'registration_id': reg.get('registration_id'),
                'event_id': reg.get('event_id'),
                'user_id': reg.get('user_id'),
                'status': reg.get('status'),
                'created_at': reg.get('created_at'),
                'name': reg.get('name'),
                'student_id': reg.get('student_id'),
                'college': reg.get('college'),
                'username': reg.get('username'),
                'phone_number': reg.get('phone_number'),
                'height': reg.get('height'),  # 确保身高字段存在
                'weight': reg.get('weight'),  # 确保体重字段存在
                'shoe_size': reg.get('shoe_size')  # 确保鞋码字段存在
            }
            formatted_registrations.append(formatted_reg)
            
        current_app.logger.info(f"活动 {event_id} 报名记录格式化后: {formatted_registrations}")
        
        # 手动分页
        total = len(formatted_registrations)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        
        # 获取当前页的记录
        current_page_items = formatted_registrations[start_idx:end_idx] if start_idx < total else []
        
        current_app.logger.info(f"返回活动 {event_id} 的报名列表: {len(current_page_items)} 条记录")
        
        return APIResponse.success(data={
            'items': current_page_items,
            'total': total,
            'pages': total_pages,
            'current_page': page
        })
    
    except Exception as e:
        current_app.logger.error(f"获取活动 {event_id} 的报名列表失败: {str(e)}")
        return APIResponse.error(f"获取报名列表失败: {str(e)}", 500)

@bp.route('/<int:event_id>/points', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
def add_event_points(event_id):
    """
    为参加活动的用户添加积分
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
            points:
              type: number
            description:
              type: string
    responses:
      200:
        description: 积分添加成功
      400:
        description: 参数错误
      403:
        description: 权限不足
      404:
        description: 活动不存在
    """
    # 检查活动是否存在
    event = Event.get_by_id(event_id)
    if not event:
        return APIResponse.error("活动不存在", 404)
    
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['points', 'description']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    points = data['points']
    description = data['description']
    
    try:
        # 获取活动的所有报名记录
        registrations = EventRegistration.list_by_event(event_id)
        
        # 为每个报名用户添加积分
        success_count = 0
        for reg in registrations:
            if User.add_points(
                user_id=reg['user_id'],
                points=points,
                change_type='event',
                related_id=event_id,
                description=description
            ):
                success_count += 1
        
        return APIResponse.success(
            data={'affected_users': success_count},
            msg=f"已为{success_count}名用户添加积分"
        )
    except Exception as e:
        current_app.logger.error(f"Failed to add points for event: {str(e)}")
        return APIResponse.error("添加积分失败", 500) 