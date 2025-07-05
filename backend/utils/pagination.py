from flask import request

def paginate_pymysql(data_list, page=None, per_page=None):
    """通用分页函数 (PyMySQL版本)
    
    Args:
        data_list: 要分页的数据列表
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
        
    # 计算总记录数和总页数
    total = len(data_list)
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 计算当前页的起止索引
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    
    # 获取当前页的数据
    items = data_list[start_idx:end_idx] if start_idx < total else []
    
    # 构建分页对象
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1
    }

# 保留原始函数以兼容旧代码
def paginate(query, page=None, per_page=None):
    """通用分页函数 (SQLAlchemy版本) - 已弃用，仅用于兼容"""
    import warnings
    warnings.warn("paginate() is deprecated, use paginate_pymysql() instead", DeprecationWarning)
    
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 10, type=int)
        
    # 限制每页数量，避免返回过多数据
    if per_page > 100:
        per_page = 100
        
    # 手动实现分页，将 SQLAlchemy 查询转换为列表
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    total = query.count()
    pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    # 构建分页对象
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_next': page < pages,
        'has_prev': page > 1
    } 