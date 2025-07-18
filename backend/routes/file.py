from flask import Blueprint, request, current_app, send_from_directory
from flask_jwt_extended import jwt_required
import os
import uuid
from werkzeug.utils import secure_filename
from utils.route_utils import APIResponse, handle_exceptions

file_bp = Blueprint('file', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@file_bp.route('/files/upload', methods=['POST'])
@jwt_required()
@handle_exceptions
def upload_file():
    """
    上传文件
    ---
    tags:
      - 文件
    security:
      - Bearer: []
    parameters:
      - name: file
        in: formData
        type: file
        required: true
    responses:
      200:
        description: 上传成功
      400:
        description: 无效文件类型
      401:
        description: 未认证
      500:
        description: 上传失败
    """
    current_app.logger.info("处理文件上传请求")
    
    if 'file' not in request.files:
        current_app.logger.warning("上传请求中没有文件部分")
        return APIResponse.error('No file part', 400)
    
    file = request.files['file']
    if file.filename == '':
        current_app.logger.warning("没有选择文件")
        return APIResponse.error('No selected file', 400)
        
    if not allowed_file(file.filename):
        current_app.logger.warning(f"无效的文件类型: {file.filename}")
        return APIResponse.error('Invalid file type', 400)
    
    try:
        # 确保上传目录存在
        upload_folder = current_app.config['UPLOAD_FOLDER']
        current_app.logger.info(f"上传目录: {upload_folder}")
        if not os.path.exists(upload_folder):
            current_app.logger.info(f"创建上传目录: {upload_folder}")
            os.makedirs(upload_folder)
            
        # 生成随机文件名防止路径遍历
        filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
        filepath = os.path.join(upload_folder, filename)
        
        current_app.logger.info(f"保存文件到: {filepath}")
        file.save(filepath)
        
        # 返回完整的URL路径
        file_url = f'/api/uploads/{filename}'
        current_app.logger.info(f"文件上传成功，URL: {file_url}")
        return APIResponse.success(data={
            'url': file_url
        })
    except Exception as e:
        current_app.logger.error(f"文件上传错误: {str(e)}", exc_info=True)
        return APIResponse.error(str(e), 500)

@file_bp.route('/uploads/<filename>')
def serve_file(filename):
    """提供上传的文件"""
    current_app.logger.info(f"获取上传的文件: {filename}")
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        current_app.logger.debug(f"从目录 {upload_folder} 提供文件")
        
        # 检查文件是否存在
        file_path = os.path.join(upload_folder, filename)
        if not os.path.exists(file_path):
            current_app.logger.error(f"文件不存在: {file_path}")
            return APIResponse.error(f"文件不存在: {filename}", 404)
        
        response = send_from_directory(upload_folder, filename)
        current_app.logger.info(f"成功提供文件: {filename}")
        return response
    except Exception as e:
        current_app.logger.error(f"获取文件错误: {str(e)}", exc_info=True)
        return APIResponse.error(f"文件访问错误: {filename} - {str(e)}", 404)