from flask import request
from datetime import datetime
from models import db, OperationLog

def log_operation():
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                response = f(*args, **kwargs)
                user_id = get_jwt_identity() if request.headers.get('Authorization') else None
                log = OperationLog(
                    user_id=user_id,
                    endpoint=request.endpoint,
                    method=request.method,
                    ip_address=request.remote_addr,  # 记录IP
                    timestamp=datetime.utcnow()
                )
                db.session.add(log)
                return response
            except Exception as e:
                current_app.logger.error(f"API Error: {str(e)}")
                raise
        return wrapper
    return decorator