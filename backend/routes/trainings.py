from flask import Blueprint, jsonify, request, g, current_app
from datetime import datetime
from models import Training, TrainingRegistration, User, PointHistory, db, EventTraining
from utils.auth import login_required, admin_required
from utils.pagination import paginate

bp = Blueprint('trainings', __name__)

@bp.route('/review')
@admin_required
def get_trainings_for_review():
    """获取训练列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')  # pending or reviewed
    
    query = Training.query
    if status == 'pending':
        # 获取未审核的训练（结束时间已过但未标记考勤的）
        query = query.filter(
            Training.end_time < datetime.utcnow(),
            ~Training.training_id.in_(
                db.session.query(TrainingRegistration.training_id)
                .filter(TrainingRegistration.status == 'awarded')
                .distinct()
            )
        )
    elif status == 'reviewed':
        # 获取已审核的训练
        query = query.filter(
            Training.training_id.in_(
                db.session.query(TrainingRegistration.training_id)
                .filter(TrainingRegistration.status == 'awarded')
                .distinct()
            )
        )
    
    query = query.order_by(Training.start_time.desc())
    pagination = paginate(query, page, per_page)
    
    items = []
    for training in pagination.items:
        training_dict = training.to_dict()
        training_dict['reviewed'] = any(r.status == 'awarded' for r in training.registrations)
        items.append(training_dict)
    
    return jsonify({
        'items': items,
        'total': pagination.total
    })

@bp.route('/<int:training_id>/attendance')
@admin_required
def get_attendance_list(training_id):
    """获取训练考勤名单"""
    try:
        # 获取训练信息
        training = Training.query.get_or_404(training_id)
        
        # 获取所有报名用户
        registrations = TrainingRegistration.query.filter_by(training_id=training_id).all()
        attendance_list = []
        
        for registration in registrations:
            user = registration.user
            attendance_list.append({
                'user_id': user.user_id,
                'name': user.name,
                'student_id': user.student_id,
                'college': user.college,
                'attendance_status': registration.attendance_status,
                'status': registration.status,
                'points_awarded': registration.points_awarded
            })
        
        return jsonify(attendance_list)
    except Exception as e:
        current_app.logger.error(f"Error getting attendance list: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:training_id>/attendance', methods=['POST'])
@admin_required
def submit_attendance(training_id):
    """提交训练考勤"""
    training = Training.query.get_or_404(training_id)
    data = request.get_json()
    attendance_records = data.get('attendance_records', [])
    
    if not isinstance(attendance_records, list):
        return jsonify({'error': '参数格式错误'}), 400
    
    # 检查训练是否已经审核过
    existing_awarded = TrainingRegistration.query.filter_by(
        training_id=training_id,
        status='awarded'
    ).first()
    
    if existing_awarded:
        return jsonify({'error': '该训练已经审核过，不能重复审核'}), 400
    
    try:
        # 更新所有考勤记录
        for record in attendance_records:
            user_id = record.get('user_id')
            attendance_status = record.get('attendance_status')
            
            if not user_id or not attendance_status:
                continue
                
            # 查找或创建考勤记录
            registration = TrainingRegistration.query.filter_by(
                training_id=training_id,
                user_id=user_id
            ).first()
            
            if not registration:
                registration = TrainingRegistration(
                    training_id=training_id,
                    user_id=user_id
                )
                db.session.add(registration)
            
            # 更新考勤状态
            registration.attendance_status = attendance_status
            registration.status = 'awarded'
            
            # 根据考勤状态发放积分
            if attendance_status == 'present':
                points = training.points
            elif attendance_status in ['late', 'early_leave']:
                points = training.points // 2  # 迟到或早退获得一半积分
            else:  # absent
                points = 0
            
            registration.points_awarded = points
            
            # 添加积分历史记录
            if points > 0:
                history = PointHistory(
                    user_id=user_id,
                    points_change=points,
                    change_type='training',
                    description=f'参加训练：{training.name}（{attendance_status}）',
                    related_id=training_id
                )
                db.session.add(history)
                
                # 更新用户总积分
                user = User.query.get(user_id)
                user.total_points += points
        
        db.session.commit()
        return jsonify({'message': '考勤提交成功'})
    
    except Exception as e:
        db.session.rollback()
        print(f'提交考勤失败: {str(e)}')  # 添加调试日志
        return jsonify({'error': str(e)}), 500

@bp.route('/options')
@login_required
def get_training_options():
    """获取训练选项列表"""
    trainings = Training.query.filter(
        Training.end_time > datetime.utcnow()
    ).order_by(Training.start_time.asc()).all()
    
    return jsonify([{
        'training_id': t.training_id,
        'name': t.name,
        'type': t.type,
        'start_time': t.start_time.isoformat(),
        'end_time': t.end_time.isoformat() if t.end_time else None
    } for t in trainings])

@bp.route('/<int:training_id>/register', methods=['POST'])
@login_required
def register_training(training_id):
    """报名训练"""
    training = Training.query.get_or_404(training_id)
    
    # 检查训练是否已结束
    if training.end_time and training.end_time < datetime.utcnow():
        return jsonify({'error': '训练已结束'}), 400
    
    # 检查是否已报名
    existing_registration = TrainingRegistration.query.filter_by(
        training_id=training_id,
        user_id=g.user.user_id
    ).first()
    
    if existing_registration:
        return jsonify({'error': '已经报名过该训练'}), 400
    
    try:
        # 创建报名记录
        registration = TrainingRegistration(
            training_id=training_id,
            user_id=g.user.user_id,
            status='registered'
        )
        db.session.add(registration)
        db.session.commit()
        
        return jsonify({'message': '报名成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:training_id>/register', methods=['DELETE'])
@login_required
def cancel_registration(training_id):
    """取消报名"""
    training = Training.query.get_or_404(training_id)
    
    # 检查训练是否已结束
    if training.end_time and training.end_time < datetime.utcnow():
        return jsonify({'error': '训练已结束'}), 400
    
    # 查找报名记录
    registration = TrainingRegistration.query.filter_by(
        training_id=training_id,
        user_id=g.user.user_id
    ).first()
    
    if not registration:
        return jsonify({'error': '未报名该训练'}), 400
    
    try:
        db.session.delete(registration)
        db.session.commit()
        return jsonify({'message': '取消报名成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:training_id>/registration')
@login_required
def get_registration_status(training_id):
    """获取报名状态"""
    registration = TrainingRegistration.query.filter_by(
        training_id=training_id,
        user_id=g.user.user_id
    ).first()
    
    return jsonify({
        'registered': registration is not None,
        'status': registration.status if registration else None
    })

@bp.route('/')
@login_required
def get_trainings():
    """获取训练列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    print('获取训练列表请求参数:', {'page': page, 'per_page': per_page})  # 添加调试日志
    
    # 获取所有训练，按开始时间倒序排列
    query = Training.query.order_by(Training.start_time.desc())
    
    # 如果不是管理员，只返回未结束的训练
    if not g.user.is_admin:
        query = query.filter(
            (Training.end_time == None) |  # 没有结束时间的训练
            (Training.end_time > datetime.utcnow())  # 未结束的训练
        )
    
    pagination = paginate(query, page, per_page)
    
    items = []
    for training in pagination.items:
        training_dict = training.to_dict()
        # 获取当前用户的报名状态
        registration = TrainingRegistration.query.filter_by(
            training_id=training.training_id,
            user_id=g.user.user_id
        ).first()
        training_dict['registered'] = registration is not None
        training_dict['status'] = registration.status if registration else None
        # 增加 reviewed 字段
        reviewed = TrainingRegistration.query.filter_by(training_id=training.training_id, status='awarded').count() > 0
        training_dict['reviewed'] = reviewed
        items.append(training_dict)
        print(f'处理训练 {training.training_id}:', training_dict)  # 添加调试日志
    
    result = {
        'items': items,
        'total': pagination.total
    }
    print('训练列表响应:', result)  # 添加调试日志
    return jsonify(result)

@bp.route('/', methods=['POST'])
@admin_required
def create_training():
    """创建训练"""
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'type', 'start_time', 'points']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段：{field}'}), 400
    
    try:
        # 创建训练记录
        training = Training(
            name=data['name'],
            type=data['type'],
            start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')) if data.get('end_time') else None,
            points=data['points'],
            created_by=g.user.user_id
        )
        db.session.add(training)
        db.session.commit()
        
        return jsonify(training.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:training_id>', methods=['PUT'])
@admin_required
def update_training(training_id):
    """更新训练"""
    training = Training.query.get_or_404(training_id)
    data = request.get_json()
    
    try:
        # 更新训练记录
        if 'name' in data:
            training.name = data['name']
        if 'type' in data:
            training.type = data['type']
        if 'start_time' in data:
            training.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        if 'end_time' in data:
            training.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')) if data['end_time'] else None
        if 'points' in data:
            training.points = data['points']
        
        db.session.commit()
        return jsonify(training.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:training_id>', methods=['DELETE'])
@admin_required
def delete_training(training_id):
    """删除训练"""
    training = Training.query.get_or_404(training_id)
    
    try:
        # 先删除关联的报名记录
        TrainingRegistration.query.filter_by(training_id=training_id).delete()
        
        # 删除关联的活动-训练记录
        EventTraining.query.filter_by(training_id=training_id).delete()
        
        # 最后删除训练记录
        db.session.delete(training)
        db.session.commit()
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f'删除训练失败: {str(e)}')  # 添加调试日志
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:training_id>/registrations')
@admin_required
def get_training_registrations(training_id):
    """获取训练报名名单"""
    training = Training.query.get_or_404(training_id)
    
    # 获取所有报名记录
    registrations = TrainingRegistration.query.filter_by(
        training_id=training_id
    ).all()
    
    # 构建报名名单
    registration_list = []
    for reg in registrations:
        user = User.query.get(reg.user_id)
        if user:
            registration_list.append({
                'user_id': user.user_id,
                'name': user.name,
                'student_id': user.student_id,
                'college': user.college,
                'status': reg.status,
                'attendance_status': reg.attendance_status,
                'points_awarded': reg.points_awarded
            })
    
    return jsonify(registration_list) 