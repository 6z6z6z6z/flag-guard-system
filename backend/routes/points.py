from flask import Blueprint, request, current_app
from datetime import datetime, timedelta
from models_pymysql import User, PointHistory
from db_connection import db
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, role_required
)
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('points', __name__)

@bp.route('/history', methods=['GET'])
@jwt_required()
@handle_exceptions
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
        user_id = int(get_jwt_identity())
        current_app.logger.info(f"User ID from JWT: {user_id}")
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        type_filter = request.args.get('type')
        
        current_app.logger.info(f"Query params - page: {page}, per_page: {per_page}, type: {type_filter}")
        
        # 获取积分历史
        history_list = PointHistory.list_by_user(user_id)
        current_app.logger.info(f"Retrieved {len(history_list)} history records")
        
        # 按类型过滤
        if type_filter:
            history_list = [h for h in history_list if h.get('change_type') == type_filter]
            current_app.logger.info(f"Filtered by type: {len(history_list)} records match")
        
        # 按时间降序排序
        history_list.sort(
            key=lambda x: x.get('change_time') if isinstance(x.get('change_time'), datetime) 
            else datetime.fromisoformat(x.get('change_time').replace('Z', '+00:00')), 
            reverse=True
        )
        
        # 手动分页
        total = len(history_list)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        
        # 获取当前页的记录
        current_page_items = history_list[start_idx:end_idx] if start_idx < total else []
        
        # 确保points_change是浮点数
        items = []
        for item in current_page_items:
            try:
                if 'points_change' in item:
                    item['points_change'] = float(item['points_change'])
                items.append(item)
            except Exception as e:
                current_app.logger.error(f"Error converting history item: {str(e)}", exc_info=True)
        
        current_app.logger.info(f"Final items count: {len(items)}")
        
        # 获取用户信息
        user = User.get_by_id(user_id)
        current_app.logger.info(f"User total points: {user.get('total_points') if user else 'User not found'}")
        
        response_data = {
            'items': items,
            'total': total,
            'pages': total_pages,
            'current_page': page,
            'total_points': float(user.get('total_points', 0)) if user else 0.0
        }
        
        current_app.logger.info(f"Response data prepared")
        
        return APIResponse.success(data=response_data)
    except Exception as e:
        current_app.logger.error(f"Error in get_point_history: {str(e)}", exc_info=True)
        raise

@bp.route('/history/all', methods=['GET'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
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
        
        # 获取所有历史记录
        all_history = PointHistory.list_all()
        
        # 按类型过滤
        if type_filter:
            all_history = [h for h in all_history if h.get('change_type') == type_filter]
        
        # 如果有搜索关键词，过滤结果
        filtered_history = []
        if search_query:
            search_query = search_query.lower()
            for history in all_history:
                user_id = history.get('user_id')
                user = User.get_by_id(user_id) if user_id else None
                if user:
                    if (search_query in str(user.get('username', '')).lower() or
                        search_query in str(user.get('name', '')).lower() or
                        search_query in str(user.get('student_id', '')).lower()):
                        history['user'] = user
                        filtered_history.append(history)
        else:
            # 添加用户信息到每条记录
            for history in all_history:
                user_id = history.get('user_id')
                user = User.get_by_id(user_id) if user_id else None
                history['user'] = user or {}
                filtered_history.append(history)
        
        # 按时间降序排序
        filtered_history.sort(
            key=lambda x: x.get('change_time') if isinstance(x.get('change_time'), datetime) 
            else datetime.fromisoformat(x.get('change_time').replace('Z', '+00:00')),
            reverse=True
        )
        
        # 手动分页
        total = len(filtered_history)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        
        # 获取当前页的记录
        items = filtered_history[start_idx:end_idx] if start_idx < total else []
            
        current_app.logger.info(f"Found {len(items)} history records for current page")
        
        return APIResponse.success(data={
            'items': items,
            'total': total,
            'pages': total_pages,
            'current_page': page
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_all_point_history: {str(e)}", exc_info=True)
        raise

@bp.route('/statistics', methods=['GET'])
@jwt_required()
@role_required('admin', 'superadmin')
@handle_exceptions
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
        user_id = int(get_jwt_identity())
        current_app.logger.info(f"User ID from JWT: {user_id}")
        
        user = User.get_by_id(user_id)
        if not user:
            current_app.logger.error(f"User not found for ID: {user_id}")
            return APIResponse.error("User not found", 404)
            
        current_app.logger.info(f"Found user: {user.get('username')}, current total_points: {user.get('total_points')}")
        
        now = datetime.utcnow()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_day_of_last_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
        
        # 获取用户所有积分历史
        history_records = PointHistory.list_by_user(user_id)
        
        # 计算本月积分
        monthly_points = 0
        for record in history_records:
            change_time = record.get('change_time')
            if isinstance(change_time, str):
                change_time = datetime.fromisoformat(change_time.replace('Z', '+00:00'))
            
            if change_time >= first_day_of_month:
                monthly_points += float(record.get('points_change', 0))
        
        current_app.logger.info(f"Monthly points result: {monthly_points}")
        
        # 计算上月积分
        last_month_points = 0
        for record in history_records:
            change_time = record.get('change_time')
            if isinstance(change_time, str):
                change_time = datetime.fromisoformat(change_time.replace('Z', '+00:00'))
            
            if first_day_of_last_month <= change_time < first_day_of_month:
                last_month_points += float(record.get('points_change', 0))
        
        current_app.logger.info(f"Last month points result: {last_month_points}")
        
        # 获取最近的积分历史记录（最多5条）
        recent_history = sorted(
            history_records,
            key=lambda x: x.get('change_time') if isinstance(x.get('change_time'), datetime) else datetime.fromisoformat(x.get('change_time').replace('Z', '+00:00')),
            reverse=True
        )[:5]
        
        current_app.logger.info(f"Recent point history: {len(recent_history)} records")
        
        current_app.logger.info(f"Statistics - total: {user.get('total_points')}, monthly: {monthly_points}, last_month: {last_month_points}")
        
        return APIResponse.success(data={
            'total_points': float(user.get('total_points', 0)),
            'monthly_points': monthly_points,
            'last_month_points': last_month_points,
            'recent_history': recent_history
        })
    except Exception as e:
        current_app.logger.error(f"Error in get_point_statistics: {str(e)}", exc_info=True)
        raise

@bp.route('/adjust', methods=['POST'])
@jwt_required()
@role_required('admin', 'superadmin')
@validate_json_request
@handle_exceptions
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
    data = request.get_json()
    
    # 验证必要字段
    required_fields = ['user_id', 'points_change', 'description']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    user_id = int(data['user_id'])
    points_change = float(data['points_change'])
    description = data['description']
    
    # 检查用户是否存在
    user = User.get_by_id(user_id)
    if not user:
        return APIResponse.error("用户不存在", 404)
    
    try:
        # 调整用户积分
        if User.add_points(
            user_id=user_id,
            points=points_change,
            change_type='manual',
            description=f'手动调整: {description}',
            related_id=None
        ):
            return APIResponse.success(msg="积分调整成功")
        else:
            return APIResponse.error("积分调整失败", 500)
    except Exception as e:
        current_app.logger.error(f"Error adjusting points: {str(e)}")
        return APIResponse.error(str(e), 500) 