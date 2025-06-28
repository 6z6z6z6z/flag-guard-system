from app import create_app, db
from models import User, PointHistory, FlagRecord, Event, Training, EventRegistration, TrainingRegistration
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_admin():
    """创建默认管理员账号"""
    try:
        # 检查是否已存在管理员账号
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info("默认管理员账号已存在")
            return
        
        # 创建管理员账号
        admin = User(
            username='admin',
            name='系统管理员',
            role='superadmin',
            student_id='admin001',
            college='系统管理',
            total_points=0
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logger.info("默认管理员账号创建成功")
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建默认管理员账号失败: {str(e)}")
        raise

def clear_all_data():
    """清除所有数据"""
    app = create_app()
    with app.app_context():
        try:
            # 开始事务
            logger.info("开始清除数据...")
            
            # 清除所有表的数据
            logger.info("正在清除积分历史记录...")
            PointHistory.query.delete()
            
            logger.info("正在清除Flag记录...")
            FlagRecord.query.delete()
            
            logger.info("正在清除活动报名记录...")
            EventRegistration.query.delete()
            
            logger.info("正在清除培训报名记录...")
            TrainingRegistration.query.delete()
            
            logger.info("正在清除活动记录...")
            Event.query.delete()
            
            logger.info("正在清除培训记录...")
            Training.query.delete()
            
            logger.info("正在清除用户数据...")
            User.query.delete()
            
            # 重置自增ID
            logger.info("正在重置自增ID...")
            tables = [
                'users',
                'point_history',
                'flag_records',
                'events',
                'trainings',
                'event_registrations',
                'training_registrations'
            ]
            
            for table in tables:
                db.session.execute(text(f'ALTER TABLE {table} AUTO_INCREMENT = 1'))
            
            # 提交事务
            db.session.commit()
            logger.info("数据清除完成！")
            
            # 创建默认管理员账号
            logger.info("正在创建默认管理员账号...")
            create_default_admin()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"清除数据失败: {str(e)}")
            raise

if __name__ == '__main__':
    # 显示警告信息
    print("警告：此操作将清除系统中的所有数据！")
    print("请确保你已经备份了重要数据。")
    confirm = input("是否继续？(yes/no): ")
    
    if confirm.lower() == 'yes':
        clear_all_data()
    else:
        print("操作已取消。") 