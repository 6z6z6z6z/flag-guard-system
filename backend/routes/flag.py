from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models_pymysql import FlagRecord, User, PointHistory
from db_connection import db
from datetime import datetime
from utils.route_utils import (
    APIResponse, validate_required_fields, handle_exceptions,
    validate_json_request, role_required
)
from sql.queries import FLAG_RECORD_QUERIES

bp = Blueprint('flag', __name__)

@bp.route('/records', methods=['POST'])
@jwt_required()
@validate_json_request
@handle_exceptions
def create_flag_record():
    """
    创建升降旗记录
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            date:
              type: string
              format: date
            type:
              type: string
              enum: [raise, lower]
            photo_url:
              type: string
    responses:
      201:
        description: 记录创建成功
      400:
        description: 参数错误
    """
    data = request.get_json()
    
    # 验证必要字段
    required_fields = ['date', 'type', 'photo_url']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return APIResponse.error(error_msg, 400)
    
    # 验证类型
    if data['type'] not in ['raise', 'lower']:
        return APIResponse.error("Invalid flag operation type", 400)
    
    try:
        # 创建记录
        record = FlagRecord.create(
            user_id=get_jwt_identity(),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            type=data['type'],
            photo_url=data['photo_url'],
            status='pending'
        )
        
        return APIResponse.success(
            data=record,
            msg="升降旗记录创建成功",
            code=201
        )
    except ValueError as e:
        return APIResponse.error(f"Invalid date format: {str(e)}", 400)
    except Exception as e:
        current_app.logger.error(f"Failed to create flag record: {str(e)}")
        return APIResponse.error("Failed to create record", 500)

@bp.route('/records', methods=['GET'])
@jwt_required()
@handle_exceptions
def get_flag_records():
    """
    获取用户的升降旗记录
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
      - name: status
        in: query
        type: string
        enum: [pending, approved, rejected]
    responses:
      200:
        description: 成功获取记录列表
    """
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    current_app.logger.info(f"获取用户 {user_id} 的升降旗记录，参数：page={page}, per_page={per_page}, status={status}")
    
    try:
        # 获取用户的所有升降旗记录
        records = FlagRecord.list_by_user(user_id)
        current_app.logger.info(f"找到用户 {user_id} 的 {len(records)} 条记录")
        
        # 确保所有记录都包含必要的字段
        formatted_records = []
        for record in records:
            if record is None:
                current_app.logger.warning("跳过无效记录")
                continue
                
            # 确保记录有所有必需的字段
            record_copy = dict(record)  # 创建副本防止修改原始数据
            
            # 确保日期格式正确
            if isinstance(record_copy.get('date'), str):
                try:
                    record_copy['date'] = datetime.strptime(record_copy['date'], '%Y-%m-%d').date().isoformat()
                except (ValueError, TypeError) as e:
                    current_app.logger.warning(f"日期格式错误：{record_copy.get('date')}, 使用当前日期")
                    record_copy['date'] = datetime.now().date().isoformat()
            elif hasattr(record_copy.get('date'), 'isoformat'):
                record_copy['date'] = record_copy['date'].isoformat()
            else:
                current_app.logger.warning(f"无效的日期值：{record_copy.get('date')}, 使用当前日期")
                record_copy['date'] = datetime.now().date().isoformat()
                
            # 确保状态字段存在
            if 'status' not in record_copy or record_copy['status'] is None:
                record_copy['status'] = 'pending'
                
            # 确保积分字段存在
            if 'points_awarded' not in record_copy or record_copy['points_awarded'] is None:
                record_copy['points_awarded'] = 0
                
            formatted_records.append(record_copy)
        
        # 根据状态过滤
        if status and status != 'all':
            filtered_records = [r for r in formatted_records if r.get('status') == status]
            current_app.logger.info(f"按状态'{status}'过滤后：{len(filtered_records)}条记录")
        else:
            filtered_records = formatted_records
        
        # 按日期降序排序
        try:
            filtered_records.sort(key=lambda x: str(x.get('date', '')), reverse=True)
        except Exception as e:
            current_app.logger.error(f"排序记录时出错：{str(e)}")
        
        # 手动分页
        total = len(filtered_records)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        
        # 获取当前页的记录
        current_page_records = filtered_records[start_idx:end_idx] if start_idx < total else []
        
        current_app.logger.info(f"返回用户{user_id}的{len(current_page_records)}条记录")
        
        return APIResponse.success(data={
            "items": current_page_records,
            "total": total,
            "pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        current_app.logger.error(f"get_flag_records中出错：{str(e)}")
        current_app.logger.exception(e)
        return APIResponse.error(f"处理请求时出错：{str(e)}", 500)

@bp.route('/records/review', methods=['GET'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def get_flag_records_for_review():
    """
    获取所有升降旗记录（管理员用）
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 10
      - name: status
        in: query
        type: string
        enum: [pending, approved, rejected]
    responses:
      200:
        description: 成功获取记录列表
      403:
        description: 权限不足
    """
    current_app.logger.info("进入get_flag_records_for_review函数")
    current_app.logger.info(f"当前用户ID：{get_jwt_identity()}")
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    current_app.logger.info(f"查询参数：page={page}, per_page={per_page}, status={status}")
    
    try:
        # 获取所有升降旗记录
        records = FlagRecord.list_all()
        current_app.logger.info(f"初始记录数量：{len(records)}")
        
        # 确保所有记录都包含必要的字段
        formatted_records = []
        for record in records:
            if record is None:
                current_app.logger.warning("跳过无效记录")
                continue
                
            # 确保记录有所有必需的字段
            record_copy = dict(record)  # 创建副本防止修改原始数据
            
            # 确保用户信息存在
            if 'user' not in record_copy or not record_copy['user']:
                record_copy['user'] = {
                    'name': record_copy.get('user_name', 'Unknown'),
                    'student_id': record_copy.get('student_id', '')
                }
                
            # 确保日期和时间格式正确
            if isinstance(record_copy.get('date'), str):
                try:
                    record_copy['date'] = datetime.strptime(record_copy['date'], '%Y-%m-%d').date().isoformat()
                except (ValueError, TypeError) as e:
                    current_app.logger.warning(f"日期格式错误：{record_copy.get('date')}, 使用当前日期")
                    record_copy['date'] = datetime.now().date().isoformat()
                except ValueError:
                    current_app.logger.warning(f"无效的日期值：{record_copy.get('date')}, 使用当前日期")
                    record_copy['date'] = datetime.now().date().isoformat()
            elif hasattr(record_copy.get('date'), 'isoformat'):
                record_copy['date'] = record_copy['date'].isoformat()
            else:
                current_app.logger.warning(f"无效的日期值：{record_copy.get('date')}, 使用当前日期")
                record_copy['date'] = datetime.now().date().isoformat()
            
            # 确保审核状态值正确
            if 'status' not in record_copy or record_copy['status'] is None:
                record_copy['status'] = 'pending'
                
            # 确保积分字段存在
            if 'points_awarded' not in record_copy or record_copy['points_awarded'] is None:
                record_copy['points_awarded'] = 0
                
            formatted_records.append(record_copy)
        
        # 根据状态过滤
        if status and status != 'all':
            filtered_records = [r for r in formatted_records if r.get('status') == status]
            current_app.logger.info(f"按状态'{status}'过滤后：{len(filtered_records)}条记录")
        else:
            filtered_records = formatted_records
            current_app.logger.info(f"不过滤状态：{len(filtered_records)}条记录")
        
        # 按日期降序排序
        try:
            filtered_records.sort(key=lambda x: str(x.get('date', '')), reverse=True)
        except Exception as e:
            current_app.logger.error(f"排序记录时出错：{str(e)}")
            current_app.logger.exception(e)
        
        current_app.logger.info(f"过滤和排序后找到{len(filtered_records)}条记录")
        
        # 手动分页
        total = len(filtered_records)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total)
        
        # 获取当前页的记录
        current_page_records = filtered_records[start_idx:end_idx] if start_idx < total else []
        
        current_app.logger.info(f"为第{page}页返回{len(current_page_records)}条记录")
        
        # 进一步调试记录内容
        for i, record in enumerate(current_page_records):
            current_app.logger.debug(f"记录{i+1}：id={record.get('record_id')}, user={record.get('user')}, status={record.get('status')}")
        
        return APIResponse.success(data={
            "items": current_page_records,
            "total": total,
            "pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        current_app.logger.error(f"get_flag_records_for_review中出错：{str(e)}")
        current_app.logger.exception(e)
        return APIResponse.error(f"处理请求时出错：{str(e)}", 500)

@bp.route('/records/<int:record_id>/approve', methods=['POST'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def approve_flag_record(record_id):
    """
    审核通过升降旗记录
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 审核成功
      403:
        description: 权限不足
      404:
        description: 记录不存在
    """
    record = FlagRecord.get_by_id(record_id)
    if not record:
        return APIResponse.error("记录不存在", 404)
        
    current_app.logger.info(f"Processing flag record approval for record_id: {record_id}")
    current_app.logger.debug(f"Record details: {record}")
    
    try:
        # 检查状态
        current_status = record.get('status')
        if current_status != 'pending':
            current_app.logger.warning(f"Record {record_id} is already reviewed with status: {current_status}")
            return APIResponse.error(f"记录已经被审核，当前状态: {current_status}", 400)
        
        # 计算并添加积分
        points = float(current_app.config.get('FLAG_POINTS', 5))
        flag_type = record.get('type', 'raise')
        flag_type_text = '升旗' if flag_type == 'raise' else '降旗'
        current_app.logger.info(f"Awarding {points} points for flag record {record_id}")
        
        # 获取用户ID
        user_id = record.get('user_id')
        if not user_id:
            return APIResponse.error("记录中缺少用户ID", 500)
        
        reviewer_id = int(get_jwt_identity())
        
        # 更新记录状态和积分
        updated_record = FlagRecord.review(
            record_id=record_id,
            status='approved',
            points_awarded=points,
            reviewer_id=reviewer_id
        )
        
        current_app.logger.debug(f"Updated record: {updated_record}")
        
        # 添加用户积分和积分历史
        User.add_points(
            user_id=user_id,
            points=points,
            change_type='flag',
            related_id=record_id,
            description=f'{flag_type_text}审核通过'
        )
        
        # 记录积分变动
        current_app.logger.info(f"Added {points} points to user {user_id} for flag record {record_id}")
        
        return APIResponse.success(msg="审核通过成功")
    except Exception as e:
        current_app.logger.error(f"Failed to approve flag record: {str(e)}")
        current_app.logger.exception(e)
        return APIResponse.error(f"审核记录失败: {str(e)}", 500)

@bp.route('/records/<int:record_id>/reject', methods=['POST'])
@jwt_required()
@role_required('admin')
@handle_exceptions
def reject_flag_record(record_id):
    """
    驳回升降旗记录
    ---
    tags:
      - 升降旗
    security:
      - Bearer: []
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: 驳回成功
      403:
        description: 权限不足
      404:
        description: 记录不存在
    """
    record = FlagRecord.get_by_id(record_id)
    if not record:
        return APIResponse.error("记录不存在", 404)
    
    current_app.logger.info(f"Processing flag record rejection for record_id: {record_id}")
    current_app.logger.debug(f"Record details: {record}")
    
    try:
        # 检查状态
        current_status = record.get('status')
        if current_status != 'pending':
            current_app.logger.warning(f"Record {record_id} is already reviewed with status: {current_status}")
            return APIResponse.error(f"记录已经被审核，当前状态: {current_status}", 400)
        
        reviewer_id = int(get_jwt_identity())
        
        # 更新记录状态
        updated_record = FlagRecord.review(
            record_id=record_id,
            status='rejected',
            points_awarded=0,
            reviewer_id=reviewer_id
        )
        
        current_app.logger.debug(f"Updated record after rejection: {updated_record}")
        
        return APIResponse.success(msg="驳回成功")
    except Exception as e:
        current_app.logger.error(f"Failed to reject flag record: {str(e)}")
        current_app.logger.exception(e)
        return APIResponse.error(f"驳回记录失败: {str(e)}", 500)