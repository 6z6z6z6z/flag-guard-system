from flask import Blueprint, request, current_app
from datetime import datetime
from models_pymysql import Training, TrainingRegistration, User, PointHistory, EventTraining
from db_connection import db
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, role_required
)
from utils.time_utils import TimeUtils
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('trainings', __name__)

@bp.route('/review')
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def get_trainings_for_review():
    """获取训练列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    # 获取所有训练
    all_trainings = Training.list_all()
    
    current_beijing_time = TimeUtils.now_beijing()
    
    # 过滤训练
    filtered_trainings = []
    for training in all_trainings:
        training_end_time = TimeUtils.from_db_to_beijing(training.get('end_time'))
        
        # 获取该训练的所有报名
        registrations = TrainingRegistration.list_by_training(training.get('training_id'))
        awarded_status = any(r.get('status') == 'awarded' for r in registrations)
        
        if status == 'pending':
            if training_end_time and training_end_time < current_beijing_time and not awarded_status:
                filtered_trainings.append(training)
        elif status == 'reviewed':
            if awarded_status:
                filtered_trainings.append(training)
        else:
            filtered_trainings.append(training)
    
    # 按开始时间降序排序
    filtered_trainings.sort(
        key=lambda x: TimeUtils.from_db_to_beijing(x.get('start_time')) or TimeUtils.now_beijing(), 
        reverse=True
    )
    
    # 分页
    total = len(filtered_trainings)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    current_page_items = filtered_trainings[start_idx:end_idx] if start_idx < total else []
    
    # 格式化输出
    items = []
    for training in current_page_items:
        training_dict = Training.format_dict(training)
        
        # 获取该训练的所有报名
        registrations = TrainingRegistration.list_by_training(training.get('training_id'))
        training_dict['reviewed'] = any(r.get('status') == 'awarded' for r in registrations)
        
        if 'type' in training_dict:
            del training_dict['type']
        items.append(training_dict)
    
    return APIResponse.success(data={
        'items': items,
        'total': total,
        'pages': total_pages,
        'current_page': page
    })

@bp.route('/<int:training_id>/attendance')
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def get_attendance_list(training_id):
    """获取训练考勤名单"""
    training = Training.get_by_id(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)
    
    registrations = TrainingRegistration.list_by_training(training_id)
    attendance_list = []
    
    for registration in registrations:
        user_id = registration.get('user_id')
        user_name = registration.get('name')
        student_id = registration.get('student_id')
        college = registration.get('college')
        
        attendance_list.append({
            'user_id': user_id,
            'name': user_name,
            'student_id': student_id,
            'college': college,
            'phone_number': registration.get('phone_number'),
            'attendance_status': registration.get('attendance_status'),
            'status': registration.get('status'),
            'points_awarded': registration.get('points_awarded')
        })
    
    return APIResponse.success(data=attendance_list)

@bp.route('/<int:training_id>/attendance', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
def submit_attendance(training_id):
    """提交训练考勤"""
    training = Training.get_by_id(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)
    
    data = request.get_json()
    attendance_records = data.get('attendance_records', [])
    if not isinstance(attendance_records, list):
        return APIResponse.error('参数格式错误', 400)
    
    # 获取所有已经获得积分的报名记录
    registrations = TrainingRegistration.list_by_training(training_id)
    awarded_user_ids = {reg.get('user_id') for reg in registrations if reg.get('status') == 'awarded'}

    try:
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

            # 查找用户的报名记录
            registration = None
            for reg in registrations:
                if reg.get('user_id') == user_id:
                    registration = reg
                    break
            
            if not registration:
                # 如果没有报名记录，创建一个
                registration = TrainingRegistration.create(
                    training_id=training_id,
                    user_id=user_id,
                    status='registered'
                )
                registration_id = registration.get('registration_id')
            else:
                registration_id = registration.get('registration_id')
            
            # 计算积分
            if attendance_status == 'present':
                points = float(training.get('points', 0))
            elif attendance_status in ['late', 'early_leave']:
                points = float(training.get('points', 0)) / 2
            else:
                points = 0.0
            
            # 更新考勤状态和积分
            TrainingRegistration.update_status(
                registration_id=registration_id,
                status='awarded',
                attendance_status=attendance_status
            )
            
            if points > 0:
                # 添加积分
                TrainingRegistration.award_points(registration_id, points)
                
                # 更新用户积分
                User.add_points(
                    user_id=user_id,
                    points=points,
                    change_type='training',
                    description=f'参加训练：{training.get("name")}（{attendance_status}）',
                    related_id=training_id
                )
        
        return APIResponse.success(msg='考勤提交成功')
    except Exception as e:
        current_app.logger.error(f'提交考勤失败: {str(e)}', exc_info=True)
        return APIResponse.error('提交考勤失败', 500)

@bp.route('/options')
@jwt_required()
@handle_exceptions
def get_training_options():
    """获取训练选项列表"""
    # 获取所有训练
    all_trainings = Training.list_all()
    current_beijing_time = TimeUtils.now_beijing()
    
    # 过滤未来的训练
    future_trainings = []
    for training in all_trainings:
        end_time = TimeUtils.from_db_to_beijing(training.get('end_time'))
        
        if end_time and end_time > current_beijing_time:
            future_trainings.append(training)
    
    # 按开始时间升序排序
    future_trainings.sort(
        key=lambda x: TimeUtils.from_db_to_beijing(x.get('start_time')) or TimeUtils.now_beijing()
    )
    
    # 格式化输出
    return APIResponse.success(data=[{
        'training_id': t.get('training_id'),
        'name': t.get('name'),
        'start_time': TimeUtils.format_for_frontend_iso(t.get('start_time')),
        'end_time': TimeUtils.format_for_frontend_iso(t.get('end_time'))
    } for t in future_trainings])

@bp.route('/<int:training_id>/register', methods=['POST'])
@jwt_required()
@handle_exceptions
def register_training(training_id):
    """报名训练"""
    training = Training.get_by_id(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)
    
    # 从数据库读取的时间是UTC时间，需要先转换为北京时间
    end_time = TimeUtils.from_db_to_beijing(training.get('end_time'))
    current_beijing_time = TimeUtils.now_beijing()
    
    if end_time and end_time < current_beijing_time:
        return APIResponse.error('训练已结束', 400)
    
    user_id = int(get_jwt_identity())
    existing_registration = TrainingRegistration.get_by_training_and_user(training_id, user_id)
    
    if existing_registration:
        return APIResponse.error(msg="您已报名此训练", code=409)
    
    try:
        TrainingRegistration.create(
            user_id=user_id,
            training_id=training_id,
            status='registered'
        )
        return APIResponse.success(msg='报名成功')
    except Exception as e:
        current_app.logger.error(f'报名失败: {str(e)}')
        return APIResponse.error(str(e), 500)

@bp.route('/<int:training_id>/register', methods=['DELETE'])
@jwt_required()
@handle_exceptions
def cancel_registration(training_id):
    """取消报名"""
    current_app.logger.info(f'开始取消报名训练 {training_id}')
    current_user_id = int(get_jwt_identity())
    current_app.logger.info(f'当前用户ID: {current_user_id}')
    
    training = Training.get_by_id(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)
        
    current_app.logger.info(f'找到训练: {training.get("name")}')
    
    end_time = TimeUtils.from_db_to_beijing(training.get('end_time'))
    current_beijing_time = TimeUtils.now_beijing()
    
    if end_time and end_time < current_beijing_time:
        current_app.logger.warning(f'训练 {training_id} 已结束')
        return APIResponse.error('训练已结束', 400)
    
    registration = TrainingRegistration.get_by_training_and_user(training_id, current_user_id)
    
    if not registration:
        current_app.logger.warning(f'用户 {current_user_id} 未报名训练 {training_id}')
        return APIResponse.error('未报名该训练', 400)
    
    try:
        current_app.logger.info(f'删除报名记录: {registration.get("registration_id")}')
        TrainingRegistration.delete(registration.get('registration_id'))
        current_app.logger.info(f'成功取消报名训练 {training_id}')
        return APIResponse.success(msg='取消报名成功')
    except Exception as e:
        current_app.logger.error(f'取消报名失败: {str(e)}')
        return APIResponse.error('取消报名失败', 500)

@bp.route('/<int:training_id>/registration')
@jwt_required()
@handle_exceptions
def get_registration_status(training_id):
    """获取个人对某个训练的报名状态"""
    user_id = int(get_jwt_identity())
    registration = TrainingRegistration.get_by_training_and_user(training_id, user_id)
    
    if not registration:
        return APIResponse.success(data={'registered': False})
    
    return APIResponse.success(data={
        'registered': True,
        'registration_id': registration.get('registration_id'),
        'status': registration.get('status'),
        'attendance_status': registration.get('attendance_status'),
        'points_awarded': registration.get('points_awarded')
    })

@bp.route('/', methods=['GET'], strict_slashes=False)
@jwt_required()
@handle_exceptions
def get_trainings():
    """获取训练列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    current_user_id = int(get_jwt_identity())
    
    # 获取所有训练 (已在数据库层面按start_time降序排序)
    all_trainings = Training.list_all()
    
    # 分页
    total = len(all_trainings)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    current_page_items = all_trainings[start_idx:end_idx] if start_idx < total else []
    
    # 获取用户的报名状态
    user_registrations = TrainingRegistration.list_by_user(current_user_id)
    user_registrations_dict = {r.get('training_id'): r for r in user_registrations}
    
    # 格式化输出
    items = []
    for training in current_page_items:
        training_dict = Training.format_dict(training)
        training_id = training.get('training_id')
        registration = user_registrations_dict.get(training_id)
        
        training_dict['is_registered'] = registration is not None
        training_dict['registration_status'] = registration.get('status') if registration else None
        training_dict['attendance_status'] = registration.get('attendance_status') if registration else None
        
        items.append(training_dict)
    
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
def create_training():
    """创建训练"""
    data = request.get_json()
    required_fields = ['name', 'start_time', 'end_time', 'points', 'location']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    try:
        # 解析前端传来的北京时间
        start_time = TimeUtils.parse_frontend_time(data['start_time'])
        end_time = TimeUtils.parse_frontend_time(data['end_time'])
        
        if not start_time or not end_time:
            return APIResponse.error('时间格式无效', 400)
        
        if start_time >= end_time:
            return APIResponse.error('开始时间必须早于结束时间', 400)
        
        created_by = get_jwt_identity()
        
        training = Training.create(
            name=data['name'],
            start_time=start_time,
            end_time=end_time,
            points=data['points'],
            location=data['location'],
            created_by=created_by
        )
        
        return APIResponse.success(
            data=training,
            msg='训练创建成功',
            code=201
        )
    except ValueError as e:
        return APIResponse.error(f'日期格式无效: {str(e)}', 400)
    except Exception as e:
        current_app.logger.error(f'创建训练失败: {str(e)}', exc_info=True)
        return APIResponse.error('创建训练失败', 500)

@bp.route('/<int:training_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
def update_training(training_id):
    """更新训练信息"""
    training = Training.get_by_id(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)
    
    data = request.get_json()
    required_fields = ['name', 'start_time', 'end_time', 'points', 'location']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    try:
        # 解析前端传来的北京时间
        start_time = TimeUtils.parse_frontend_time(data['start_time'])
        end_time = TimeUtils.parse_frontend_time(data['end_time'])
        
        if not start_time or not end_time:
            return APIResponse.error('时间格式无效', 400)
        
        if start_time >= end_time:
            return APIResponse.error('开始时间必须早于结束时间', 400)
        
        status = data.get('status', training.get('status', 'scheduled'))
        
        updated_training = Training.update(
            training_id=training_id,
            name=data['name'],
            start_time=start_time,
            end_time=end_time,
            points=data['points'],
            location=data['location'],
            status=status
        )
        
        return APIResponse.success(
            data=updated_training,
            msg='训练更新成功'
        )
    except ValueError as e:
        return APIResponse.error(f'日期格式无效: {str(e)}', 400)
    except Exception as e:
        current_app.logger.error(f'更新训练失败: {str(e)}', exc_info=True)
        return APIResponse.error('更新训练失败', 500)

@bp.route('/<int:training_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def delete_training(training_id):
    """删除训练"""
    result = Training.delete(training_id)
    if result:
        return APIResponse.success(msg='训练删除成功')
    return APIResponse.error('训练不存在或删除失败', 404)

@bp.route('/<int:training_id>/registrations')
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def get_training_registrations(training_id):
    """获取训练报名列表"""
    registrations = TrainingRegistration.list_by_training(training_id)
    return APIResponse.success(data=registrations)

@bp.route('/debug', methods=['GET'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def debug_trainings():
    """调试训练数据"""
    all_trainings = Training.list_all()
    all_registrations = []
    
    for training in all_trainings:
        training_id = training.get('training_id')
        registrations = TrainingRegistration.list_by_training(training_id)
        
        all_registrations.extend([{
            'training_id': training_id,
            'training_name': training.get('name'),
            'registration_id': r.get('registration_id'),
            'user_id': r.get('user_id'),
            'user_name': r.get('name'),
            'phone_number': r.get('phone_number'),
            'student_id': r.get('student_id'),
            'college': r.get('college'),
            'status': r.get('status'),
            'attendance_status': r.get('attendance_status'),
            'points_awarded': r.get('points_awarded')
        } for r in registrations])
    
    return APIResponse.success(data={
        'trainings': all_trainings,
        'registrations': all_registrations
    })

@bp.route('/<int:training_id>/registrations/attendance', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
def confirm_attendance(training_id):
    """确认训练出勤情况"""
    data = request.get_json()
    attendance_records = data.get('records', [])
    if not isinstance(attendance_records, list):
        return APIResponse.error('参数格式错误', 400)
    
    training = Training.get_by_id(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)
    
    try:
        for record in attendance_records:
            registration_id = record.get('registration_id')
            attendance_status = record.get('attendance_status')
            
            if not registration_id or not attendance_status:
                continue
            
            # 更新考勤状态
            TrainingRegistration.update_status(
                registration_id=registration_id,
                status='attended',
                attendance_status=attendance_status
            )
        
        return APIResponse.success(msg='考勤确认成功')
    except Exception as e:
        current_app.logger.error(f'确认考勤失败: {str(e)}', exc_info=True)
        return APIResponse.error('确认考勤失败', 500)

@bp.route('/registrations/<int:registration_id>/reject', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def reject_registration(registration_id):
    """拒绝训练报名"""
    registration = TrainingRegistration.get_by_id(registration_id)
    if not registration:
        return APIResponse.error('报名记录不存在', 404)
    
    try:
        TrainingRegistration.update_status(
            registration_id=registration_id,
            status='rejected',
            attendance_status=None
        )
        return APIResponse.success(msg='拒绝报名成功')
    except Exception as e:
        current_app.logger.error(f'拒绝报名失败: {str(e)}')
        return APIResponse.error('拒绝报名失败', 500)

@bp.route('/<int:training_id>/award', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def award_points_for_training(training_id):
    """为训练参与者发放积分"""
    training = Training.get_by_id(training_id)
    if not training:
        return APIResponse.error('训练不存在', 404)
    
    try:
        # 获取训练的所有参与者
        registrations = TrainingRegistration.list_by_training(training_id)
        attendees = [r for r in registrations if r.get('attendance_status') in ['present', 'late', 'early_leave']]
        
        awarded_count = 0
        for attendee in attendees:
            registration_id = attendee.get('registration_id')
            attendance_status = attendee.get('attendance_status')
            user_id = attendee.get('user_id')
            
            # 如果已经发过积分，跳过
            if attendee.get('status') == 'awarded':
                continue
            
            # 计算积分
            if attendance_status == 'present':
                points = float(training.get('points', 0))
            elif attendance_status in ['late', 'early_leave']:
                points = float(training.get('points', 0)) / 2
            else:
                continue
            
            # 记录积分
            TrainingRegistration.award_points(registration_id, points)
            
            # 更新用户积分
            User.add_points(
                user_id=user_id,
                points=points,
                change_type='training',
                description=f'参加训练：{training.get("name")}（{attendance_status}）',
                related_id=training_id
            )
            
            awarded_count += 1
        
        return APIResponse.success(
            data={'awarded_count': awarded_count},
            msg=f'成功为{awarded_count}名参与者发放积分'
        )
    except Exception as e:
        current_app.logger.error(f'发放积分失败: {str(e)}')
        return APIResponse.error('发放积分失败', 500)

@bp.route('/<int:training_id>/registrations', methods=['GET'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def get_training_registrations_new(training_id):
    """获取训练报名列表（分页版本）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取所有报名
    all_registrations = TrainingRegistration.list_by_training(training_id)
    
    # 分页
    total = len(all_registrations)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    # 获取当前页的记录
    current_page_items = all_registrations[start_idx:end_idx] if start_idx < total else []
    
    return APIResponse.success(data={
        'items': current_page_items,
        'total': total,
        'pages': total_pages,
        'current_page': page
    })

@bp.route('/registrations/<int:registration_id>/confirm', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
def confirm_registration(registration_id):
    """确认训练报名"""
    registration = TrainingRegistration.get_by_id(registration_id)
    if not registration:
        return APIResponse.error('报名记录不存在', 404)
    
    try:
        TrainingRegistration.update_status(
            registration_id=registration_id,
            status='confirmed',
            attendance_status=None
        )
        return APIResponse.success(msg='确认报名成功')
    except Exception as e:
        current_app.logger.error(f'确认报名失败: {str(e)}')
        return APIResponse.error('确认报名失败', 500)