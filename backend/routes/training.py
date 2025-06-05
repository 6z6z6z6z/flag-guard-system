from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import Training, TrainingRegistration, User
from extensions import db
from routes.auth import role_required

training_bp = Blueprint('training', __name__)

@training_bp.route('/trainings', methods=['GET'])
@jwt_required()
def get_trainings():
    """
    获取训练列表
    ---
    tags:
      - 训练
    security:
      - Bearer: []
    responses:
      200:
        description: 训练列表
        schema:
          type: array
          items:
            type: object
            properties:
              training_id:
                type: integer
              name:
                type: string
              type:
                type: string
              start_time:
                type: string
                format: date-time
              end_time:
                type: string
                format: date-time
              points:
                type: integer
              created_by:
                type: integer
    """
    trainings = Training.query.all()
    return jsonify([{
        'training_id': t.training_id,
        'name': t.name,
        'type': t.type,
        'start_time': t.start_time.isoformat(),
        'end_time': t.end_time.isoformat() if t.end_time else None,
        'points': t.points,
        'created_by': t.created_by
    } for t in trainings]), 200

@training_bp.route('/trainings/<int:training_id>', methods=['GET'])
@jwt_required()
def get_training(training_id):
    """
    获取特定训练详情
    ---
    tags:
      - 训练
    security:
      - Bearer: []
    parameters:
      - name: training_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 训练详情
      404:
        description: 训练不存在
    """
    training = Training.query.get_or_404(training_id)
    return jsonify({
        'training_id': training.training_id,
        'name': training.name,
        'type': training.type,
        'start_time': training.start_time.isoformat(),
        'end_time': training.end_time.isoformat() if training.end_time else None,
        'points': training.points,
        'created_by': training.created_by
    }), 200

@training_bp.route('/registrations/<int:reg_id>/confirm', methods=['PUT'])
@jwt_required()
def confirm_training_registration(reg_id):
    """
    确认训练参与并加分
    ---
    tags:
      - 训练
    security:
      - Bearer: []
    parameters:
      - name: reg_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 确认成功
      400:
        description: 已处理
      404:
        description: 记录不存在
      500:
        description: 加分失败
    """
    reg = TrainingRegistration.query.get_or_404(reg_id)
    training = Training.query.get_or_404(reg.training_id)
    
    if reg.status != 'registered':
        return jsonify({'error': 'Registration already processed'}), 400
    
    # 确认参与并加分
    user = User.query.get(reg.user_id)
    if user.add_points(training.points, 'training', reg_id, f'训练参与: {training.name}'):
        reg.status = 'confirmed'
        reg.attended = True
        reg.points_awarded = training.points
        db.session.commit()
        return jsonify({'message': 'Training confirmed'}), 200
    else:
        return jsonify({'error': 'Failed to add points'}), 500

@training_bp.route('/trainings/<int:training_id>/register', methods=['POST'])
@jwt_required()
def register_for_training(training_id):
    """
    注册参加训练
    ---
    tags:
      - 训练
    security:
      - Bearer: []
    parameters:
      - name: training_id
        in: path
        type: integer
        required: true
    responses:
      201:
        description: 注册成功
      400:
        description: 已注册
      404:
        description: 训练不存在
    """
    training = Training.query.get_or_404(training_id)
    user_id = get_jwt_identity()
    
    # 检查是否已经注册
    existing_reg = TrainingRegistration.query.filter_by(
        training_id=training_id,
        user_id=user_id
    ).first()
    
    if existing_reg:
        return jsonify({'error': 'Already registered for this training'}), 400
    
    # 创建新的注册记录
    registration = TrainingRegistration(
        training_id=training_id,
        user_id=user_id,
        status='registered'
    )
    db.session.add(registration)
    db.session.commit()
    
    return jsonify({
        'message': 'Successfully registered for training',
        'registration_id': registration.registration_id
    }), 201

@training_bp.route('/trainings', methods=['POST'])
@jwt_required()
@role_required('admin')  # 添加角色验证
def create_training():
    """
    创建训练
    ---
    tags:
      - 训练
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
            type:
              type: string
            start_time:
              type: string
              format: date-time
            end_time:
              type: string
              format: date-time
            points:
              type: integer
    responses:
      201:
        description: 训练创建成功
      401:
        description: 未认证
      403:
        description: 权限不足
    """
    data = request.get_json()
    training = Training(
        name=data['name'],
        type=data['type'],
        start_time=datetime.fromisoformat(data['start_time']),
        end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
        points=data['points'],
        created_by=get_jwt_identity()
    )
    db.session.add(training)
    db.session.commit()
    return jsonify({'message': 'Training created', 'training_id': training.training_id}), 201