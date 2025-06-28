from flask import Blueprint, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models import User, PointHistory, db
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, log_operation, role_required
)
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('points', __name__)

@bp.route('/history')
@jwt_required()
@handle_exceptions
@log_operation('get_point_history')
def get_point_history():
    """
    获取个人积分历史
    ---
    tags:
      - 积分
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
      - name: type
        in: query
        type: string
    responses:
      200:
        description: 积分历史列表
    """
    try:
        current_app.logger.info("Starting get_point_history")
        user_id = get_jwt_identity()
        current_app.logger.info(f"User ID from JWT: {user_id}")
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        type_filter = request.args.get('type')
        
        current_app.logger.info(f"Query params - page: {page}, per_page: {per_page}, type: {type_filter}")
        
        # 构建基础查询
        query = PointHistory.query.filter_by(user_id=user_id)
        if type_filter:
            query = query.filter_by(change_type=type_filter)
        
        # 添加排序
        query = query.order_by(PointHistory.change_time.desc())
        
        # 执行分页查询
        current_app.logger.info("Executing pagination query")
        pagination = query.paginate(page=page, per_page=per_page)
        
        # 获取记录并转换为字典
        items = []
        for item in pagination.items:
            try:
                item_dict = item.to_dict()
                current_app.logger.info(f"History item: {item_dict}")
                # 确保points_change是浮点数
                if 'points_change' in item_dict:
                    item_dict['points_change'] = float(item_dict['points_change'])
                items.append(item_dict)
            except Exception as e:
                current_app.logger.error(f"Error converting history item to dict: {str(e)}", exc_info=True)
        
        current_app.logger.info(f"Found {len(items)} history records")
        
        # 获取用户信息
        user = User.query.get(user_id)
        current_app.logger.info(f"User total points: {user.total_points if user else 'User not found'}")
        
        response_data = {
            'items': items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'total_points': float(user.total_points) if user else 0.0
        }
        
        current_app.logger.info(f"Response data: {response_data}")
        
        return APIResponse.success(data=response_data)
    except Exception as e:
        current_app.logger.error(f"Error in get_point_history: {str(e)}", exc_info=True)
        raise

@bp.route('/history/all')
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
@log_operation('get_all_point_history')
def get_all_point_history():
    """
    获取所有用户的积分历史（管理员）
    ---
    tags:
      - 积分
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
      - name: type
        in: query
        type: string
      - name: query
        in: query
        type: string
        description: 搜索关键词（用户名、姓名或学号）
    responses:
      200:
        description: 所有用户的积分历史
      403:
        description: 权限不足
    """
    try:
        current_app.logger.info("Starting get_all_point_history")
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        type_filter = request.args.get('type')
        search_query = request.args.get('query', '')
        
        current_app.logger.info(f"Query params - page: {page}, per_page: {per_page}, type: {type_filter}, query: {search_query}")
        
        query = PointHistory.query.join(User)
        if type_filter:
            query = query.filter(PointHistory.change_type == type_filter)
        
        if search_query:
            query = query.filter(
                (User.username.ilike(f'%{search_query}%')) |
                (User.name.ilike(f'%{search_query}%')) |
                (User.student_id.ilike(f'%{search_query}%'))
            )
            
        query = query.order_by(PointHistory.change_time.desc())
        
        current_app.logger.info("Executing pagination query")
        pagination = query.paginate(page=page, per_page=per_page)
        
        items = []
        for history in pagination.items:
            history_dict = history.to_dict()
            history_dict['user'] = history.user.to_dict()
            items.append(history_dict)
            
        current_app.logger.info(f"Found {len(items)} history records")
        
        return APIResponse.success(data={
            'items': items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_all_point_history: {str(e)}", exc_info=True)
        raise

@bp.route('/statistics')
@jwt_required()
@handle_exceptions
@log_operation('get_point_statistics')
def get_point_statistics():
    """
    获取积分统计信息
    ---
    tags:
      - 积分
    security:
      - Bearer: []
    responses:
      200:
        description: 积分统计信息
    """
    try:
        current_app.logger.info("Starting get_point_statistics")
        user_id = get_jwt_identity()
        current_app.logger.info(f"User ID from JWT: {user_id}")
        
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"User not found for ID: {user_id}")
            return APIResponse.error("User not found", 404)
            
        current_app.logger.info(f"Found user: {user.username}, current total_points: {user.total_points}")
        
        now = datetime.utcnow()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_day_of_last_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
        
        current_app.logger.info("Calculating monthly points")
        monthly_points_query = db.session.query(func.sum(PointHistory.points_change)).filter(
            and_(
                PointHistory.user_id == user_id,
                PointHistory.change_time >= first_day_of_month
            )
        )
        current_app.logger.info(f"Monthly points query: {monthly_points_query}")
        monthly_points = monthly_points_query.scalar() or 0
        current_app.logger.info(f"Monthly points result: {monthly_points}")
        
        current_app.logger.info("Calculating last month points")
        last_month_points_query = db.session.query(func.sum(PointHistory.points_change)).filter(
            and_(
                PointHistory.user_id == user_id,
                PointHistory.change_time >= first_day_of_last_month,
                PointHistory.change_time < first_day_of_month
            )
        )
        current_app.logger.info(f"Last month points query: {last_month_points_query}")
        last_month_points = last_month_points_query.scalar() or 0
        current_app.logger.info(f"Last month points result: {last_month_points}")
        
        # 获取最近的积分历史记录
        recent_history = PointHistory.query.filter_by(user_id=user_id)\
            .order_by(PointHistory.change_time.desc())\
            .limit(5).all()
        current_app.logger.info(f"Recent point history: {[h.to_dict() for h in recent_history]}")
        
        current_app.logger.info(f"Statistics - total: {user.total_points}, monthly: {monthly_points}, last_month: {last_month_points}")
        
        return APIResponse.success(data={
            'total_points': user.total_points,
            'monthly_points': monthly_points,
            'last_month_points': last_month_points,
            'recent_history': [h.to_dict() for h in recent_history]
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_point_statistics: {str(e)}", exc_info=True)
        raise

@bp.route('/adjust', methods=['POST'])
@jwt_required()
@role_required('admin')
@validate_json_request
@handle_exceptions
@log_operation('adjust_points')
def adjust_points():
    """
    调整用户积分（管理员）
    ---
    tags:
      - 积分
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
            points_change:
              type: number
            change_type:
              type: string
            description:
              type: string
    responses:
      200:
        description: 积分调整成功
      400:
        description: 参数错误
      403:
        description: 权限不足
      404:
        description: 用户不存在
    """
    try:
        current_app.logger.info("Starting adjust_points")
        data = request.get_json()
        current_app.logger.info(f"Request data: {data}")
        
        required_fields = ['user_id', 'points_change', 'change_type', 'description']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            current_app.logger.error(f"Validation error: {error_msg}")
            return APIResponse.error(error_msg, 400)
            
        user = User.query.get_or_404(data['user_id'])
        current_app.logger.info(f"Found user: {user.username}")
        
        try:
            history = PointHistory(
                user_id=data['user_id'],
                points_change=data['points_change'],
                change_type=data['change_type'],
                description=data['description']
            )
            db.session.add(history)
            user.total_points += data['points_change']
            db.session.commit()
            current_app.logger.info(f"Successfully adjusted points for user {user.username}")
            return APIResponse.success(msg="积分调整成功")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in adjust_points: {str(e)}", exc_info=True)
            return APIResponse.error("Failed to adjust points", 500)
    except Exception as e:
        current_app.logger.error(f"Error in adjust_points: {str(e)}", exc_info=True)
        raise 