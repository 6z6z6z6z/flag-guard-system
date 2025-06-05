from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models import User, PointHistory, db
from utils.auth import login_required, admin_required
from utils.pagination import paginate

bp = Blueprint('points', __name__)

@bp.route('/history')
@login_required
def get_point_history():
    """获取个人积分历史"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    type_filter = request.args.get('type')

    query = PointHistory.query.filter_by(user_id=g.user.user_id)
    if type_filter:
        query = query.filter_by(change_type=type_filter)
    
    query = query.order_by(PointHistory.change_time.desc())
    pagination = paginate(query, page, per_page)
    
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total
    })

@bp.route('/history/all')
@admin_required
def get_all_point_history():
    """获取所有用户的积分历史（管理员）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    type_filter = request.args.get('type')

    query = PointHistory.query
    if type_filter:
        query = query.filter_by(change_type=type_filter)
    
    query = query.order_by(PointHistory.change_time.desc())
    pagination = paginate(query, page, per_page)
    
    items = []
    for history in pagination.items:
        history_dict = history.to_dict()
        history_dict['user'] = history.user.to_dict()
        items.append(history_dict)
    
    return jsonify({
        'items': items,
        'total': pagination.total
    })

@bp.route('/statistics')
@login_required
def get_point_statistics():
    """获取积分统计信息"""
    user = g.user
    now = datetime.utcnow()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_day_of_last_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
    
    # 本月积分
    monthly_points = db.session.query(func.sum(PointHistory.points_change)).filter(
        and_(
            PointHistory.user_id == user.user_id,
            PointHistory.change_time >= first_day_of_month
        )
    ).scalar() or 0
    
    # 上月积分
    last_month_points = db.session.query(func.sum(PointHistory.points_change)).filter(
        and_(
            PointHistory.user_id == user.user_id,
            PointHistory.change_time >= first_day_of_last_month,
            PointHistory.change_time < first_day_of_month
        )
    ).scalar() or 0
    
    return jsonify({
        'total_points': user.total_points,
        'monthly_points': monthly_points,
        'last_month_points': last_month_points
    })

@bp.route('/adjust', methods=['POST'])
@admin_required
def adjust_points():
    """调整用户积分（管理员）"""
    data = request.get_json()
    user_id = data.get('user_id')
    points_change = data.get('points_change')
    change_type = data.get('change_type')
    description = data.get('description')
    
    if not all([user_id, points_change is not None, change_type, description]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    try:
        # 添加积分历史记录
        history = PointHistory(
            user_id=user_id,
            points_change=points_change,
            change_type=change_type,
            description=description
        )
        db.session.add(history)
        
        # 更新用户总积分
        user.total_points += points_change
        db.session.commit()
        
        return jsonify({'message': '积分调整成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 