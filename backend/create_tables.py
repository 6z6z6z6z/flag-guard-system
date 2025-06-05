import sys
from os.path import dirname, abspath
sys.path.append(dirname(dirname(abspath(__file__))))

from app import create_app
from extensions import db
from models import TrainingRegistration

app = create_app()

with app.app_context():
    # 删除所有表
    db.drop_all()
    # 创建所有表
    db.create_all()
    
    # 确保 training_registrations 表有 attendance_status 列
    if not hasattr(TrainingRegistration, 'attendance_status'):
        db.engine.execute('ALTER TABLE training_registrations ADD COLUMN attendance_status VARCHAR(20)')
    
    print("数据库表已重新创建")