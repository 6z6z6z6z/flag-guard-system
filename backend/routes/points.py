from flask import Blueprint, request, current_app
from datetime import datetime, timedelta, timezone
from models_pymysql import User, PointHistory
from db_connection import db
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, role_required
)
from utils.time_utils import TimeUtils, BEIJING_TZ
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
        
        # 参数验证
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 10
        
        current_app.logger.info(f"Query params - page: {page}, per_page: {per_page}, type: {type_filter}")
        
        # 获取用户信息，确保用户存在
        try:
            user = User.get_by_id(user_id)
            if not user:
                current_app.logger.warning(f"User not found for ID: {user_id}")
                return APIResponse.success(data={
                    'items': [],
                    'total': 0,
                    'pages': 0,
                    'current_page': page,
                    'total_points': 0.0
                })
        except Exception as e:
            current_app.logger.error(f"Error getting user: {str(e)}", exc_info=True)
            return APIResponse.success(data={
                'items': [],
                'total': 0,
                'pages': 0,
                'current_page': page,
                'total_points': 0.0
            })
        
        # 确保总积分为浮点数
        total_points = float(user.get('total_points', 0.0))
        current_app.logger.info(f"User: {user.get('username')}, role: {user.get('role')}, total points: {total_points}")
        
        # 获取积分历史，使用安全的默认值
        try:
            history_list = PointHistory.list_by_user(user_id)
            if history_list is None:
                history_list = []
            current_app.logger.info(f"Retrieved {len(history_list)} history records")
        except Exception as e:
            current_app.logger.error(f"Error getting point history: {str(e)}", exc_info=True)
            history_list = []
        
        # 如果没有历史记录，返回空列表
        if not history_list:
            current_app.logger.info(f"No point history for user {user_id}")
            return APIResponse.success(data={
                'items': [],
                'total': 0,
                'pages': 0,
                'current_page': page,
                'total_points': total_points
            })
        
        # 按类型过滤
        if type_filter:
            try:
                history_list = [h for h in history_list if h and h.get('change_type') == type_filter]
                current_app.logger.info(f"Filtered by type '{type_filter}': {len(history_list)} records match")
            except Exception as e:
                current_app.logger.error(f"Error filtering by type: {str(e)}", exc_info=True)
                # 如果过滤失败，继续使用未过滤的列表
        
        # 按时间降序排序，使用更安全的排序逻辑
        try:
            def safe_get_time(x):
                try:
                    if not x:
                        return datetime(1970, 1, 1)
                    change_time = x.get('change_time')
                    if isinstance(change_time, datetime):
                        return change_time
                    elif isinstance(change_time, str):
                        # 处理格式化后的时间字符串，例如 "2023-12-01 15:30:00"
                        if 'T' in change_time:
                            # ISO格式
                            return datetime.fromisoformat(change_time.replace('Z', '+00:00'))
                        else:
                            # 普通格式
                            return datetime.strptime(change_time, '%Y-%m-%d %H:%M:%S')
                    else:
                        # 如果无法解析时间，返回一个很早的时间作为默认值
                        return datetime(1970, 1, 1)
                except Exception as e:
                    current_app.logger.warning(f"Failed to parse time {change_time}: {e}")
                    return datetime(1970, 1, 1)
            
            history_list.sort(key=safe_get_time, reverse=True)
        except Exception as e:
            current_app.logger.error(f"Error sorting history: {str(e)}", exc_info=True)
            # 如果排序失败，继续使用原始列表
        
        # 手动分页
        total = len(history_list)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        
        # 获取当前页的记录
        current_page_items = history_list[start_idx:end_idx] if start_idx < total else []
        
        # 格式化数据并确保points_change是浮点数
        items = []
        for item in current_page_items:
            try:
                if not item:
                    continue
                
                # 数据已经在模型层格式化过了，只需要确保数据完整性
                formatted_item = dict(item)  # 创建副本避免修改原数据
                if 'points_change' in formatted_item:
                    formatted_item['points_change'] = float(formatted_item.get('points_change', 0))
                # 确保其他必要字段存在
                formatted_item.setdefault('change_type', 'unknown')
                formatted_item.setdefault('description', '未知操作')
                formatted_item.setdefault('history_id', 0)
                items.append(formatted_item)
            except Exception as e:
                current_app.logger.error(f"Error converting history item: {str(e)}, item: {item}", exc_info=True)
                # 即使格式化失败，也添加一个基本的记录
                try:
                    fallback_item = {
                        'history_id': item.get('history_id', 0) if item else 0,
                        'points_change': float(item.get('points_change', 0)) if item else 0.0,
                        'change_type': item.get('change_type', 'unknown') if item else 'unknown',
                        'description': item.get('description', '数据格式错误') if item else '数据格式错误',
                        'change_time': str(item.get('change_time', '')) if item else ''
                    }
                    items.append(fallback_item)
                except Exception as fallback_error:
                    current_app.logger.error(f"Failed to create fallback item: {fallback_error}")
                    # 跳过这个有问题的条目
                    continue
        
        current_app.logger.info(f"Final items count: {len(items)}")
        
        response_data = {
            'items': items,
            'total': total,
            'pages': total_pages,
            'current_page': page,
            'total_points': total_points
        }
        
        current_app.logger.info(f"Response data prepared successfully")
        
        return APIResponse.success(data=response_data)
    except Exception as e:
        current_app.logger.error(f"Critical error in get_point_history: {str(e)}", exc_info=True)
        # 返回空的默认数据而不是抛出异常
        return APIResponse.success(data={
            'items': [],
            'total': 0,
            'pages': 0,
            'current_page': 1,
            'total_points': 0.0
        })

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
        
        # 获取当前页的记录并格式化
        current_page_items = filtered_history[start_idx:end_idx] if start_idx < total else []
        
        # 格式化数据，处理时间字段
        items = []
        for item in current_page_items:
            try:
                formatted_item = PointHistory.format_dict(item)
                items.append(formatted_item)
            except Exception as e:
                current_app.logger.error(f"Error formatting history item: {str(e)}", exc_info=True)
                items.append(item)  # 如果格式化失败，使用原始数据
            
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
            
        current_app.logger.info(f"Found user: {user.get('username')}, role: {user.get('role')}, current total_points: {user.get('total_points')}")
        
        # 获取用户所有积分历史，不再对管理员做特殊处理
        # 管理员也可能有积分记录（比如手动调整的积分）
        try:
            history_records = PointHistory.list_by_user(user_id)
            if history_records is None:
                history_records = []
            current_app.logger.info(f"Found {len(history_records)} history records for user {user_id}")
        except Exception as e:
            current_app.logger.error(f"Error getting history for statistics: {str(e)}", exc_info=True)
            history_records = []
        
        # 如果没有积分记录，返回默认统计值
        if not history_records:
            current_app.logger.info(f"No point history for user {user_id}, returning default statistics")
            return APIResponse.success(data={
                'total_points': float(user.get('total_points', 0)),
                'monthly_points': 0.0,
                'last_month_points': 0.0,
                'recent_history': []
            })
        
        # 使用TimeUtils获取当前北京时间
        try:
            current_beijing_time = TimeUtils.now_beijing()
            current_app.logger.info(f"Current Beijing time: {current_beijing_time}")
            
            # 计算本月第一天（北京时间）
            first_day_of_month_beijing = current_beijing_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 计算上月第一天（北京时间）
            if first_day_of_month_beijing.month == 1:
                first_day_of_last_month_beijing = first_day_of_month_beijing.replace(year=first_day_of_month_beijing.year - 1, month=12)
            else:
                first_day_of_last_month_beijing = first_day_of_month_beijing.replace(month=first_day_of_month_beijing.month - 1)
            
            current_app.logger.info(f"Time calculation - first_day_of_month: {first_day_of_month_beijing}, first_day_of_last_month: {first_day_of_last_month_beijing}")
        except Exception as e:
            current_app.logger.error(f"Error calculating time boundaries: {str(e)}", exc_info=True)
            # 如果时间计算失败，返回默认值
            return APIResponse.success(data={
                'total_points': float(user.get('total_points', 0)),
                'monthly_points': 0.0,
                'last_month_points': 0.0,
                'recent_history': []
            })
        
        # 计算本月积分
        monthly_points = 0
        for record in history_records:
            try:
                change_time = record.get('change_time')
                # 处理时间，确保最终都是带时区的datetime对象用于比较
                if isinstance(change_time, datetime):
                    # 如果是datetime对象，确保它有时区信息
                    if change_time.tzinfo is None:
                        # 无时区信息，假设是北京时间
                        beijing_time = change_time.replace(tzinfo=BEIJING_TZ)
                    else:
                        beijing_time = change_time
                elif isinstance(change_time, str):
                    # 先尝试解析字符串为datetime
                    try:
                        if 'T' in change_time:
                            # ISO格式，可能包含时区信息
                            beijing_time = datetime.fromisoformat(change_time.replace('Z', '+00:00'))
                            # 如果是UTC时间，需要转换为北京时间
                            if beijing_time.tzinfo and beijing_time.tzinfo == timezone.utc:
                                beijing_time = beijing_time.astimezone(BEIJING_TZ)
                        else:
                            # 普通格式，假设已经是北京时间，添加时区信息
                            naive_time = datetime.strptime(change_time, '%Y-%m-%d %H:%M:%S')
                            beijing_time = naive_time.replace(tzinfo=BEIJING_TZ)
                    except Exception as parse_error:
                        current_app.logger.warning(f"Failed to parse time string '{change_time}': {parse_error}")
                        continue
                else:
                    current_app.logger.warning(f"Unknown time format: {change_time}")
                    continue
                
                if beijing_time and beijing_time >= first_day_of_month_beijing:
                    points_change = float(record.get('points_change', 0))
                    monthly_points += points_change
                    current_app.logger.debug(f"Monthly record: beijing_time={beijing_time}, points={points_change}")
            except Exception as e:
                current_app.logger.error(f"Error processing monthly points record: {str(e)}", exc_info=True)
                continue
        
        current_app.logger.info(f"Monthly points result: {monthly_points}")
        
        # 计算上月积分
        last_month_points = 0
        for record in history_records:
            try:
                change_time = record.get('change_time')
                # 处理时间，确保最终都是带时区的datetime对象用于比较
                if isinstance(change_time, datetime):
                    # 如果是datetime对象，确保它有时区信息
                    if change_time.tzinfo is None:
                        # 无时区信息，假设是北京时间
                        beijing_time = change_time.replace(tzinfo=BEIJING_TZ)
                    else:
                        beijing_time = change_time
                elif isinstance(change_time, str):
                    # 先尝试解析字符串为datetime
                    try:
                        if 'T' in change_time:
                            # ISO格式，可能包含时区信息
                            beijing_time = datetime.fromisoformat(change_time.replace('Z', '+00:00'))
                            # 如果是UTC时间，需要转换为北京时间
                            if beijing_time.tzinfo and beijing_time.tzinfo == timezone.utc:
                                beijing_time = beijing_time.astimezone(BEIJING_TZ)
                        else:
                            # 普通格式，假设已经是北京时间，添加时区信息
                            naive_time = datetime.strptime(change_time, '%Y-%m-%d %H:%M:%S')
                            beijing_time = naive_time.replace(tzinfo=BEIJING_TZ)
                    except Exception as parse_error:
                        current_app.logger.warning(f"Failed to parse time string '{change_time}': {parse_error}")
                        continue
                else:
                    current_app.logger.warning(f"Unknown time format: {change_time}")
                    continue
                
                if beijing_time and first_day_of_last_month_beijing <= beijing_time < first_day_of_month_beijing:
                    points_change = float(record.get('points_change', 0))
                    last_month_points += points_change
                    current_app.logger.debug(f"Last month record: beijing_time={beijing_time}, points={points_change}")
            except Exception as e:
                current_app.logger.error(f"Error processing last month points record: {str(e)}", exc_info=True)
                continue
        
        # 获取最近的积分历史记录（最多5条）并格式化
        def safe_get_time_for_sorting(x):
            try:
                change_time = x.get('change_time')
                if isinstance(change_time, datetime):
                    return change_time
                elif isinstance(change_time, str):
                    if 'T' in change_time:
                        return datetime.fromisoformat(change_time.replace('Z', '+00:00'))
                    else:
                        return datetime.strptime(change_time, '%Y-%m-%d %H:%M:%S')
                else:
                    return datetime(1970, 1, 1)
            except Exception as e:
                current_app.logger.warning(f"Failed to parse time for sorting {change_time}: {e}")
                return datetime(1970, 1, 1)
        
        recent_history_raw = sorted(
            history_records,
            key=safe_get_time_for_sorting,
            reverse=True
        )[:5]
        
        # 格式化最近的历史记录
        recent_history = []
        for record in recent_history_raw:
            try:
                formatted_record = PointHistory.format_dict(record)
                recent_history.append(formatted_record)
            except Exception as e:
                current_app.logger.error(f"Error formatting recent history record: {str(e)}", exc_info=True)
                recent_history.append(record)  # 如果格式化失败，使用原始数据
        
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
        # 返回默认统计数据而不是抛出异常
        try:
            user_id = int(get_jwt_identity())
            user = User.get_by_id(user_id)
            total_points = float(user.get('total_points', 0)) if user else 0.0
        except:
            total_points = 0.0
        
        return APIResponse.success(data={
            'total_points': total_points,
            'monthly_points': 0.0,
            'last_month_points': 0.0,
            'recent_history': []
        })

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
    required_fields = ['user_id', 'points_change', 'change_type', 'description']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    user_id = int(data['user_id'])
    points_change = float(data['points_change'])
    change_type = data['change_type']
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
            change_type=change_type,
            description=f'手动调整: {description}',
            related_id=None
        ):
            return APIResponse.success(msg="积分调整成功")
        else:
            return APIResponse.error("积分调整失败", 500)
    except Exception as e:
        current_app.logger.error(f"Error adjusting points: {str(e)}")
        return APIResponse.error(str(e), 500) 