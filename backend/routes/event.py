from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import Event, EventRegistration, User
from extensions import db

event_bp = Blueprint('event', __name__)

@event_bp.route('/events', methods=['POST'])
@jwt_required()
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
              description: 活动名称
            time:
              type: string
              format: date-time
              description: 活动时间
            uniform_required:
              type: string
              description: 着装要求
    responses:
      201:
        description: 活动创建成功
      401:
        description: 未认证
      403:
        description: 权限不足
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin':
        return jsonify({'message': '权限不足'}), 403

    data = request.get_json()
    
    event = Event(
        name=data['name'],
        time=datetime.fromisoformat(data['time']),
        uniform_required=data.get('uniform_required'),
        created_by=user_id
    )
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'message': '活动创建成功', 'event_id': event.event_id}), 201

@event_bp.route('/events', methods=['GET'])
@jwt_required()
def get_events():
    """
    获取所有活动列表
    ---
    tags:
      - 活动
    security:
      - Bearer: []
    responses:
      200:
        description: 活动列表
      401:
        description: 未认证
    """
    events = Event.query.all()
    return jsonify([{
        'event_id': event.event_id,
        'name': event.name,
        'time': event.time.isoformat(),
        'uniform_required': event.uniform_required,
        'created_by': event.created_by
    } for event in events]), 200

@event_bp.route('/events/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    """
    获取活动详情
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
        description: 活动ID
    responses:
      200:
        description: 活动详情
      401:
        description: 未认证
      404:
        description: 活动不存在
    """
    event = Event.query.get_or_404(event_id)
    return jsonify({
        'event_id': event.event_id,
        'name': event.name,
        'time': event.time.isoformat(),
        'uniform_required': event.uniform_required,
        'created_by': event.created_by
    }), 200