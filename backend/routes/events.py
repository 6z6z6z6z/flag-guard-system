from flask import Blueprint, jsonify, request, g
from datetime import datetime
from models import Event, Training, db, EventRegistration
from utils.auth import login_required, admin_required
from utils.pagination import paginate
from flask import current_app

bp = Blueprint('events', __name__)

@bp.route('/')
@login_required
def get_events():
    """获取活动列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Event.query.order_by(Event.time.desc())
    pagination = paginate(query, page, per_page)
    
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
            user_id=g.user.user_id
        ).first()
        event_dict['is_registered'] = registration is not None
        
        items.append(event_dict)
    
    # 直接返回活动列表
    return jsonify(items)

@bp.route('/', methods=['POST'])
@admin_required
def create_event():
    """创建活动"""
    data = request.get_json()
    name = data.get('name')
    time = data.get('time')
    uniform_required = data.get('uniform_required')
    training_ids = data.get('trainings', [])
    
    if not all([name, time]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        # 创建活动
        event = Event(
            name=name,
            time=datetime.fromisoformat(time.replace('Z', '+00:00')),
            uniform_required=uniform_required,
            created_by=g.user.user_id
        )
        db.session.add(event)
        
        # 关联训练
        if training_ids:
            trainings = Training.query.filter(Training.training_id.in_(training_ids)).all()
            event.trainings.extend(trainings)
        
        db.session.commit()
        return jsonify(event.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:event_id>', methods=['PUT'])
@admin_required
def update_event(event_id):
    """更新活动"""
    event = Event.query.get_or_404(event_id)
    
    # 检查是否为过期活动
    if event.time < datetime.utcnow():
        return jsonify({'error': '不能修改已过期的活动'}), 400
    
    data = request.get_json()
    name = data.get('name')
    time = data.get('time')
    uniform_required = data.get('uniform_required')
    training_ids = data.get('trainings', [])
    
    if not all([name, time]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        # 更新基本信息
        event.name = name
        event.time = datetime.fromisoformat(time.replace('Z', '+00:00'))
        event.uniform_required = uniform_required
        
        # 更新关联训练
        event.trainings = []
        if training_ids:
            trainings = Training.query.filter(Training.training_id.in_(training_ids)).all()
            event.trainings.extend(trainings)
        
        db.session.commit()
        return jsonify(event.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:event_id>', methods=['DELETE'])
@admin_required
def delete_event(event_id):
    """删除活动"""
    try:
        # 记录请求信息
        current_app.logger.info(f"Event deletion attempt - event_id: {event_id}, user_id: {g.user.user_id}")
        
        # 检查活动是否存在
        event = Event.query.get_or_404(event_id)
        if not event:
            current_app.logger.warning(f"Event not found - event_id: {event_id}")
            return jsonify({'error': '活动不存在'}), 404
        
        try:
            # 先删除所有相关的报名记录
            registrations = EventRegistration.query.filter_by(event_id=event_id).all()
            for registration in registrations:
                db.session.delete(registration)
            
            # 删除活动
            db.session.delete(event)
            db.session.commit()
            
            current_app.logger.info(f"Event and its registrations deleted successfully - event_id: {event_id}")
            return jsonify({'message': '活动删除成功'}), 200
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error while deleting event: {str(e)}")
            return jsonify({'error': '删除活动时发生数据库错误'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Event deletion error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:event_id>/register', methods=['POST'])
@login_required
def register_for_event(event_id):
    """注册参加活动"""
    try:
        # 记录请求信息
        current_app.logger.info(f"Event registration attempt - event_id: {event_id}, user_id: {g.user.user_id}")
        
        # 检查活动是否存在
        event = Event.query.get_or_404(event_id)
        if not event:
            current_app.logger.warning(f"Event not found - event_id: {event_id}")
            return jsonify({'error': '活动不存在'}), 404
            
        user_id = g.user.user_id
        
        # 检查是否已经注册
        existing_reg = EventRegistration.query.filter_by(
            event_id=event_id,
            user_id=user_id
        ).first()
        
        if existing_reg:
            current_app.logger.warning(f"User already registered - event_id: {event_id}, user_id: {user_id}")
            return jsonify({'error': '已经注册过该活动'}), 400
        
        # 检查活动时间是否已过
        if event.time < datetime.utcnow():
            current_app.logger.warning(f"Event has expired - event_id: {event_id}")
            return jsonify({'error': '活动已过期'}), 400
        
        # 创建新的注册记录
        registration = EventRegistration(
            event_id=event_id,
            user_id=user_id,
            status='registered'  # 显式设置状态
        )
        db.session.add(registration)
        db.session.commit()
        
        current_app.logger.info(f"Event registration successful - event_id: {event_id}, user_id: {user_id}")
        return jsonify({
            'message': '活动注册成功',
            'registration_id': registration.registration_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Event registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:event_id>/register', methods=['DELETE'])
@login_required
def cancel_event_registration(event_id):
    """取消活动报名"""
    event = Event.query.get_or_404(event_id)
    user_id = g.user.user_id
    
    # 查找注册记录
    registration = EventRegistration.query.filter_by(
        event_id=event_id,
        user_id=user_id,
        status='registered'  # 只能取消已报名但未确认的报名
    ).first()
    
    if not registration:
        return jsonify({'error': '未找到有效的报名记录'}), 404
    
    try:
        # 删除报名记录
        db.session.delete(registration)
        db.session.commit()
        return jsonify({'message': '成功取消活动报名'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:event_id>/registrations', methods=['GET'])
@admin_required
def get_event_registrations(event_id):
    """获取活动报名人员名单"""
    try:
        # 检查活动是否存在
        event = Event.query.get_or_404(event_id)
        if not event:
            return jsonify({'error': '活动不存在'}), 404
            
        # 获取所有报名记录
        registrations = EventRegistration.query.filter_by(event_id=event_id).all()
        
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
                'height': user.height if user.height is not None else 0,
                'weight': user.weight if user.weight is not None else 0,
                'shoe_size': user.shoe_size if user.shoe_size is not None else 0,
                'status': reg.status,
                'created_at': reg.created_at.isoformat() if reg.created_at else None
            })
            
        return jsonify(registration_list)
        
    except Exception as e:
        current_app.logger.error(f"Error getting event registrations: {str(e)}")
        return jsonify({'error': str(e)}), 500 