from flask import request
from extensions import db

def paginate(query, page=None, per_page=None):
    """通用分页函数
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码（从1开始）
        per_page: 每页数量
        
    Returns:
        pagination: 分页对象，包含以下属性：
            - items: 当前页的数据列表
            - page: 当前页码
            - per_page: 每页数量
            - total: 总记录数
            - pages: 总页数
    """
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 10, type=int)
        
    # 限制每页数量，避免返回过多数据
    if per_page > 100:
        per_page = 100
        
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    ) 