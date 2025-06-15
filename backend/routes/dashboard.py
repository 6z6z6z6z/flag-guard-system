from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Training, Event, FlagRecord, TrainingRegistration, db
from sqlalchemy import func
from utils.route_utils import APIResponse
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """
    获取仪表盘数据
    ---
    tags:
      - 仪表盘
    security:
      - Bearer: []
    responses:
      200:
        description: 成功获取仪表盘数据
    """
    try:
        current_app.logger.info("Starting to fetch dashboard data")
        
        # 获取当前用户ID
        user_id = get_jwt_identity()
        current_app.logger.info(f"Current user_id: {user_id}")
        
        # 验证用户是否存在
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User not found for ID: {user_id}")
            return APIResponse.error("User not found", 401)
        
        current_app.logger.info(f"User authenticated: {user.username}")
        
        # 获取用户总数
        total_users = User.query.count()
        current_app.logger.info(f"Total users: {total_users}")
        
        # 获取训练总数
        total_trainings = Training.query.count()
        current_app.logger.info(f"Total trainings: {total_trainings}")
        
        # 获取活动总数
        total_events = Event.query.count()
        current_app.logger.info(f"Total events: {total_events}")
        
        # 获取升降旗记录总数
        total_flags = FlagRecord.query.count()
        current_app.logger.info(f"Total flags: {total_flags}")
        
        # 获取待审核列表和数量
        pending_flags_list = FlagRecord.query.filter_by(status='pending').order_by(FlagRecord.date.desc()).all()
        
        now = datetime.utcnow()
        pending_trainings_list = TrainingRegistration.query.join(Training).filter(
            TrainingRegistration.status == 'registered',
            Training.start_time < now
        ).order_by(Training.start_time.desc()).all()

        pending_records_count = len(pending_flags_list) + len(pending_trainings_list)
        current_app.logger.info(f"Pending records count: {pending_records_count}")

        unified_pending_list = []
        for flag in pending_flags_list:
            unified_pending_list.append({
                'type': '升降旗', 'id': flag.record_id, 'user_name': flag.user.name,
                'time': flag.date.isoformat(), 'details': f"[{flag.type.capitalize()}]"
            })
        for reg in pending_trainings_list:
            unified_pending_list.append({
                'type': '训练', 'id': reg.training_id, 'user_name': reg.user.name,
                'time': reg.training.start_time.isoformat(), 'details': reg.training.name
            })
        
        # 计算总积分
        total_points = db.session.query(func.sum(User.total_points)).scalar() or 0
        current_app.logger.info(f"Total points: {total_points}")
        
        # 获取最近的活动
        recent_events = Event.query.order_by(Event.time.desc()).limit(5).all()
        current_app.logger.info(f"Recent events count: {len(recent_events)}")
        
        # 获取最近的训练
        recent_trainings = Training.query.order_by(Training.start_time.desc()).limit(5).all()
        current_app.logger.info(f"Recent trainings count: {len(recent_trainings)}")
        
        # 获取最近的升降旗记录
        recent_flags = FlagRecord.query.order_by(FlagRecord.date.desc()).limit(5).all()
        current_app.logger.info(f"Recent flags count: {len(recent_flags)}")
        
        # 准备响应数据
        response_data = {
            "total_users": total_users,
            "total_trainings": total_trainings,
            "total_events": total_events,
            "total_flags": total_flags,
            "pending_records": pending_records_count,
            "total_points": float(total_points),
            "recent_events": [event.to_dict() for event in recent_events],
            "recent_trainings": [training.to_dict() for training in recent_trainings],
            "pending_tasks": unified_pending_list,
        }
        
        current_app.logger.info(f"Dashboard data prepared: {response_data}")
        return APIResponse.success(data=response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in get_dashboard_data: {str(e)}", exc_info=True)
        return APIResponse.error("Failed to fetch dashboard data", 500) 