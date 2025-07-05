import click
from flask import Flask
from flask.cli import with_appcontext
from db_connection import db
from models_pymysql import User, FlagRecord, Training, Event, PointHistory, OperationLog
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
    return app

app = create_app()

@app.cli.command('init-db')
@with_appcontext
def init_db():
    """初始化数据库"""
    try:
        # 读取并执行schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'sql', 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # 按分号分割SQL语句并执行
        sql_statements = schema_sql.split(';')
        for statement in sql_statements:
            if statement.strip():
                db.execute_update(statement)
                
        click.echo('数据库表已创建')
    except Exception as e:
        click.echo(f'初始化数据库失败: {str(e)}')

@app.cli.command('drop-db')
@click.option('--yes', is_flag=True, help='Skip confirmation.')
@with_appcontext
def drop_db(yes):
    """删除所有数据库表"""
    if yes or click.confirm('确定要删除所有数据库表吗？此操作不可恢复！'):
        try:
            # 针对MySQL，临时禁用外键检查
            db.execute_update('SET FOREIGN_KEY_CHECKS=0;')
            
            # 获取所有表名
            tables = db.execute_query("SHOW TABLES")
            for table in tables:
                table_name = list(table.values())[0]
                db.execute_update(f"DROP TABLE IF EXISTS `{table_name}`")
            
            # 恢复外键检查
            db.execute_update('SET FOREIGN_KEY_CHECKS=1;')
            click.echo('数据库表已删除')
        except Exception as e:
            click.echo(f'删除数据库表失败: {str(e)}')

@app.cli.command('create-user')
@click.argument('username')
@click.argument('password')
@click.argument('name')
@click.argument('student_id')
@click.option('--college', default='系统管理', help='所属学院')
@click.option('--role', type=click.Choice(['member', 'admin', 'superadmin']), default='member', help='用户角色')
@with_appcontext
def create_user(username, password, name, student_id, college, role):
    """创建用户"""
    try:
        # 检查用户名是否存在
        if User.get_by_username(username):
            click.echo(f'用户名 {username} 已存在')
            return
            
        # 检查学号是否存在
        if User.get_by_student_id(student_id):
            click.echo(f'学号 {student_id} 已存在')
            return
            
        # 创建用户
        user = User.create(
            username=username,
            password=password,
            role=role,
            name=name,
            student_id=student_id,
            college=college
        )
        
        if user:
            click.echo(f'用户 {username} 创建成功')
            click.echo(f'用户ID: {user["user_id"]}')
            click.echo(f'角色: {user["role"]}')
        else:
            click.echo('用户创建失败')
            
    except Exception as e:
        click.echo(f'创建用户失败: {str(e)}')

@app.cli.command('delete-user')
@click.argument('username')
@with_appcontext
def delete_user(username):
    """删除用户"""
    try:
        user = User.get_by_username(username)
        if user:
            result = User.delete(user['user_id'])
            if result:
                click.echo(f'用户 {username} 已删除')
            else:
                click.echo(f'删除用户 {username} 失败')
        else:
            click.echo(f'用户 {username} 不存在')
    except Exception as e:
        click.echo(f'删除用户失败: {str(e)}')

@app.cli.command('list-users')
@click.option('--role', help='按角色筛选')
@with_appcontext
def list_users(role):
    """列出所有用户"""
    try:
        users = User.list_all()
        
        # 根据角色筛选
        if role:
            users = [user for user in users if user['role'] == role]
        
        if not users:
            click.echo('没有找到用户')
            return
            
        for user in users:
            click.echo(f'ID: {user["user_id"]}, 用户名: {user["username"]}, 角色: {user["role"]}, '
                      f'姓名: {user["name"]}, 学号: {user["student_id"]}, 学院: {user["college"]}')
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
        flag_count = db.execute_query(
            "SELECT COUNT(*) as count FROM flag_records WHERE created_at < %s",
            (cutoff_date,), fetch_one=True
        )['count']
        
        point_count = db.execute_query(
            "SELECT COUNT(*) as count FROM point_history WHERE change_time < %s",
            (cutoff_date,), fetch_one=True
        )['count']
        
        if dry_run:
            click.echo(f'将要删除 {days} 天前的记录:')
            click.echo(f'- 升降旗记录: {flag_count} 条')
            click.echo(f'- 积分历史: {point_count} 条')
            return
            
        # 清理旧的升降旗记录
        db.execute_update(
            "DELETE FROM flag_records WHERE created_at < %s",
            (cutoff_date,)
        )
        
        # 清理旧的积分历史
        db.execute_update(
            "DELETE FROM point_history WHERE change_time < %s",
            (cutoff_date,)
        )
        
        click.echo(f'已清理 {days} 天前的记录:')
        click.echo(f'- 升降旗记录: {flag_count} 条')
        click.echo(f'- 积分历史: {point_count} 条')
    except Exception as e:
        click.echo(f'清理记录失败: {str(e)}')

@app.cli.command('backup-db')
@click.argument('backup_path')
@with_appcontext
def backup_db(backup_path):
    """备份数据库"""
    try:
        # 确保备份目录存在
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # 获取数据库连接信息
        host = app.config['MYSQL_HOST']
        user = app.config['MYSQL_USER']
        password = app.config['MYSQL_PASSWORD']
        db_name = app.config['MYSQL_DATABASE']
        
        # 使用 mysqldump 命令备份
        import subprocess
        cmd = f'mysqldump -h {host} -u {user} -p{password} {db_name} > {backup_path}'
        subprocess.run(cmd, shell=True, check=True)
        click.echo(f'MySQL数据库已备份到 {backup_path}')
    except Exception as e:
        click.echo(f'数据库备份失败: {str(e)}')

@app.cli.command('check-system')
@with_appcontext
def check_system():
    """系统健康检查"""
    try:
        # 检查数据库连接
        try:
            db.get_connection()
            click.echo('✅ 数据库连接正常')
        except Exception as e:
            click.echo(f'❌ 数据库连接失败: {str(e)}')
            return
            
        # 检查表是否存在
        tables = ['users', 'trainings', 'training_registrations', 'events', 
                  'event_registrations', 'flag_records', 'point_history', 'operation_logs']
        missing_tables = []
        
        for table in tables:
            result = db.execute_query(
                f"SHOW TABLES LIKE '{table}'"
            )
            if not result:
                missing_tables.append(table)
                
        if missing_tables:
            click.echo(f'❌ 缺少以下数据表: {", ".join(missing_tables)}')
        else:
            click.echo('✅ 所有数据表存在')
            
        # 显示统计信息
        user_count = db.execute_query("SELECT COUNT(*) as count FROM users", fetch_one=True)['count']
        training_count = db.execute_query("SELECT COUNT(*) as count FROM trainings", fetch_one=True)['count']
        event_count = db.execute_query("SELECT COUNT(*) as count FROM events", fetch_one=True)['count']
        flag_count = db.execute_query("SELECT COUNT(*) as count FROM flag_records", fetch_one=True)['count']
        
        click.echo('\n系统统计信息:')
        click.echo(f'- 用户数量: {user_count}')
        click.echo(f'- 训练数量: {training_count}')
        click.echo(f'- 活动数量: {event_count}')
        click.echo(f'- 升降旗记录: {flag_count}')
        
    except Exception as e:
        click.echo(f'系统检查失败: {str(e)}')

@app.cli.command('reset-password')
@click.argument('username')
@click.argument('new_password')
@with_appcontext
def reset_password(username, new_password):
    """重置用户密码"""
    try:
        user = User.get_by_username(username)
        if not user:
            click.echo(f'用户 {username} 不存在')
            return
            
        if User.set_password(user['user_id'], new_password):
            click.echo(f'用户 {username} 密码已重置')
        else:
            click.echo(f'重置 {username} 密码失败')
            
    except Exception as e:
        click.echo(f'重置密码失败: {str(e)}')

@app.cli.command('export-data')
@click.argument('export_path')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json', help='导出格式')
@with_appcontext
def export_data(export_path, format):
    """导出数据"""
    try:
        # 确保导出目录存在
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        # 获取要导出的数据
        users = User.list_all()
        trainings = Training.list_all()
        events = Event.list_all()
        flag_records = FlagRecord.list_all()
        point_history = PointHistory.list_all()
        
        # 准备导出数据
        export_data = {
            'users': users,
            'trainings': trainings,
            'events': events,
            'flag_records': flag_records,
            'point_history': point_history,
            'export_time': datetime.utcnow().isoformat()
        }
        
        if format == 'json':
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            click.echo(f'数据已导出为JSON格式: {export_path}')
        else:
            click.echo('CSV导出格式暂不支持')
            
    except Exception as e:
        click.echo(f'导出数据失败: {str(e)}')

def init_cli(app):
    """初始化CLI命令"""
    app.cli.add_command(init_db)
    app.cli.add_command(drop_db)
    app.cli.add_command(create_user)
    app.cli.add_command(delete_user)
    app.cli.add_command(list_users)
    app.cli.add_command(cleanup_records)
    app.cli.add_command(backup_db)
    app.cli.add_command(check_system)
    app.cli.add_command(reset_password)
    app.cli.add_command(export_data)