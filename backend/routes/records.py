from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, Training, Event, FlagRecord
from extensions import db
from routes.auth import role_required

records_bp = Blueprint('records', __name__)

@records_bp.route('/records', methods=['GET'])
@jwt_required()
def get_records():
    """
    获取用户的培训和活动记录
    ---
    tags:
      - 记录
    security:
      - Bearer: []
    responses:
      200:
        description: 成功获取记录
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # 获取用户参与的培训记录
    training_records = Training.query.filter(
        Training.participants.any(user_id=user_id)
    ).all()
    
    # 获取用户参与的活动记录
    event_records = Event.query.filter(
        Event.participants.any(user_id=user_id)
    ).all()
    
    return jsonify({
        "data": {
            "training_records": [
                {
                    "id": record.id,
                    "title": record.title,
                    "date": record.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": record.status,
                    "points": record.points
                } for record in training_records
            ],
            "event_records": [
                {
                    "id": record.id,
                    "title": record.title,
                    "date": record.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": record.status,
                    "points": record.points
                } for record in event_records
            ]
        }
    }), 200

@records_bp.route('/records/pending', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_pending_records():
    """
    获取所有待审核的记录（管理员用）
    ---
    tags:
      - 记录
    security:
      - Bearer: []
    responses:
      200:
        description: 成功获取待审核记录
      403:
        description: 权限不足
    """
    try:
        # 获取待审核的升降旗记录
        flag_records = FlagRecord.query.filter_by(status='pending').all()
        
        # 获取待审核的培训记录
        training_records = Training.query.filter(
            Training.registrations.any(status='registered')
        ).all()
        
        # 获取待审核的活动记录
        event_records = Event.query.filter(
            Event.registrations.any(status='registered')
        ).all()
        
        return jsonify({
            "data": {
                "flag_records": [record.to_dict() for record in flag_records],
                "training_records": [
                    {
                        "id": record.training_id,
                        "name": record.name,
                        "type": record.type,
                        "start_time": record.start_time.isoformat(),
                        "end_time": record.end_time.isoformat() if record.end_time else None,
                        "points": record.points,
                        "created_by": record.created_by
                    } for record in training_records
                ],
                "event_records": [
                    {
                        "id": record.event_id,
                        "name": record.name,
                        "time": record.time.isoformat(),
                        "uniform_required": record.uniform_required,
                        "created_by": record.created_by
                    } for record in event_records
                ]
            }
        }), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500 