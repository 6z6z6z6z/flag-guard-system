from datetime import datetime
import logging
import re
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import db
from sql.queries import *

logger = logging.getLogger(__name__)

class BaseModel:
    """基础模型类，提供通用功能"""
    
    @staticmethod
    def convert_datetime(value):
        """转换datetime为ISO格式字符串"""
        if isinstance(value, datetime):
            return value.isoformat()
        return value
    
    @classmethod
    def format_dict(cls, data):
        """格式化字典，处理特殊类型"""
        if not data:
            return {}
        result = {}
        for key, value in data.items():
            result[key] = cls.convert_datetime(value)
        return result

class User(BaseModel):
    """用户模型"""
    
    @staticmethod
    def validate_student_id(student_id):
        """验证学号格式是否为2个大写字母+8个数字"""
        return re.match(r'^[A-Z]{2}\d{8}$', student_id)
    
    @classmethod
    def get_by_id(cls, user_id):
        """根据ID获取用户"""
        try:
            data = db.execute_query(USER_QUERIES['get_by_id'], (user_id,), fetch_one=True)
            return data
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_username(cls, username):
        """根据用户名获取用户"""
        try:
            data = db.execute_query(USER_QUERIES['get_by_username'], (username,), fetch_one=True)
            return data
        except Exception as e:
            logger.error(f"根据用户名获取用户失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_student_id(cls, student_id):
        """根据学号获取用户"""
        try:
            data = db.execute_query(USER_QUERIES['get_by_student_id'], (student_id,), fetch_one=True)
            return data
        except Exception as e:
            logger.error(f"根据学号获取用户失败: {str(e)}")
            return None
    
    @classmethod
    def create(cls, username, password, role, name, student_id, college, phone_number=None):
        """创建用户"""
        try:
            # 设置密码哈希
            password_hash = generate_password_hash(password)
            
            # 插入用户数据
            user_id = db.execute_insert(
                USER_QUERIES['create'],
                (username, password_hash, role, name, student_id, college, phone_number)
            )
            
            # 返回新创建的用户
            return cls.get_by_id(user_id)
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return None
    
    @classmethod
    def update(cls, user_id, name, college, role, phone_number, height, weight, shoe_size):
        """更新用户信息"""
        try:
            db.execute_update(
                USER_QUERIES['update'],
                (name, college, role, phone_number, height, weight, shoe_size, user_id)
            )
            return cls.get_by_id(user_id)
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return None
    
    @classmethod
    def set_password(cls, user_id, password):
        """设置用户密码"""
        try:
            password_hash = generate_password_hash(password)
            db.execute_update(USER_QUERIES['update_password'], (password_hash, user_id))
            return True
        except Exception as e:
            logger.error(f"设置密码失败: {str(e)}")
            return False
    
    @classmethod
    def check_password(cls, user, password):
        """验证密码"""
        try:
            if not password or not user or not user.get('password'):
                return False
            return check_password_hash(user['password'], password)
        except Exception as e:
            logger.error(f"验证密码失败: {str(e)}")
            return False
    
    @classmethod
    def add_points(cls, user_id, points, change_type, related_id, description):
        """添加积分并记录历史"""
        try:
            # 更新用户总积分
            db.execute_update(USER_QUERIES['update_points'], (points, user_id))
            
            # 记录积分历史
            PointHistory.create(user_id, points, change_type, description, related_id)
            
            return True
        except Exception as e:
            logger.error(f"添加积分失败: {str(e)}")
            return False
    
    @classmethod
    def is_admin(cls, user):
        """判断是否为管理员"""
        return user and user.get('role') in ['admin', 'captain', 'superadmin']
    
    @classmethod
    def list_all(cls):
        """列出所有用户"""
        try:
            return db.execute_query(USER_QUERIES['list_all'])
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return []
    
    @classmethod
    def search(cls, keyword):
        """搜索用户"""
        try:
            keyword = f'%{keyword}%'
            return db.execute_query(USER_QUERIES['search'], (keyword, keyword, keyword))
        except Exception as e:
            logger.error(f"搜索用户失败: {str(e)}")
            return []
    
    @classmethod
    def delete(cls, user_id):
        """删除用户"""
        try:
            return db.execute_update(USER_QUERIES['delete'], (user_id,))
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return 0
    
    @classmethod
    def to_dict(cls, user):
        """将用户信息转换为字典，不包含敏感信息"""
        if not user:
            return {}
        
        # 确保处理可能缺失的字段
        height = user.get('height')
        weight = user.get('weight')
        shoe_size = user.get('shoe_size')
        
        return {
            'user_id': user.get('user_id'),
            'username': user.get('username'),
            'role': user.get('role'),
            'name': user.get('name'),
            'student_id': user.get('student_id'),
            'college': user.get('college'),
            'height': height if height is not None else '',
            'weight': weight if weight is not None else '',
            'shoe_size': shoe_size if shoe_size is not None else '',
            'total_points': user.get('total_points', 0),
            'phone_number': user.get('phone_number', '')
        }

class Training(BaseModel):
    """训练模型"""
    
    @classmethod
    def create(cls, name, start_time, end_time, points, location, created_by, status='scheduled'):
        """创建训练"""
        try:
            training_id = db.execute_insert(
                TRAINING_QUERIES['create'],
                (name, start_time, end_time, points, location, created_by, status)
            )
            return cls.get_by_id(training_id)
        except Exception as e:
            logger.error(f"创建训练失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, training_id):
        """根据ID获取训练"""
        try:
            return db.execute_query(TRAINING_QUERIES['get_by_id'], (training_id,), fetch_one=True)
        except Exception as e:
            logger.error(f"获取训练失败: {str(e)}")
            return None
    
    @classmethod
    def update(cls, training_id, name, start_time, end_time, points, location, status):
        """更新训练信息"""
        try:
            db.execute_update(
                TRAINING_QUERIES['update'],
                (name, start_time, end_time, points, location, status, training_id)
            )
            return cls.get_by_id(training_id)
        except Exception as e:
            logger.error(f"更新训练失败: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, training_id):
        """删除训练"""
        try:
            return db.execute_update(TRAINING_QUERIES['delete'], (training_id,))
        except Exception as e:
            logger.error(f"删除训练失败: {str(e)}")
            return 0
    
    @classmethod
    def list_all(cls):
        """列出所有训练"""
        try:
            return db.execute_query(TRAINING_QUERIES['list_all'])
        except Exception as e:
            logger.error(f"获取训练列表失败: {str(e)}")
            return []
    
    @classmethod
    def list_upcoming(cls):
        """列出即将开始的训练"""
        try:
            return db.execute_query(TRAINING_QUERIES['list_upcoming'])
        except Exception as e:
            logger.error(f"获取即将开始的训练失败: {str(e)}")
            return []
    
    @classmethod
    def update_status(cls, training_id, status):
        """更新训练状态"""
        try:
            return db.execute_update(TRAINING_QUERIES['update_status'], (status, training_id))
        except Exception as e:
            logger.error(f"更新训练状态失败: {str(e)}")
            return 0
            
    @classmethod
    def to_dict(cls, training):
        """将训练转换为字典"""
        if not training:
            return {}
        
        # 处理日期时间格式
        result = cls.format_dict(training)
        
        return result

class TrainingRegistration(BaseModel):
    """训练报名模型"""
    
    @classmethod
    def create(cls, training_id, user_id, status='registered'):
        """创建训练报名"""
        try:
            registration_id = db.execute_insert(
                TRAINING_REGISTRATION_QUERIES['create'],
                (training_id, user_id, status)
            )
            return cls.get_by_id(registration_id)
        except Exception as e:
            logger.error(f"创建训练报名失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, registration_id):
        """根据ID获取报名信息"""
        try:
            return db.execute_query(
                TRAINING_REGISTRATION_QUERIES['get_by_id'], 
                (registration_id,), 
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"获取报名信息失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_training_and_user(cls, training_id, user_id):
        """根据训练和用户获取报名信息"""
        try:
            return db.execute_query(
                TRAINING_REGISTRATION_QUERIES['get_by_training_and_user'], 
                (training_id, user_id), 
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"获取报名信息失败: {str(e)}")
            return None
    
    @classmethod
    def update_status(cls, registration_id, status, attendance_status=None):
        """更新报名状态"""
        try:
            db.execute_update(
                TRAINING_REGISTRATION_QUERIES['update_status'],
                (status, attendance_status, registration_id)
            )
            return cls.get_by_id(registration_id)
        except Exception as e:
            logger.error(f"更新报名状态失败: {str(e)}")
            return None
    
    @classmethod
    def award_points(cls, registration_id, points):
        """奖励积分"""
        try:
            return db.execute_update(
                TRAINING_REGISTRATION_QUERIES['award_points'],
                (points, registration_id)
            )
        except Exception as e:
            logger.error(f"奖励积分失败: {str(e)}")
            return 0
    
    @classmethod
    def delete(cls, registration_id):
        """删除报名记录"""
        try:
            return db.execute_update(TRAINING_REGISTRATION_QUERIES['delete'], (registration_id,))
        except Exception as e:
            logger.error(f"删除报名记录失败: {str(e)}")
            return 0
    
    @classmethod
    def list_by_training(cls, training_id):
        """列出训练的所有报名记录"""
        try:
            return db.execute_query(TRAINING_REGISTRATION_QUERIES['list_by_training'], (training_id,))
        except Exception as e:
            logger.error(f"获取训练报名列表失败: {str(e)}")
            return []
    
    @classmethod
    def list_by_user(cls, user_id):
        """列出用户的所有报名记录"""
        try:
            return db.execute_query(TRAINING_REGISTRATION_QUERIES['list_by_user'], (user_id,))
        except Exception as e:
            logger.error(f"获取用户报名列表失败: {str(e)}")
            return []
    
    @classmethod
    def to_dict(cls, registration):
        """将报名记录转换为字典"""
        if not registration:
            return {}
        
        # 处理日期时间格式
        return cls.format_dict(registration)

class Event(BaseModel):
    """活动模型"""
    
    @classmethod
    def create(cls, name, time, location, uniform_required, created_by):
        """创建活动"""
        try:
            event_id = db.execute_insert(
                EVENT_QUERIES['create'],
                (name, time, location, uniform_required, created_by)
            )
            return cls.get_by_id(event_id)
        except Exception as e:
            logger.error(f"创建活动失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, event_id):
        """根据ID获取活动"""
        try:
            event = db.execute_query(EVENT_QUERIES['get_by_id'], (event_id,), fetch_one=True)
            if event:
                # 获取活动关联的训练
                trainings = EventTraining.list_by_event(event_id)
                event['trainings'] = trainings
            return event
        except Exception as e:
            logger.error(f"获取活动失败: {str(e)}")
            return None
    
    @classmethod
    def update(cls, event_id, name, time, location, uniform_required):
        """更新活动信息"""
        try:
            db.execute_update(
                EVENT_QUERIES['update'],
                (name, time, location, uniform_required, event_id)
            )
            return cls.get_by_id(event_id)
        except Exception as e:
            logger.error(f"更新活动失败: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, event_id):
        """删除活动"""
        try:
            return db.execute_update(EVENT_QUERIES['delete'], (event_id,))
        except Exception as e:
            logger.error(f"删除活动失败: {str(e)}")
            return 0
    
    @classmethod
    def list_all(cls):
        """列出所有活动"""
        try:
            events = db.execute_query(EVENT_QUERIES['list_all'])
            # 为每个活动获取关联的训练
            for event in events:
                event['trainings'] = EventTraining.list_by_event(event['event_id'])
            return events
        except Exception as e:
            logger.error(f"获取活动列表失败: {str(e)}")
            return []
    
    @classmethod
    def list_upcoming(cls):
        """列出即将开始的活动"""
        try:
            events = db.execute_query(EVENT_QUERIES['list_upcoming'])
            # 为每个活动获取关联的训练
            for event in events:
                event['trainings'] = EventTraining.list_by_event(event['event_id'])
            return events
        except Exception as e:
            logger.error(f"获取即将开始的活动失败: {str(e)}")
            return []
    
    @classmethod
    def status(cls, event):
        """获取活动状态"""
        if not event:
            return '未知'
        
        event_time = event.get('time')
        if not event_time:
            return '未知'
            
        if isinstance(event_time, str):
            event_time = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            
        return '未开始' if event_time > datetime.now() else '已结束'
    
    @classmethod
    def to_dict(cls, event):
        """将活动转换为字典"""
        if not event:
            return {}
        
        # 处理日期时间格式
        result = cls.format_dict(event)
        
        # 添加状态
        result['status'] = cls.status(event)
        
        return result

class EventTraining(BaseModel):
    """活动-训练关联模型"""
    
    @classmethod
    def add(cls, event_id, training_id):
        """添加关联"""
        try:
            return db.execute_insert(EVENT_TRAINING_QUERIES['add'], (event_id, training_id))
        except Exception as e:
            logger.error(f"添加活动-训练关联失败: {str(e)}")
            return 0
    
    @classmethod
    def remove(cls, event_id, training_id):
        """移除关联"""
        try:
            return db.execute_update(EVENT_TRAINING_QUERIES['remove'], (event_id, training_id))
        except Exception as e:
            logger.error(f"移除活动-训练关联失败: {str(e)}")
            return 0
    
    @classmethod
    def list_by_event(cls, event_id):
        """获取活动关联的所有训练"""
        try:
            return db.execute_query(EVENT_TRAINING_QUERIES['list_by_event'], (event_id,))
        except Exception as e:
            logger.error(f"获取活动关联训练列表失败: {str(e)}")
            return []
    
    @classmethod
    def list_by_training(cls, training_id):
        """获取训练关联的所有活动"""
        try:
            return db.execute_query(EVENT_TRAINING_QUERIES['list_by_training'], (training_id,))
        except Exception as e:
            logger.error(f"获取训练关联活动列表失败: {str(e)}")
            return []

class EventRegistration(BaseModel):
    """活动报名模型"""
    
    @classmethod
    def create(cls, event_id, user_id, status='registered'):
        """创建活动报名"""
        try:
            registration_id = db.execute_insert(
                EVENT_REGISTRATION_QUERIES['create'],
                (event_id, user_id, status)
            )
            return cls.get_by_id(registration_id)
        except Exception as e:
            logger.error(f"创建活动报名失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, registration_id):
        """根据ID获取报名信息"""
        try:
            return db.execute_query(
                EVENT_REGISTRATION_QUERIES['get_by_id'], 
                (registration_id,), 
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"获取报名信息失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_event_and_user(cls, event_id, user_id):
        """根据活动和用户获取报名信息"""
        try:
            return db.execute_query(
                EVENT_REGISTRATION_QUERIES['get_by_event_and_user'], 
                (event_id, user_id), 
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"获取报名信息失败: {str(e)}")
            return None
    
    @classmethod
    def update_status(cls, registration_id, status):
        """更新报名状态"""
        try:
            db.execute_update(EVENT_REGISTRATION_QUERIES['update_status'], (status, registration_id))
            return cls.get_by_id(registration_id)
        except Exception as e:
            logger.error(f"更新报名状态失败: {str(e)}")
            return None
    
    @classmethod
    def delete(cls, registration_id):
        """删除报名记录"""
        try:
            return db.execute_update(EVENT_REGISTRATION_QUERIES['delete'], (registration_id,))
        except Exception as e:
            logger.error(f"删除报名记录失败: {str(e)}")
            return 0
    
    @classmethod
    def list_by_event(cls, event_id):
        """列出活动的所有报名记录"""
        try:
            # 打印执行的SQL语句和参数，用于调试
            logger.info(f"执行SQL: {EVENT_REGISTRATION_QUERIES['list_by_event']} 参数: {event_id}")
            
            results = db.execute_query(EVENT_REGISTRATION_QUERIES['list_by_event'], (event_id,))
            
            # 打印原始结果用于调试
            logger.info(f"查询原始结果数量: {len(results)}")
            if results and len(results) > 0:
                logger.info(f"第一条记录示例: {results[0]}")
            
            # 确保结果被正确格式化，处理潜在的None值
            formatted_results = []
            for row in results:
                # 转换datetime对象为字符串
                formatted_row = cls.format_dict(row)
                # 确保身高、体重和鞋码字段显示，即使为NULL也要转换为可显示的值
                if formatted_row.get('height') is None:
                    formatted_row['height'] = ''
                if formatted_row.get('weight') is None:
                    formatted_row['weight'] = ''
                if formatted_row.get('shoe_size') is None:
                    formatted_row['shoe_size'] = ''
                    
                logger.debug(f"格式化后记录: height={formatted_row.get('height')}, weight={formatted_row.get('weight')}, shoe_size={formatted_row.get('shoe_size')}")
                formatted_results.append(formatted_row)
            
            logger.info(f"成功获取活动 {event_id} 的报名列表: {len(formatted_results)} 条记录")
            return formatted_results
        except Exception as e:
            logger.error(f"获取活动报名列表失败: {str(e)}")
            return []
    
    @classmethod
    def list_by_user(cls, user_id):
        """列出用户的所有报名记录"""
        try:
            return db.execute_query(EVENT_REGISTRATION_QUERIES['list_by_user'], (user_id,))
        except Exception as e:
            logger.error(f"获取用户报名列表失败: {str(e)}")
            return []

class FlagRecord(BaseModel):
    """升降旗记录模型"""
    
    @classmethod
    def create(cls, user_id, date, type, photo_url, status='pending'):
        """创建升降旗记录"""
        try:
            logger.info(f"创建升降旗记录: user_id={user_id}, date={date}, type={type}, photo_url={photo_url}, status={status}")
            
            # 转换日期格式
            if isinstance(date, str):
                try:
                    date = datetime.strptime(date, '%Y-%m-%d').date()
                except ValueError as e:
                    logger.error(f"日期格式错误: {str(e)}")
                    # 使用当前日期作为默认值
                    date = datetime.now().date()
            
            record_id = db.execute_insert(
                FLAG_RECORD_QUERIES['create'],
                (user_id, date, type, photo_url, status)
            )
            
            logger.info(f"升降旗记录创建成功，ID: {record_id}")
            return cls.get_by_id(record_id)
        except Exception as e:
            logger.error(f"创建升降旗记录失败: {str(e)}")
            logger.exception(e)
            return None
    
    @classmethod
    def get_by_id(cls, record_id):
        """根据ID获取升降旗记录"""
        try:
            result = db.execute_query(FLAG_RECORD_QUERIES['get_by_id'], (record_id,), fetch_one=True)
            if result:
                # 转换datetime对象为字符串
                return cls.format_dict(result)
            return None
        except Exception as e:
            logger.error(f"获取升降旗记录失败: {str(e)}")
            logger.exception(e)
            return None
    
    @classmethod
    def update(cls, record_id, date, type, photo_url):
        """更新升降旗记录"""
        try:
            db.execute_update(
                FLAG_RECORD_QUERIES['update'],
                (date, type, photo_url, record_id)
            )
            return cls.get_by_id(record_id)
        except Exception as e:
            logger.error(f"更新升降旗记录失败: {str(e)}")
            return None
    
    @classmethod
    def review(cls, record_id, status, points_awarded, reviewer_id):
        """审核升降旗记录"""
        try:
            logger.info(f"审核升降旗记录: record_id={record_id}, status={status}, points_awarded={points_awarded}, reviewer_id={reviewer_id}")
            db.execute_update(
                FLAG_RECORD_QUERIES['review'],
                (status, points_awarded, reviewer_id, record_id)
            )
            return cls.get_by_id(record_id)
        except Exception as e:
            logger.error(f"审核升降旗记录失败: {str(e)}")
            logger.exception(e)
            return None
    
    @classmethod
    def delete(cls, record_id):
        """删除升降旗记录"""
        try:
            return db.execute_update(FLAG_RECORD_QUERIES['delete'], (record_id,))
        except Exception as e:
            logger.error(f"删除升降旗记录失败: {str(e)}")
            return 0
    
    @classmethod
    def list_by_user(cls, user_id):
        """列出用户的所有升降旗记录"""
        try:
            logger.info(f"获取用户 {user_id} 的升降旗记录")
            results = db.execute_query(FLAG_RECORD_QUERIES['list_by_user'], (user_id,))
            
            # 确保结果被正确格式化，处理潜在的None值
            formatted_results = []
            for row in results:
                if row is None:
                    logger.warning("遇到None记录，已跳过")
                    continue
                    
                # 转换datetime对象为字符串
                formatted_row = cls.format_dict(row)
                
                # 确保所有必需的字段都存在
                if 'record_id' not in formatted_row or formatted_row['record_id'] is None:
                    logger.warning(f"记录缺少record_id: {formatted_row}")
                    continue
                
                if 'status' not in formatted_row or formatted_row['status'] is None:
                    formatted_row['status'] = 'pending'
                
                if 'points_awarded' not in formatted_row or formatted_row['points_awarded'] is None:
                    formatted_row['points_awarded'] = 0
                
                formatted_results.append(formatted_row)
            
            logger.info(f"成功获取用户 {user_id} 的升降旗记录: {len(formatted_results)} 条记录")
            return formatted_results
        except Exception as e:
            logger.error(f"获取用户升降旗记录失败: {str(e)}")
            logger.exception(e)
            return []
    
    @classmethod
    def list_all(cls):
        """列出所有升降旗记录"""
        try:
            logger.info("获取所有升降旗记录")
            results = db.execute_query(FLAG_RECORD_QUERIES['list_all'])
            
            # 确保结果被正确格式化，处理潜在的None值
            formatted_results = []
            for row in results:
                if row is None:
                    logger.warning("遇到None记录，已跳过")
                    continue
                    
                # 转换datetime对象为字符串
                formatted_row = cls.format_dict(row)
                
                # 确保所有必需的字段都存在
                if 'record_id' not in formatted_row or formatted_row['record_id'] is None:
                    logger.warning(f"记录缺少record_id: {formatted_row}")
                    continue
                
                if 'status' not in formatted_row or formatted_row['status'] is None:
                    formatted_row['status'] = 'pending'
                
                if 'points_awarded' not in formatted_row or formatted_row['points_awarded'] is None:
                    formatted_row['points_awarded'] = 0
                
                # 构建统一的用户对象格式
                formatted_row['user'] = {
                    'name': formatted_row.get('user_name', 'Unknown'),
                    'student_id': formatted_row.get('student_id', '')
                }
                
                formatted_results.append(formatted_row)
            
            logger.info(f"成功获取所有升降旗记录: {len(formatted_results)} 条记录")
            return formatted_results
        except Exception as e:
            logger.error(f"获取所有升降旗记录失败: {str(e)}")
            logger.exception(e)
            return []
    
    @classmethod
    def list_pending(cls):
        """列出所有待审核的升降旗记录"""
        try:
            results = db.execute_query(FLAG_RECORD_QUERIES['list_pending'])
            
            # 确保结果被正确格式化，处理潜在的None值
            formatted_results = []
            for row in results:
                # 转换datetime对象为字符串
                formatted_row = cls.format_dict(row)
                formatted_results.append(formatted_row)
            
            logger.info(f"成功获取待审核升降旗记录: {len(formatted_results)} 条记录")
            return formatted_results
        except Exception as e:
            logger.error(f"获取待审核升降旗记录失败: {str(e)}")
            logger.exception(e)
            return []

class PointHistory(BaseModel):
    """积分历史记录模型"""
    
    @classmethod
    def create(cls, user_id, points_change, change_type, description, related_id=None):
        """创建积分历史记录"""
        try:
            history_id = db.execute_insert(
                POINT_HISTORY_QUERIES['create'],
                (user_id, points_change, change_type, description, related_id)
            )
            return cls.get_by_id(history_id)
        except Exception as e:
            logger.error(f"创建积分历史记录失败: {str(e)}")
            return None
    
    @classmethod
    def get_by_id(cls, history_id):
        """根据ID获取积分历史记录"""
        try:
            return db.execute_query(
                POINT_HISTORY_QUERIES['get_by_id'], 
                (history_id,), 
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"获取积分历史记录失败: {str(e)}")
            return None
    
    @classmethod
    def list_by_user(cls, user_id):
        """列出用户的所有积分历史记录"""
        try:
            return db.execute_query(POINT_HISTORY_QUERIES['list_by_user'], (user_id,))
        except Exception as e:
            logger.error(f"获取用户积分历史记录失败: {str(e)}")
            return []
    
    @classmethod
    def list_all(cls):
        """列出所有积分历史记录"""
        try:
            return db.execute_query(POINT_HISTORY_QUERIES['list_all'])
        except Exception as e:
            logger.error(f"获取所有积分历史记录失败: {str(e)}")
            return []
    
    @classmethod
    def get_user_total(cls, user_id):
        """获取用户总积分"""
        try:
            logger.info(f"获取用户 {user_id} 的总积分")
            result = db.execute_query(
                POINT_HISTORY_QUERIES['get_user_total'], 
                (user_id,), 
                fetch_one=True
            )
            
            # 确保结果存在且不为None
            total_points = 0.0
            if result and result.get('total_points') is not None:
                total_points = float(result['total_points'])
            logger.info(f"用户 {user_id} 的总积分: {total_points}")
            return total_points
        except Exception as e:
            logger.error(f"获取用户总积分失败: {str(e)}")
            logger.exception(e)
            return 0.0

class OperationLog(BaseModel):
    """操作日志模型"""
    
    @classmethod
    def create(cls, user_id, endpoint, method, ip_address):
        """创建操作日志"""
        try:
            return db.execute_insert(
                OPERATION_LOG_QUERIES['create'],
                (user_id, endpoint, method, ip_address)
            )
        except Exception as e:
            logger.error(f"创建操作日志失败: {str(e)}")
            return None
    
    @classmethod
    def list_recent(cls, limit=100):
        """列出最近的操作日志"""
        try:
            return db.execute_query(OPERATION_LOG_QUERIES['list_recent'], (limit,))
        except Exception as e:
            logger.error(f"获取最近操作日志失败: {str(e)}")
            return [] 