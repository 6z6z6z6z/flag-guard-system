from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
import logging
import re
from flask import current_app

logger = logging.getLogger(__name__)

class BaseModel(db.Model):
    """基础模型类，提供通用功能"""
    __abstract__ = True

    def to_dict(self):
        """将模型转换为字典"""
        try:
            result = {}
            for column in self.__table__.columns:
                value = getattr(self, column.name)
                if value is None:
                    result[column.name] = None
                elif isinstance(value, datetime):
                    value = value.isoformat()
                    result[column.name] = value
                else:
                    result[column.name] = value
            return result
        except Exception as e:
            logger.error(f'Error converting {self.__class__.__name__} to dict: {str(e)}')
            return {}

class User(BaseModel):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # 'member', 'admin', 'captain'
    name = db.Column(db.String(50), nullable=False)
    student_id = db.Column(db.String(10), unique=True, nullable=False, index=True)
    college = db.Column(db.String(100), nullable=False)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    shoe_size = db.Column(db.Integer)
    total_points = db.Column(db.Float, default=0.0)
    phone_number = db.Column(db.String(15), nullable=True)
    
    # 关系
    flag_records = db.relationship('FlagRecord', foreign_keys='FlagRecord.user_id', back_populates='user')
    reviewed_flags = db.relationship('FlagRecord', foreign_keys='FlagRecord.reviewer_id', back_populates='reviewer')
    training_registrations = db.relationship('TrainingRegistration', back_populates='user')
    event_registrations = db.relationship('EventRegistration', back_populates='user')
    point_history = db.relationship('PointHistory', back_populates='user')
    created_trainings = db.relationship('Training', back_populates='creator', foreign_keys='Training.created_by')
    created_events = db.relationship('Event', back_populates='creator', foreign_keys='Event.created_by')

    @staticmethod
    def validate_student_id(student_id):
        """验证学号格式是否为2个大写字母+8个数字"""
        return re.match(r'^[A-Z]{2}\d{8}$', student_id)

    def set_password(self, password):
        """设置密码，自动进行哈希处理"""
        if not password or not isinstance(password, str):
            logger.error(f'Invalid password format for user {self.username}')
            return False
            
        try:
            self.password = generate_password_hash(password)
            logger.info(f'Password set for user {self.username}')
            return True
        except Exception as e:
            logger.error(f'Error setting password for user {self.username}: {str(e)}')
            return False
    
    def check_password(self, password):
        """验证密码"""
        try:
            if not password:
                current_app.logger.warning(f"Password check failed for user {self.username}: Empty password")
                return False
            
            if not self.password:
                current_app.logger.warning(f"Password check failed for user {self.username}: No password hash")
                return False
            
            result = check_password_hash(self.password, password)
            if not result:
                current_app.logger.warning(f"Password check failed for user {self.username}: Invalid password")
            return result
        except Exception as e:
            current_app.logger.error(f"Password check error for user {self.username}: {str(e)}")
            return False
    
    def add_points(self, points, change_type, related_id, description):
        """添加积分并记录历史"""
        try:
            self.total_points += points
            history = PointHistory(
                user_id=self.user_id,
                points_change=points,
                change_type=change_type,
                related_id=related_id,
                description=description
            )
            db.session.add(history)
            db.session.commit()
            logger.info(f'Points added for user {self.username}: {points} points, type: {change_type}')
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error adding points for user {self.username}: {str(e)}')
            return False

    def is_admin(self):
        """判断是否为管理员"""
        return self.role in ['admin', 'captain']

    def to_dict(self):
        """将用户信息转换为字典，不包含敏感信息"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'name': self.name,
            'student_id': self.student_id,
            'college': self.college,
            'height': self.height,
            'weight': self.weight,
            'shoe_size': self.shoe_size,
            'total_points': self.total_points,
            'phone_number': self.phone_number
        }

class Training(BaseModel):
    """训练模型"""
    __tablename__ = 'trainings'

    training_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    points = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(200), nullable=False, default='')
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='scheduled')  # e.g., 'scheduled', 'ended', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    registrations = db.relationship('TrainingRegistration', back_populates='training', cascade='all, delete-orphan')
    creator = db.relationship('User', back_populates='created_trainings', foreign_keys=[created_by])
    events = db.relationship('Event', secondary='event_trainings', back_populates='trainings')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'training_id': self.training_id,
            'name': self.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'points': self.points,
            'location': self.location if self.location is not None else '',
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TrainingRegistration(BaseModel):
    __tablename__ = 'training_registrations'
    registration_id = db.Column(db.Integer, primary_key=True)
    training_id = db.Column(db.Integer, db.ForeignKey('trainings.training_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(20), default='registered')  # 'registered', 'confirmed', 'awarded'
    attendance_status = db.Column(db.String(20))  # 'absent', 'present', 'late', 'early_leave'
    points_awarded = db.Column(db.Float)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关系
    user = db.relationship('User', back_populates='training_registrations')
    training = db.relationship('Training', back_populates='registrations')

    def to_dict(self):
        """将报名记录转换为字典，包含用户信息和标准UTC时间"""
        return {
            'registration_id': self.registration_id,
            'training_id': self.training_id,
            'user_id': self.user_id,
            'status': self.status,
            'attendance_status': self.attendance_status,
            'points_awarded': self.points_awarded,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'user': {
                'name': self.user.name,
                'student_id': self.user.student_id,
                'college': self.user.college
            }
        }

class Event(BaseModel):
    __tablename__ = 'events'
    event_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100))
    uniform_required = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    registrations = db.relationship('EventRegistration', back_populates='event')
    creator = db.relationship('User', back_populates='created_events', foreign_keys=[created_by])
    trainings = db.relationship('Training', secondary='event_trainings', back_populates='events')

    @hybrid_property
    def status(self):
        if self.time > datetime.utcnow():
            return '未开始'
        else:
            return '已结束'

    def to_dict(self):
        """转换为字典"""
        try:
            return {
                'event_id': self.event_id,
                'name': self.name,
                'time': self.time.isoformat() if self.time else None,
                'location': self.location,
                'uniform_required': self.uniform_required,
                'status': self.status,
                'created_by': self.created_by,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'trainings': [{
                    'training_id': t.training_id,
                    'name': t.name
                } for t in self.trainings]
            }
        except Exception as e:
            logger.error(f'Error converting event {self.event_id} to dict: {str(e)}')
            return {}

# 活动-训练关联表
class EventTraining(BaseModel):
    __tablename__ = 'event_trainings'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), nullable=False)
    training_id = db.Column(db.Integer, db.ForeignKey('trainings.training_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EventRegistration(BaseModel):
    __tablename__ = 'event_registrations'
    registration_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    status = db.Column(db.String(20), default='registered')  # 'registered', 'confirmed', 'cancelled'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = db.relationship('User', back_populates='event_registrations')
    event = db.relationship('Event', back_populates='registrations')

    def __init__(self, **kwargs):
        super(EventRegistration, self).__init__(**kwargs)
        if 'created_at' not in kwargs:
            self.created_at = datetime.utcnow()
        if 'updated_at' not in kwargs:
            self.updated_at = datetime.utcnow()

class FlagRecord(BaseModel):
    """升降旗记录"""
    __tablename__ = 'flag_records'
    
    record_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # raise or lower
    photo_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    points_awarded = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    
    # 关系
    user = db.relationship('User', foreign_keys=[user_id], back_populates='flag_records')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviewed_flags')
    
    def to_dict(self):
        """将升降旗记录转换为字典"""
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'date': self.date.isoformat() if self.date else None,
            'type': self.type,
            'photo_url': self.photo_url,
            'status': self.status,
            'points_awarded': self.points_awarded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer.name if self.reviewer else None
        }

class PointHistory(BaseModel):
    """积分历史记录"""
    __tablename__ = 'point_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    points_change = db.Column(db.Float, nullable=False)
    change_type = db.Column(db.String(20), nullable=False)  # flag, training, event
    description = db.Column(db.String(255))
    related_id = db.Column(db.Integer)  # 相关记录ID
    change_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    user = db.relationship('User', back_populates='point_history')
    
    def to_dict(self):
        """转换为字典"""
        try:
            return {
                'history_id': self.history_id,
                'user_id': self.user_id,
                'points_change': self.points_change,
                'change_type': self.change_type,
                'description': self.description,
                'related_id': self.related_id,
                'change_time': self.change_time.isoformat() if self.change_time else None
            }
        except Exception as e:
            logger.error(f'Error converting point history {self.history_id} to dict: {str(e)}')
            return {}

class OperationLog(BaseModel):
    __tablename__ = 'operation_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    endpoint = db.Column(db.String(100), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))