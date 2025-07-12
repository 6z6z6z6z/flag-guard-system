"""
时间处理工具模块
统一处理系统中的时间转换，确保所有时间都按照东八区（北京时间）处理
"""
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# 定义东八区时区
BEIJING_TZ = timezone(timedelta(hours=8))

class TimeUtils:
    """时间处理工具类"""
    
    @staticmethod
    def now_beijing():
        """获取当前北京时间"""
        return datetime.now(BEIJING_TZ)
    
    @staticmethod
    def to_beijing_time(dt):
        """将时间转换为北京时间
        
        Args:
            dt: datetime对象或时间字符串
            
        Returns:
            带有北京时区信息的datetime对象
        """
        if dt is None:
            return None
            
        if isinstance(dt, str):
            # 解析字符串时间
            try:
                if dt.endswith('Z'):
                    # UTC时间
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                elif '+' in dt or dt.endswith('00'):
                    # 已包含时区信息
                    dt = datetime.fromisoformat(dt)
                else:
                    # 假设为北京时间字符串，添加时区信息
                    dt = datetime.fromisoformat(dt)
                    dt = dt.replace(tzinfo=BEIJING_TZ)
            except Exception as e:
                logger.error(f"解析时间字符串失败: {dt}, 错误: {e}")
                return None
        
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                # 无时区信息，假设为北京时间
                return dt.replace(tzinfo=BEIJING_TZ)
            else:
                # 转换为北京时间
                return dt.astimezone(BEIJING_TZ)
        
        return None
    
    @staticmethod
    def to_utc_for_storage(dt):
        """将北京时间转换为UTC时间用于数据库存储
        
        Args:
            dt: datetime对象（假设为北京时间）
            
        Returns:
            UTC时间的datetime对象
        """
        if dt is None:
            return None
            
        if isinstance(dt, str):
            # 先转换为北京时间，再转UTC
            dt = TimeUtils.to_beijing_time(dt)
            
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                # 假设为北京时间
                dt = dt.replace(tzinfo=BEIJING_TZ)
            # 转换为UTC时间
            return dt.astimezone(timezone.utc)
        
        return None
    
    @staticmethod
    def from_db_to_beijing(dt):
        """从数据库读取的时间转换为北京时间
        
        Args:
            dt: 从数据库读取的datetime对象
            
        Returns:
            北京时间的datetime对象
        """
        if dt is None:
            return None
            
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                # 数据库中的时间假设为UTC，转换为北京时间
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(BEIJING_TZ)
        
        return dt
    
    @staticmethod
    def format_for_frontend(dt):
        """格式化时间用于前端显示
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化的时间字符串（北京时间）
        """
        if dt is None:
            return None
            
        beijing_dt = TimeUtils.to_beijing_time(dt)
        if beijing_dt:
            return beijing_dt.strftime('%Y-%m-%d %H:%M:%S')
        return None
    
    @staticmethod
    def format_for_frontend_iso(dt):
        """格式化时间为ISO格式用于前端显示
        
        Args:
            dt: datetime对象
            
        Returns:
            ISO格式的时间字符串（北京时间）
        """
        if dt is None:
            return None
            
        beijing_dt = TimeUtils.to_beijing_time(dt)
        if beijing_dt:
            return beijing_dt.isoformat()
        return None
    
    @staticmethod
    def is_past(dt):
        """判断时间是否已过期（基于北京时间）
        
        Args:
            dt: datetime对象或时间字符串
            
        Returns:
            bool: True表示已过期
        """
        beijing_dt = TimeUtils.to_beijing_time(dt)
        if beijing_dt is None:
            return False
        
        current_time = TimeUtils.now_beijing()
        return beijing_dt < current_time
    
    @staticmethod
    def parse_frontend_time(time_str):
        """解析前端传来的时间字符串（假设为北京时间）
        
        Args:
            time_str: 前端传来的时间字符串
            
        Returns:
            带有北京时区信息的datetime对象
        """
        if not time_str:
            return None
            
        try:
            # 移除时区后缀，因为前端传来的就是北京时间
            if time_str.endswith('Z'):
                time_str = time_str[:-1]
            if '+' in time_str:
                time_str = time_str.split('+')[0]
            
            # 解析时间并添加北京时区
            # 处理各种可能的格式
            if 'T' in time_str:
                dt = datetime.fromisoformat(time_str)
            else:
                dt = datetime.fromisoformat(time_str.replace(' ', 'T'))
            
            # 如果没有时区信息，添加北京时区
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=BEIJING_TZ)
            
            return dt
        except Exception as e:
            logger.error(f"解析前端时间失败: {time_str}, 错误: {e}")
            return None
