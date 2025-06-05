import click
from flask import Flask
from flask.cli import with_appcontext
from extensions import db
from models import User, FlagRecord, Training, Event, PointHistory
from datetime import datetime, timedelta
import logging
import json
import os
import shutil
from config import Config

logger = logging.getLogger(__name__)

def create_app():
    """创建CLI专用的应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

app = create_app()

@app.cli.command('init-db')
@with_appcontext
def init_db():
    """初始化数据库"""
    try:
        db.create_all()
        click.echo('数据库表已创建')
    except Exception as e:
        click.echo(f'初始化数据库失败: {str(e)}')

@app.cli.command('drop-db')
@with_appcontext
def drop_db():
    """删除所有数据库表"""
    if click.confirm('确定要删除所有数据库表吗？此操作不可恢复！'):
        try:
            db.drop_all()
            click.echo('数据库表已删除')
        except Exception as e:
            click.echo(f'删除数据库表失败: {str(e)}')

@app.cli.command('create-admin')
@click.argument('username')
@click.argument('password')
@click.argument('name')
@click.argument('student_id')
@click.option('--college', default='系统管理', help='所属学院')
@with_appcontext
def create_admin(username, password, name, student_id, college):
    """创建管理员用户"""
    try:
        if User.query.filter_by(username=username).first():
            click.echo(f'用户名 {username} 已存在')
            return
        if User.query.filter_by(student_id=student_id).first():
            click.echo(f'学号 {student_id} 已存在')
            return
            
        admin = User(
            username=username,
            name=name,
            student_id=student_id,
            role='admin',
            college=college
        )
        
        # 设置密码并验证
        if not admin.set_password(password):
            click.echo('设置密码失败')
            return
            
        # 验证密码是否正确设置
        if not admin.check_password(password):
            click.echo('密码验证失败')
            return
            
        db.session.add(admin)
        db.session.commit()
        
        # 验证用户是否成功创建
        created_user = User.query.filter_by(username=username).first()
        if created_user and created_user.check_password(password):
            click.echo(f'管理员用户 {username} 创建成功')
            click.echo(f'用户ID: {created_user.user_id}')
            click.echo(f'角色: {created_user.role}')
        else:
            click.echo('用户创建后验证失败')
            
    except Exception as e:
        db.session.rollback()
        click.echo(f'创建管理员用户失败: {str(e)}')

@app.cli.command('list-users')
@click.option('--role', help='按角色筛选')
@with_appcontext
def list_users(role):
    """列出所有用户"""
    try:
        query = User.query
        if role:
            query = query.filter_by(role=role)
        users = query.all()
        
        if not users:
            click.echo('没有找到用户')
            return
            
        for user in users:
            click.echo(f'ID: {user.user_id}, 用户名: {user.username}, 角色: {user.role}, '
                      f'姓名: {user.name}, 学号: {user.student_id}, 学院: {user.college}')
    except Exception as e:
        click.echo(f'列出用户失败: {str(e)}')

@app.cli.command('cleanup-records')
@click.option('--days', default=30, help='清理多少天前的记录')
@click.option('--dry-run', is_flag=True, help='仅显示将要删除的记录，不实际删除')
@with_appcontext
def cleanup_records(days, dry_run):
    """清理旧记录"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    try:
        # 统计要删除的记录
        flag_count = FlagRecord.query.filter(FlagRecord.created_at < cutoff_date).count()
        point_count = PointHistory.query.filter(PointHistory.change_time < cutoff_date).count()
        
        if dry_run:
            click.echo(f'将要删除 {days} 天前的记录:')
            click.echo(f'- 升降旗记录: {flag_count} 条')
            click.echo(f'- 积分历史: {point_count} 条')
            return
            
        # 清理旧的升降旗记录
        FlagRecord.query.filter(FlagRecord.created_at < cutoff_date).delete()
        # 清理旧的积分历史
        PointHistory.query.filter(PointHistory.change_time < cutoff_date).delete()
        db.session.commit()
        click.echo(f'已清理 {days} 天前的记录:')
        click.echo(f'- 升降旗记录: {flag_count} 条')
        click.echo(f'- 积分历史: {point_count} 条')
    except Exception as e:
        db.session.rollback()
        click.echo(f'清理记录失败: {str(e)}')

@app.cli.command('backup-db')
@click.argument('backup_path')
@with_appcontext
def backup_db(backup_path):
    """备份数据库"""
    try:
        # 确保备份目录存在
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # 复制数据库文件
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            shutil.copy2(db_path, backup_path)
            click.echo(f'数据库已备份到 {backup_path}')
        else:
            click.echo('目前只支持 SQLite 数据库的备份')
    except Exception as e:
        click.echo(f'备份数据库失败: {str(e)}')

@app.cli.command('check-system')
@with_appcontext
def check_system():
    """检查系统状态"""
    try:
        # 检查数据库连接
        db.session.execute('SELECT 1')
        click.echo('数据库连接正常')
        
        # 检查用户数量
        user_count = User.query.count()
        click.echo(f'系统中共有 {user_count} 个用户')
        
        # 检查管理员数量
        admin_count = User.query.filter_by(role='admin').count()
        click.echo(f'系统中共有 {admin_count} 个管理员')
        
        # 检查最近的记录
        recent_flags = FlagRecord.query.order_by(FlagRecord.created_at.desc()).limit(5).all()
        click.echo('最近的升降旗记录:')
        for flag in recent_flags:
            click.echo(f'- {flag.date}: {flag.type} ({flag.status})')
        
        # 检查积分统计
        total_points = db.session.query(db.func.sum(User.total_points)).scalar() or 0
        click.echo(f'系统总积分: {total_points}')
        
    except Exception as e:
        click.echo(f'系统检查失败: {str(e)}')

@app.cli.command('reset-password')
@click.argument('username')
@click.argument('new_password')
@with_appcontext
def reset_password(username, new_password):
    """重置用户密码"""
    try:
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            click.echo(f'用户 {username} 的密码已重置')
        else:
            click.echo(f'用户 {username} 不存在')
    except Exception as e:
        db.session.rollback()
        click.echo(f'重置密码失败: {str(e)}')

@app.cli.command('export-data')
@click.argument('export_path')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json', help='导出格式')
@with_appcontext
def export_data(export_path, format):
    """导出系统数据"""
    try:
        data = {
            'users': [user.to_dict() for user in User.query.all()],
            'flag_records': [record.to_dict() for record in FlagRecord.query.all()],
            'trainings': [training.to_dict() for training in Training.query.all()],
            'events': [event.to_dict() for event in Event.query.all()],
            'point_history': [history.to_dict() for history in PointHistory.query.all()]
        }
        
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        if format == 'json':
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            # TODO: 实现 CSV 导出
            click.echo('CSV 导出功能尚未实现')
            return
            
        click.echo(f'数据已导出到 {export_path}')
    except Exception as e:
        click.echo(f'导出数据失败: {str(e)}')