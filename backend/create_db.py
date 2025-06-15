import pymysql

def create_database():
    # 连接到 MySQL 服务器
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='123456'
    )
    
    try:
        with connection.cursor() as cursor:
            # 创建主数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS `system` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("主数据库 'system' 创建成功")
            
            # 创建测试数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS `system_test` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("测试数据库 'system_test' 创建成功")
            
        connection.commit()
    finally:
        connection.close()

if __name__ == '__main__':
    create_database() 