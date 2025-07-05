import pymysql
import pymysql.cursors
import os
import logging
from dotenv import load_dotenv
from flask import current_app

load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

class Database:
    """数据库连接管理类"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """单例模式获取数据库连接实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def __init__(self):
        """初始化数据库连接配置"""
        self.connection = None
        
    def connect(self):
        """创建数据库连接"""
        try:
            if self.connection is None or not self.connection.open:
                # 从Flask配置中读取数据库配置
                if current_app:
                    self.host = current_app.config['MYSQL_HOST']
                    self.user = current_app.config['MYSQL_USER']
                    self.password = current_app.config['MYSQL_PASSWORD']
                    self.db = current_app.config['MYSQL_DATABASE']
                    self.port = current_app.config['MYSQL_PORT']
                    self.charset = current_app.config['MYSQL_CHARSET']
                else:
                    # 如果没有Flask上下文，从环境变量读取
                    self.host = os.environ.get('MYSQL_HOST', 'localhost')
                    self.user = os.environ.get('MYSQL_USER', 'root')
                    self.password = os.environ.get('MYSQL_PASSWORD', '123456')
                    self.db = os.environ.get('MYSQL_DATABASE', 'system')
                    self.port = int(os.environ.get('MYSQL_PORT', 3306))
                    self.charset = os.environ.get('MYSQL_CHARSET', 'utf8mb4')
                
                self.connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.db,
                    port=self.port,
                    charset=self.charset,
                    cursorclass=pymysql.cursors.DictCursor
                )
                logger.info(f"Database connection established to {self.host}:{self.port}/{self.db}")
            return self.connection
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
            
    def get_connection(self):
        """获取数据库连接"""
        return self.connect()
    
    def execute_query(self, query, params=None, fetch_one=False):
        """执行查询并获取结果"""
        conn = self.connect()
        cursor = None
        try:
            cursor = conn.cursor()
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
            if cursor:
                cursor.close()
    
    def execute_update(self, query, params=None):
        """执行更新操作并返回受影响的行数"""
        conn = self.connect()
        cursor = None
        try:
            cursor = conn.cursor()
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
            if cursor:
                cursor.close()
                
    def execute_many(self, query, params_list):
        """批量执行SQL操作"""
        conn = self.connect()
        cursor = None
        try:
            cursor = conn.cursor()
            result = cursor.executemany(query, params_list)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Error executing batch update: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def execute_insert(self, query, params=None):
        """执行插入操作并返回最后插入的ID"""
        conn = self.connect()
        cursor = None
        try:
            cursor = conn.cursor()
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
            if cursor:
                cursor.close()
    
    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.open:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
            
    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()

# 创建全局数据库实例
db = Database.get_instance() 