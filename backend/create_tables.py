import sys
from os.path import dirname, abspath
sys.path.append(dirname(dirname(abspath(__file__))))

from app import create_app
from extensions import db
from models import TrainingRegistration, Event
from sqlalchemy import text, inspect

app = create_app()

def column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

with app.app_context():
    # 删除所有表
    db.drop_all()
    # 创建所有表
    db.create_all()
    
    with db.engine.connect() as conn:
        # 确保 training_registrations 表有 attendance_status 列
        if not column_exists(conn, 'training_registrations', 'attendance_status'):
            conn.execute(text('ALTER TABLE training_registrations ADD COLUMN attendance_status VARCHAR(20)'))
            print("添加 attendance_status 列成功")
        
        # 确保 trainings 表有 created_at 和 updated_at 列
        if not column_exists(conn, 'trainings', 'created_at'):
            conn.execute(text('ALTER TABLE trainings ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            print("添加 created_at 列成功")
        
        if not column_exists(conn, 'trainings', 'updated_at'):
            conn.execute(text('ALTER TABLE trainings ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
            print("添加 updated_at 列成功")
        
        # 确保 events 表有所有必需的列
        if not column_exists(conn, 'events', 'time'):
            conn.execute(text('ALTER TABLE events ADD COLUMN time DATETIME'))
            print("添加 time 列成功")
        
        if not column_exists(conn, 'events', 'location'):
            conn.execute(text('ALTER TABLE events ADD COLUMN location VARCHAR(100)'))
            print("添加 location 列成功")
        
        if not column_exists(conn, 'events', 'uniform_required'):
            conn.execute(text('ALTER TABLE events ADD COLUMN uniform_required VARCHAR(255)'))
            print("添加 uniform_required 列成功")
        
        if not column_exists(conn, 'events', 'created_at'):
            conn.execute(text('ALTER TABLE events ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            print("添加 created_at 列成功")
        
        conn.commit()
    
    print("数据库表已重新创建")