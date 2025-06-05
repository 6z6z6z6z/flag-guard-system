from app import create_app
from models import User, Training, Event, FlagRecord, PointHistory, TrainingRegistration, EventRegistration
from extensions import db

def clear_data():
    app = create_app()
    with app.app_context():
        # 按照依赖关系的顺序删除数据
        PointHistory.query.delete()
        FlagRecord.query.delete()
        TrainingRegistration.query.delete()
        EventRegistration.query.delete()
        Training.query.delete()
        Event.query.delete()
        User.query.delete()
        
        # 提交更改
        db.session.commit()
        print("所有数据已清空！")

if __name__ == '__main__':
    clear_data() 