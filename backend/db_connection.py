import pymysql
import pymysql.cursors
import os
import logging
from dotenv import load_dotenv
from flask import current_app
from dbutils.pooled_db import PooledDB

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    """数据库连接池管理类"""
    _instance = None
    _pool = None

    @classmethod
    def get_instance(cls):
        """单例模式获取数据库管理实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if Database._pool is None:
            # 从 Flask 配置或环境变量读取
            if current_app:
                host = current_app.config['MYSQL_HOST']
                user = current_app.config['MYSQL_USER']
                password = current_app.config['MYSQL_PASSWORD']
                db = current_app.config['MYSQL_DATABASE']
                port = current_app.config['MYSQL_PORT']
                charset = current_app.config['MYSQL_CHARSET']
            else:
                # 如果没有Flask上下文，从环境变量读取
                host = os.environ.get('MYSQL_HOST', 'localhost')
                user = os.environ.get('MYSQL_USER', 'root')
                password = os.environ.get('MYSQL_PASSWORD', '123456')
                db = os.environ.get('MYSQL_DATABASE', 'system')
                port = int(os.environ.get('MYSQL_PORT', 3306))
                charset = os.environ.get('MYSQL_CHARSET', 'utf8mb4')

            Database._pool = PooledDB(
                creator=pymysql,
                maxconnections=10,  # 最大连接数
                mincached=2,        # 初始化时创建的空闲连接
                maxcached=5,        # 最大空闲连接数
                blocking=True,      # 连接数不足时是否等待
                ping=7,             # 检查连接是否可用 (0-7)
                host=host,
                user=user,
                password=password,
                database=db,
                port=port,
                charset=charset,
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info(f"Database connection pool initialized for {host}:{port}/{db}")

    def get_connection(self):
        """从连接池获取连接"""
        return Database._pool.connection()

    def execute_query(self, query, params=None, fetch_one=False):
        """执行查询并获取结果"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            conn.close()  # 归还连接给连接池

    def execute_update(self, query, params=None):
        """执行更新操作并返回受影响的行数"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                result = cursor.execute(query, params or ())
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing update: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            conn.close()

    def execute_many(self, query, params_list):
        """批量执行SQL操作"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                result = cursor.executemany(query, params_list)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing batch update: {str(e)}")
            raise
        finally:
            conn.close()

    def execute_insert(self, query, params=None):
        """执行插入操作并返回最后插入的ID"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                last_id = cursor.lastrowid
            conn.commit()
            return last_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing insert: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            conn.close()

# 创建全局数据库实例
db = Database.get_instance()
