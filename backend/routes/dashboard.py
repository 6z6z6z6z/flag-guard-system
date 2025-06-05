from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import User, Training, Event, FlagRecord

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
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
    total_users = User.query.count()
    total_trainings = Training.query.count()
    total_events = Event.query.count()
    total_flags = FlagRecord.query.count()
    
    return jsonify({
        "data": {
            "stats": {
                "total_users": total_users,
                "total_trainings": total_trainings,
                "total_events": total_events,
                "total_flags": total_flags
            }
        }
    }), 200 