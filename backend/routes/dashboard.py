from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models_pymysql import User, Training, Event, FlagRecord, TrainingRegistration
from utils.route_utils import APIResponse, handle_exceptions
from db_connection import db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', methods=['GET'])
@jwt_required()
@handle_exceptions
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
    current_app.logger.info("Starting to fetch dashboard data")
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    current_app.logger.info(f"Current user_id: {user_id}")
    
    # 验证用户是否存在
    user = User.get_by_id(int(user_id))
    if not user:
        current_app.logger.error(f"User not found for ID: {user_id}")
        return APIResponse.error("User not found", 401)
    
    current_app.logger.info(f"User authenticated: {user['username']}")
    
    # 获取用户总数
    total_users = len(User.list_all())
    current_app.logger.info(f"Total users: {total_users}")
    
    # 获取训练总数
    total_trainings = len(Training.list_all())
    current_app.logger.info(f"Total trainings: {total_trainings}")
    
    # 获取活动总数
    total_events = len(Event.list_all())
    current_app.logger.info(f"Total events: {total_events}")
    
    # 获取升降旗记录总数
    total_flags = len(FlagRecord.list_all())
    current_app.logger.info(f"Total flags: {total_flags}")
    
    # 获取待审核列表和数量
    pending_flags_list = FlagRecord.list_pending()
    
    # 获取需要考勤的训练报名
    pending_trainings_query = """
        SELECT tr.*, t.name as training_name, t.start_time, u.name as user_name
        FROM training_registrations tr
        JOIN trainings t ON tr.training_id = t.training_id
        JOIN users u ON tr.user_id = u.user_id
        WHERE tr.status = 'registered' AND t.start_time < NOW()
        ORDER BY t.start_time DESC
    """
    pending_trainings_list = db.execute_query(pending_trainings_query)

    pending_records_count = len(pending_flags_list) + len(pending_trainings_list)
    current_app.logger.info(f"Pending records count: {pending_records_count}")

    unified_pending_list = []
    for flag in pending_flags_list:
        unified_pending_list.append({
            'type': '升降旗', 
            'id': flag['record_id'], 
            'user_name': flag['user_name'],
            'time': flag['date'].isoformat() if isinstance(flag['date'], datetime) else flag['date'], 
            'details': f"[{flag['type'].capitalize()}]"
        })
    for reg in pending_trainings_list:
        unified_pending_list.append({
            'type': '训练', 
            'id': reg['training_id'], 
            'user_name': reg['user_name'],
            'time': reg['start_time'].isoformat() if isinstance(reg['start_time'], datetime) else reg['start_time'], 
            'details': reg['training_name']
        })
    
    # 计算总积分
    total_points_query = "SELECT SUM(total_points) as sum_points FROM users"
    total_points_result = db.execute_query(total_points_query, fetch_one=True)
    total_points = float(total_points_result['sum_points'] or 0)
    current_app.logger.info(f"Total points: {total_points}")
    
    # 获取最近的活动
    recent_events_query = "SELECT * FROM events ORDER BY time DESC LIMIT 5"
    recent_events_data = db.execute_query(recent_events_query)
    recent_events = [Event.format_dict(event) for event in recent_events_data]
    current_app.logger.info(f"Recent events count: {len(recent_events)}")
    
    # 获取最近的训练
    recent_trainings_query = "SELECT * FROM trainings ORDER BY start_time DESC LIMIT 5"
    recent_trainings_data = db.execute_query(recent_trainings_query)
    recent_trainings = [Training.format_dict(training) for training in recent_trainings_data]
    current_app.logger.info(f"Recent trainings count: {len(recent_trainings)}")
    
    # 准备响应数据
    response_data = {
        "total_users": total_users,
        "total_trainings": total_trainings,
        "total_events": total_events,
        "total_flags": total_flags,
        "pending_records": pending_records_count,
        "total_points": total_points,
        "recent_events": recent_events,
        "recent_trainings": recent_trainings,
        "pending_tasks": unified_pending_list,
    }
    
    current_app.logger.info(f"Dashboard data prepared: {response_data}")
    return APIResponse.success(data=response_data) 