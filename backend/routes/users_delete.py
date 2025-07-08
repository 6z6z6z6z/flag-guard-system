from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models_pymysql import User
from db_connection import db
from utils.route_utils import APIResponse, role_required, handle_exceptions

# 创建一个新的蓝图
user_delete_bp = Blueprint('user_delete', __name__)

@user_delete_bp.route('/', methods=['POST'])
@jwt_required()
@role_required('superadmin')
@handle_exceptions
def delete_user():
    """
    删除用户（仅超级管理员）
    ---
    tags:
      - 用户
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
              description: 要删除的用户ID
    responses:
      200:
        description: 删除成功
      403:
        description: 权限不足
      404:
        description: 用户不存在
      500:
        description: 服务器错误
    """
    current_app.logger.info("收到删除用户请求")
    
    # 解析请求数据
    data = request.get_json()
    if not data or 'user_id' not in data:
        current_app.logger.error("缺少user_id参数")
        return APIResponse.error("缺少用户ID", 400)
    
    user_id = data.get('user_id')
    current_app.logger.info(f"尝试删除用户ID: {user_id}")
    
    # 获取当前用户身份
    current_user_id = get_jwt_identity()
    
    # 不允许删除自己
    if int(current_user_id) == int(user_id):
        return APIResponse.error("不能删除自己的账号", 403)
    
    # 获取用户
    user = User.get_by_id(int(user_id))
    if not user:
        return APIResponse.error("用户不存在", 404)
    
    # 不允许删除超级管理员
    if user['role'] == 'superadmin':
        return APIResponse.error("不能删除超级管理员账号", 403)
    
    try:
        # 直接使用SQL删除用户及其相关数据
        conn = db.connect()
        cursor = conn.cursor()
        
        # 开始删除用户相关数据
        try:
            # 1. 删除用户的积分历史记录
            cursor.execute("DELETE FROM point_history WHERE user_id = %s", (user_id,))
            point_history_count = cursor.rowcount
            current_app.logger.info(f"已删除 {point_history_count} 条积分历史记录")
            
            # 2. 删除用户的训练报名记录
            cursor.execute("DELETE FROM training_registrations WHERE user_id = %s", (user_id,))
            training_reg_count = cursor.rowcount
            current_app.logger.info(f"已删除 {training_reg_count} 条训练报名记录")
            
            # 3. 删除用户的活动报名记录
            cursor.execute("DELETE FROM event_registrations WHERE user_id = %s", (user_id,))
            event_reg_count = cursor.rowcount
            current_app.logger.info(f"已删除 {event_reg_count} 条活动报名记录")
            
            # 4. 删除用户的升降旗记录
            cursor.execute("DELETE FROM flag_records WHERE user_id = %s", (user_id,))
            flag_records_count = cursor.rowcount
            current_app.logger.info(f"已删除 {flag_records_count} 条升降旗记录")
            
            # 5. 最后删除用户本身
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            user_count = cursor.rowcount
            
            # 提交事务
            conn.commit()
            
            if user_count == 0:
                current_app.logger.error(f"用户 {user_id} 在最终删除阶段未找到")
                return APIResponse.error("用户不存在或已被删除", 404)
            
            current_app.logger.info(f"成功删除用户 {user['username']} (ID: {user_id})")
            return APIResponse.success(msg="用户删除成功")
            
        except Exception as e:
            # 发生错误，回滚事务
            conn.rollback()
            current_app.logger.error(f"删除用户时发生错误: {str(e)}")
            return APIResponse.error(f"删除用户失败: {str(e)}", 500)
        finally:
            # 关闭游标
            cursor.close()
            
    except Exception as e:
        current_app.logger.error(f"数据库连接失败: {str(e)}")
        return APIResponse.error("数据库连接失败", 500) 