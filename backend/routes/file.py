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
    if 'file' not in request.files:
        return APIResponse.error('No file part', 400)
    
    file = request.files['file']
    if file.filename == '':
        return APIResponse.error('No selected file', 400)
        
    if not allowed_file(file.filename):
        return APIResponse.error('Invalid file type', 400)
    
    try:
        # 确保上传目录存在
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        # 生成随机文件名防止路径遍历
        filename = secure_filename(str(uuid.uuid4()) + os.path.splitext(file.filename)[1])
        filepath = os.path.join(upload_folder, filename)
        
        file.save(filepath)
        
        # 返回完整的URL路径
        return APIResponse.success(data={
            'url': f'/api/uploads/{filename}'
        })
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return APIResponse.error(str(e), 500)

@file_bp.route('/uploads/<filename>')
def serve_file(filename):
    """提供上传的文件"""
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)