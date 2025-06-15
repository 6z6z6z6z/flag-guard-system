from flask import Blueprint, request, current_app, jsonify
from datetime import datetime
from models import Training, TrainingRegistration, User, PointHistory, db, EventTraining
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, log_operation, role_required
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

bp = Blueprint('trainings', __name__)

@bp.route('/review')
@jwt_required()
@role_required('admin')
@handle_exceptions
@log_operation('get_trainings_for_review')
def get_trainings_for_review():
    """获取训练列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    query = Training.query
    if status == 'pending':
        query = query.filter(
            Training.end_time < datetime.utcnow(),
            ~Training.training_id.in_(
                db.session.query(TrainingRegistration.training_id)
                .filter(TrainingRegistration.status == 'awarded')
                .distinct()
            )
        )
    elif status == 'reviewed':
        query = query.filter(
            Training.training_id.in_(
                db.session.query(TrainingRegistration.training_id)
                .filter(TrainingRegistration.status == 'awarded')
                .distinct()
            )
        )
    query = query.order_by(Training.start_time.desc())
    pagination = query.paginate(page=page, per_page=per_page)
    items = []
    for training in pagination.items:
        training_dict = training.to_dict()
        training_dict['reviewed'] = any(r.status == 'awarded' for r in training.registrations)
        if 'type' in training_dict:
            del training_dict['type']
        items.append(training_dict)
    return APIResponse.success(data={
        'items': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@bp.route('/<int:training_id>/attendance')
@jwt_required()
@role_required('admin')
@handle_exceptions
@log_operation('get_attendance_list')
def get_attendance_list(training_id):
    """获取训练考勤名单"""
    training = Training.query.get_or_404(training_id)
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
    return APIResponse.success(data=attendance_list)

@bp.route('/<int:training_id>/attendance', methods=['POST'])
@jwt_required()
@role_required('admin')
@validate_json_request
@handle_exceptions
@log_operation('submit_attendance')
def submit_attendance(training_id):
    """提交训练考勤"""
    training = Training.query.get_or_404(training_id)
    data = request.get_json()
    attendance_records = data.get('attendance_records', [])
    if not isinstance(attendance_records, list):
        return APIResponse.error('参数格式错误', 400)
    
    awarded_registrations = TrainingRegistration.query.filter_by(
        training_id=training_id, 
        status='awarded'
    ).all()
    awarded_user_ids = {reg.user_id for reg in awarded_registrations}

    try:
        new_histories = []
        updated_users = []

        for record in attendance_records:
            user_id = record.get('user_id')
            attendance_status = record.get('attendance_status')
            if not user_id or not attendance_status:
                continue

            if user_id in awarded_user_ids:
                current_app.logger.warning(
                    f'Skipping user {user_id} for training {training_id}: already awarded.'
                )
                continue

            registration = TrainingRegistration.query.filter_by(
                training_id=training_id,
                user_id=user_id
            ).first()
            if not registration:
                registration = TrainingRegistration(
                    training_id=training_id,
                    user_id=user_id,
                    status='registered'
                )
                db.session.add(registration)
            
            registration.attendance_status = attendance_status
            registration.status = 'awarded'
            
            if attendance_status == 'present':
                points = float(training.points)
            elif attendance_status in ['late', 'early_leave']:
                points = float(training.points) / 2
            else:
                points = 0.0
            
            registration.points_awarded = points
            
            if points > 0:
                user = User.query.get(user_id)
                if user:
                    user.total_points = (user.total_points or 0) + points
                    history = PointHistory(
                        user_id=user_id,
                        points_change=points,
                        change_type='training',
                        description=f'参加训练：{training.name}（{attendance_status}）',
                        related_id=training_id
                    )
                    new_histories.append(history)
                    updated_users.append(user)
        
        if new_histories:
            db.session.add_all(new_histories)
        
        db.session.commit()
        return APIResponse.success(msg='考勤提交成功')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'提交考勤失败: {str(e)}', exc_info=True)
        return APIResponse.error('提交考勤失败', 500)

@bp.route('/options')
@jwt_required()
@handle_exceptions
@log_operation('get_training_options')
def get_training_options():
    """获取训练选项列表"""
    trainings = Training.query.filter(
        Training.end_time > datetime.utcnow()
    ).order_by(Training.start_time.asc()).all()
    return APIResponse.success(data=[{
        'training_id': t.training_id,
        'name': t.name,
        'start_time': t.start_time.isoformat(),
        'end_time': t.end_time.isoformat() if t.end_time else None
    } for t in trainings])

@bp.route('/<int:training_id>/register', methods=['POST'])
@jwt_required()
@handle_exceptions
@log_operation('register_training')
def register_training(training_id):
    """报名训练"""
    training = Training.query.get_or_404(training_id)
    if training.end_time and training.end_time < datetime.utcnow():
        return APIResponse.error('训练已结束', 400)
    user_id = get_jwt_identity()
    existing_registration = TrainingRegistration.query.filter_by(
        user_id=user_id,
        training_id=training_id
    ).first()
    if existing_registration:
        return APIResponse.error(msg="您已报名此训练", code=409)
    try:
        registration = TrainingRegistration(
            user_id=user_id,
            training_id=training_id,
            status='registered'
        )
        db.session.add(registration)
        db.session.commit()
        return APIResponse.success(msg='报名成功')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'报名失败: {str(e)}')
        return APIResponse.error(str(e), 500)

@bp.route('/<int:training_id>/register', methods=['DELETE'])
@jwt_required()
@handle_exceptions
@log_operation('cancel_registration')
def cancel_registration(training_id):
    """取消报名"""
    current_app.logger.info(f'开始取消报名训练 {training_id}')
    current_user_id = get_jwt_identity()
    current_app.logger.info(f'当前用户ID: {current_user_id}')
    
    training = Training.query.get_or_404(training_id)
    current_app.logger.info(f'找到训练: {training.name}')
    
    if training.end_time and training.end_time < datetime.utcnow():
        current_app.logger.warning(f'训练 {training_id} 已结束')
        return APIResponse.error('训练已结束', 400)
    
    registration = TrainingRegistration.query.filter_by(
        training_id=training_id,
        user_id=current_user_id
    ).first()
    
    if not registration:
        current_app.logger.warning(f'用户 {current_user_id} 未报名训练 {training_id}')
        return APIResponse.error('未报名该训练', 400)
    
    try:
        current_app.logger.info(f'删除报名记录: {registration.registration_id}')
        db.session.delete(registration)
        db.session.commit()
        current_app.logger.info(f'成功取消报名训练 {training_id}')
        return APIResponse.success(msg='取消报名成功')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'取消报名失败: {str(e)}')
        return APIResponse.error('取消报名失败', 500)

@bp.route('/<int:training_id>/registration')
@jwt_required()
@handle_exceptions
@log_operation('get_registration_status')
def get_registration_status(training_id):
    """获取报名状态"""
    registration = TrainingRegistration.query.filter_by(
        training_id=training_id,
        user_id=get_jwt_identity()
    ).first()
    return APIResponse.success(data={
        'registered': registration is not None,
        'status': registration.status if registration else None
    })

@bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@handle_exceptions
@log_operation('get_trainings')
def get_trainings():
    """获取训练列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    current_user_id = get_jwt_identity()
    
    # 获取当前用户
    current_user = User.query.get(current_user_id)
    if not current_user:
        return APIResponse.error('用户不存在', 404)
    
    query = Training.query

    # 如果不是管理员，只显示未结束的训练
    if not current_user.is_admin:
        query = query.filter(Training.end_time > datetime.utcnow())
    
    query = query.order_by(Training.start_time.desc())
    pagination = query.paginate(page=page, per_page=per_page)
    
    items = []
    for training in pagination.items:
        training_dict = training.to_dict()
        
        # 统一检查当前用户的报名状态
        registration = TrainingRegistration.query.filter_by(
            training_id=training.training_id,
            user_id=current_user_id
        ).first()
        training_dict['is_registered'] = registration is not None
        
        items.append(training_dict)
    
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
@log_operation('create_training')
def create_training():
    """创建训练"""
    try:
        # 记录请求信息
        current_app.logger.info("=== Create Training Request ===")
        current_app.logger.info(f"Request headers: {dict(request.headers)}")
        current_app.logger.info(f"Request data: {request.get_json()}")
        
        # 获取当前用户信息
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        current_app.logger.info(f"Current user: {current_user.username} (ID: {user_id}, Role: {current_user.role})")
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'start_time', 'end_time', 'points', 'location']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            current_app.logger.warning(f"Missing required fields: {error_msg}")
            return APIResponse.error(error_msg, 400)
        
        # 创建训练记录
        try:
            training = Training(
                name=data['name'],
                start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
                end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')),
                points=float(data['points']),
                location=data['location'],
                created_by=user_id
            )
            db.session.add(training)
            db.session.commit()
            current_app.logger.info(f"Training created successfully: {training.name} (ID: {training.training_id})")
            return APIResponse.success(data=training.to_dict(), msg='训练创建成功')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create training: {str(e)}")
            return APIResponse.error(str(e), 500)
    except Exception as e:
        current_app.logger.error(f"Unexpected error in create_training: {str(e)}")
        return APIResponse.error(str(e), 500)

@bp.route('/<int:training_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_training(training_id):
    """更新训练"""
    try:
        # 获取训练对象
        training = Training.query.get_or_404(training_id)
        data = request.get_json()
        
        # 打印详细的调试信息
        print(f"=== 开始更新训练 {training_id} ===")
        print(f"接收到的更新数据: {data}")
        print(f"更新前的训练数据: {training.to_dict()}")
        
        # 验证必要字段
        if not data:
            return jsonify({
                'code': 400,
                'message': '请求数据不能为空'
            }), 400
            
        # 更新基本信息
        try:
            if 'name' in data:
                training.name = data['name']
            if 'start_time' in data:
                training.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            if 'end_time' in data:
                training.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            if 'points' in data:
                training.points = data['points']
            if 'location' in data:
                print(f"更新地点字段: {data['location']}")
                training.location = data['location']
            
            # 打印更新后的数据
            print(f"更新后的训练数据: {training.to_dict()}")
            
            # 提交到数据库
            db.session.commit()
            
            # 验证数据是否真的保存成功
            db.session.refresh(training)
            print(f"数据库刷新后的训练数据: {training.to_dict()}")
            
            # 返回更新后的数据
            response_data = training.to_dict()
            print(f"返回给前端的数据: {response_data}")
            
            return jsonify({
                'code': 200,
                'message': '更新成功',
                'data': response_data
            })
            
        except ValueError as e:
            print(f"数据格式错误: {str(e)}")
            return jsonify({
                'code': 400,
                'message': f'数据格式错误: {str(e)}'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        print(f"更新训练失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'更新失败: {str(e)}'
        }), 500

@bp.route('/<int:training_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def delete_training(training_id):
    """(管理员)删除训练"""
    training = Training.query.get(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)

    db.session.delete(training)
    db.session.commit()
    return APIResponse.success(msg='训练删除成功')

@bp.route('/<int:training_id>/registrations')
@jwt_required()
@role_required('admin')
@handle_exceptions
@log_operation('get_training_registrations')
def get_training_registrations(training_id):
    """获取训练报名人员名单"""
    training = Training.query.get_or_404(training_id)
    registrations = TrainingRegistration.query.filter_by(training_id=training_id).all()
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
            'status': reg.status,
            'attendance_status': reg.attendance_status,
            'points_awarded': reg.points_awarded,
            'created_at': reg.created_at.isoformat() if reg.created_at else None
        })
    return APIResponse.success(data=registration_list)

@bp.route('/debug', methods=['GET'])
@jwt_required()
@role_required('admin')
def debug_trainings():
    """调试接口：获取训练数据"""
    trainings = Training.query.all()
    result = []
    for t in trainings:
        result.append({
            'training_id': t.training_id,
            'name': t.name,
            'location': t.location,
            'start_time': t.start_time.isoformat() if t.start_time else None,
            'end_time': t.end_time.isoformat() if t.end_time else None,
            'points': t.points,
            'created_by': t.created_by
        })
    return APIResponse.success(data=result)

@bp.route('/<int:training_id>/registrations/attendance', methods=['POST'])
@jwt_required()
@role_required('admin')
@validate_json_request
@handle_exceptions
@log_operation('confirm_attendance')
def confirm_attendance(training_id):
    """确认考勤并添加积分"""
    training = Training.query.get_or_404(training_id)
    data = request.get_json()
    updates = data.get('updates', [])
    
    try:
        for update in updates:
            registration_id = update.get('registration_id')
            new_status = update.get('attendance_status')
            new_points = float(update.get('points_awarded', 0))

            registration = TrainingRegistration.query.get(registration_id)
            if not registration or registration.training_id != training_id:
                continue

            user = User.query.get(registration.user_id)
            if not user:
                continue

            # 1. 查找并删除旧的积分历史记录，同时从用户总分中减去旧积分
            old_history = PointHistory.query.filter_by(
                user_id=user.user_id,
                change_type='training_award',
                related_id=training_id
            ).first()

            if old_history:
                user.total_points -= old_history.points_change
                db.session.delete(old_history)

            # 2. 更新报名记录
            registration.attendance_status = new_status
            registration.points_awarded = new_points

            # 3. 如果有新积分，则添加到用户总分并创建新的历史记录
            if new_points > 0:
                user.total_points += new_points
                new_history = PointHistory(
                    user_id=user.user_id,
                    points_change=new_points,
                    change_type='training_award',
                    description=f"参加训练: {training.name}",
                    related_id=training_id
                )
                db.session.add(new_history)

        # 标记训练为已审核
        training.status = 'ended'
        db.session.commit()
        return APIResponse.success(msg='考勤确认成功')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'确认考勤失败: {str(e)}')
        return APIResponse.error(str(e), 500)

@bp.route('/registrations/<int:registration_id>/reject', methods=['POST'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def reject_registration(registration_id):
    """(管理员)拒绝报名"""
    registration = TrainingRegistration.query.get(registration_id)
    if not registration:
        return APIResponse.error(msg="报名记录不存在", code=404)

    if registration.status != 'registered':
        return APIResponse.error(msg="该报名记录已处理", code=400)

    # For now, we just delete the rejected registration.
    # Alternatively, we could set a 'rejected' status.
    db.session.delete(registration)
    db.session.commit()
    
    return APIResponse.success(msg="已拒绝并删除报名记录")

@bp.route('/<int:training_id>/award', methods=['POST'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def award_points_for_training(training_id):
    """为参与训练的成员发放积分"""
    training = Training.query.get(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)

    # Implementation of award_points_for_training function
    # This function should be implemented to handle the logic for awarding points to training participants
    return APIResponse.success(msg='积分发放逻辑未实现')

@bp.route('/<int:training_id>/registrations', methods=['GET'])
@jwt_required()
@role_required('admin')
@handle_exceptions
@log_operation('get_training_registrations')
def get_training_registrations_new(training_id):
    """获取训练报名人员名单"""
    training = Training.query.get_or_404(training_id)
    registrations = TrainingRegistration.query.filter_by(training_id=training_id).all()
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
            'status': reg.status,
            'attendance_status': reg.attendance_status,
            'points_awarded': reg.points_awarded,
            'created_at': reg.created_at.isoformat() if reg.created_at else None
        })
    return APIResponse.success(data=registration_list)

@bp.route('/registrations/<int:registration_id>/confirm', methods=['POST'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def confirm_registration(registration_id):
    """确认报名"""
    registration = TrainingRegistration.query.get(registration_id)
    if not registration:
        return APIResponse.error("报名记录不存在", 404)

    registration.attendance_status = status
    if registration.status == 'registered':
        registration.status = 'confirmed'
        
    db.session.commit()
    return APIResponse.success({
        'registration_id': registration.registration_id,
        'attendance_status': registration.attendance_status
    }) 