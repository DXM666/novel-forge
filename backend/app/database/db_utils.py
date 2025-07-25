"""
数据库工具模块 - 实现PostgreSQL和向量数据库的交互功能
提供统一的数据库连接管理、事务处理和错误处理
"""
import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
import json
import contextlib
from functools import wraps

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extensions import ISOLATION_LEVEL_SERIALIZABLE, ISOLATION_LEVEL_READ_COMMITTED

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入统一配置
from ..config import settings
from ..utils.logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 全局连接池
connection_pool = None

def init_db_pool(min_conn: int = None, max_conn: int = None, **kwargs) -> bool:
    """
    初始化数据库连接池
    
    参数:
        min_conn: 最小连接数，如果为None则使用配置文件中的值
        max_conn: 最大连接数，如果为None则使用配置文件中的值
        **kwargs: 其他数据库配置参数，会覆盖默认配置
    
    返回:
        是否成功初始化
    """
    global connection_pool
    
    # 使用统一配置
    config = settings.db_config.copy()
    
    # 如果提供了额外参数，覆盖默认配置
    if kwargs:
        config.update(kwargs)
        
    # 设置连接池大小
    min_connections = min_conn if min_conn is not None else settings.db_pool_min_size
    max_connections = max_conn if max_conn is not None else settings.db_pool_max_size
    
    try:
        if connection_pool is not None:
            # 如果连接池已存在，先关闭现有连接
            connection_pool.closeall()
            logger.info("关闭现有连接池")
        
        # 创建引擎
        engine = create_engine(
            settings.database_url
        )
        
        # 创建新的连接池
        connection_pool = SimpleConnectionPool(
            minconn=min_connections,
            maxconn=max_connections,
            **config
        )
        
        logger.info("数据库连接池初始化成功")
        return True
    except Exception as e:
        logger.error(f"初始化数据库连接池失败: {e}")
        connection_pool = None
        return False

def get_db_connection():
    """
    获取数据库连接
    
    返回:
        数据库连接对象或None
    """
    global connection_pool
    
    # 如果连接池不存在，尝试初始化
    if connection_pool is None:
        init_db_pool()
    
    if connection_pool:
        try:
            return connection_pool.getconn()
        except Exception as e:
            logger.error(f"从连接池获取连接失败: {str(e)}")
    
    # 连接池失败，尝试直接连接
    try:
        logger.warning("连接池不可用，尝试直接连接数据库")
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"数据库直接连接失败: {str(e)}")
        return None

def release_db_connection(conn):
    """
    释放数据库连接回连接池
    
    参数:
        conn: 数据库连接对象
    """
    global connection_pool
    
    if connection_pool and conn:
        try:
            connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"释放连接回连接池失败: {str(e)}")
            try:
                conn.close()
            except:
                pass


@contextlib.contextmanager
def db_transaction(isolation_level=ISOLATION_LEVEL_READ_COMMITTED):
    """
    数据库事务上下文管理器
    
    参数:
        isolation_level: 事务隔离级别
    
    用法:
        with db_transaction() as (conn, cursor):
            cursor.execute("INSERT INTO ...")
            # 自动提交或回滚
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("无法获取数据库连接")
        
        # 设置隔离级别
        conn.set_isolation_level(isolation_level)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield conn, cursor
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"事务执行失败: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)

def retry_on_error(max_retries=3, retry_delay=0.5):
    """
    数据库操作重试装饰器
    
    参数:
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
    
    用法:
        @retry_on_error(max_retries=3)
        def some_db_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"操作失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))  # 指数退避
            
            # 所有重试都失败
            logger.error(f"操作在 {max_retries} 次尝试后失败: {str(last_error)}")
            raise last_error
        return wrapper
    return decorator

def execute_query(query: str, params: tuple = None, fetch: bool = True, 
                 cursor_factory=RealDictCursor) -> Tuple[bool, Any]:
    """
    执行SQL查询
    
    参数:
        query: SQL查询语句
        params: 查询参数
        fetch: 是否获取结果
        cursor_factory: 游标工厂
    
    返回:
        (成功标志, 结果或错误信息)
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return False, "无法获取数据库连接"
        
        cursor = conn.cursor(cursor_factory=cursor_factory)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
        else:
            result = None
        
        conn.commit()
        return True, result
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"查询执行失败: {str(e)}\nQuery: {query}\nParams: {params}")
        return False, str(e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db_connection(conn)


def create_project(title: str, description: str, author_id: str) -> Tuple[bool, str]:
    """
    创建新项目
    
    参数:
        title: 项目标题
        description: 项目描述
        author_id: 作者ID
    
    返回:
        (成功标志, 项目ID或错误信息)
    """
    query = """
    INSERT INTO projects (title, description, author_id)
    VALUES (%s, %s, %s)
    RETURNING id
    """
    success, result = execute_query(query, (title, description, author_id))
    
    if success and result:
        return True, result[0]['id']
    return False, "创建项目失败" if not success else "未返回项目ID"


def get_project(project_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    获取项目信息
    
    参数:
        project_id: 项目ID
    
    返回:
        (成功标志, 项目信息或错误信息)
    """
    query = """
    SELECT * FROM projects WHERE id = %s
    """
    success, result = execute_query(query, (project_id,))
    
    if success:
        if result:
            return True, dict(result[0])
        return False, "项目不存在"
    return False, result


def save_memory_entry(project_id: str, entry_type: str, content: str, 
                     metadata: Dict[str, Any] = None) -> Tuple[bool, str]:
    """
    保存记忆条目
    
    参数:
        project_id: 项目ID
        entry_type: 条目类型 (summary, event, character_state等)
        content: 内容
        metadata: 元数据
    
    返回:
        (成功标志, 记忆ID或错误信息)
    """
    query = """
    INSERT INTO memory_entries (project_id, entry_type, content, metadata)
    VALUES (%s, %s, %s, %s)
    RETURNING id
    """
    success, result = execute_query(query, (project_id, entry_type, content, Json(metadata or {})))
    
    if success and result:
        return True, result[0]['id']
    return False, "保存记忆条目失败" if not success else "未返回记忆ID"


def get_memory_entries(project_id: str, entry_type: Optional[str] = None, 
                      limit: int = 100) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    获取记忆条目
    
    参数:
        project_id: 项目ID
        entry_type: 可选的条目类型过滤
        limit: 返回结果数量限制
    
    返回:
        (成功标志, 记忆条目列表或错误信息)
    """
    if entry_type:
        query = """
        SELECT * FROM memory_entries 
        WHERE project_id = %s AND entry_type = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        params = (project_id, entry_type, limit)
    else:
        query = """
        SELECT * FROM memory_entries 
        WHERE project_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        params = (project_id, limit)
    
    success, result = execute_query(query, params)
    
    if success:
        return True, [dict(item) for item in result]
    return False, result


def save_novel_element(project_id: str, element_type: str, element_id: str, 
                      data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    保存小说元素
    
    参数:
        project_id: 项目ID
        element_type: 元素类型 (character, location, item等)
        element_id: 元素ID
        data: 元素数据
    
    返回:
        (成功标志, 元素ID或错误信息)
    """
    # 检查元素是否已存在
    check_query = """
    SELECT id FROM novel_elements 
    WHERE project_id = %s AND element_type = %s AND element_id = %s
    """
    success, result = execute_query(check_query, (project_id, element_type, element_id))
    
    if success:
        if result:
            # 更新现有元素
            update_query = """
            UPDATE novel_elements 
            SET data = %s, updated_at = NOW()
            WHERE project_id = %s AND element_type = %s AND element_id = %s
            RETURNING id
            """
            success, result = execute_query(update_query, (Json(data), project_id, element_type, element_id))
        else:
            # 创建新元素
            insert_query = """
            INSERT INTO novel_elements (project_id, element_type, element_id, data)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
            success, result = execute_query(insert_query, (project_id, element_type, element_id, Json(data)))
    
    if success and result:
        return True, result[0]['id']
    return False, "保存小说元素失败" if not success else "未返回元素ID"


def get_novel_element(project_id: str, element_type: str, element_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    获取小说元素
    
    参数:
        project_id: 项目ID
        element_type: 元素类型
        element_id: 元素ID
    
    返回:
        (成功标志, 元素数据或错误信息)
    """
    query = """
    SELECT * FROM novel_elements 
    WHERE project_id = %s AND element_type = %s AND element_id = %s
    """
    success, result = execute_query(query, (project_id, element_type, element_id))
    
    if success:
        if result:
            return True, dict(result[0])
        return False, "元素不存在"
    return False, result


def get_novel_elements_by_type(project_id: str, element_type: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    获取指定类型的所有小说元素
    
    参数:
        project_id: 项目ID
        element_type: 元素类型
    
    返回:
        (成功标志, 元素列表或错误信息)
    """
    query = """
    SELECT * FROM novel_elements 
    WHERE project_id = %s AND element_type = %s
    ORDER BY element_id
    """
    success, result = execute_query(query, (project_id, element_type))
    
    if success:
        return True, [dict(item) for item in result]
    return False, result


def save_chapter(project_id: str, chapter_number: int, title: str, 
                summary: Optional[str] = None, content: Optional[str] = None,
                status: str = 'draft') -> Tuple[bool, str]:
    """
    保存章节
    
    参数:
        project_id: 项目ID
        chapter_number: 章节编号
        title: 章节标题
        summary: 章节摘要
        content: 章节内容
        status: 章节状态
    
    返回:
        (成功标志, 章节ID或错误信息)
    """
    # 检查章节是否已存在
    check_query = """
    SELECT id FROM chapters 
    WHERE project_id = %s AND chapter_number = %s
    """
    success, result = execute_query(check_query, (project_id, chapter_number))
    
    if success:
        if result:
            # 更新现有章节
            update_query = """
            UPDATE chapters 
            SET title = %s, summary = %s, content = %s, status = %s, updated_at = NOW()
            WHERE project_id = %s AND chapter_number = %s
            RETURNING id
            """
            success, result = execute_query(update_query, 
                                          (title, summary, content, status, project_id, chapter_number))
        else:
            # 创建新章节
            insert_query = """
            INSERT INTO chapters (project_id, chapter_number, title, summary, content, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            success, result = execute_query(insert_query, 
                                          (project_id, chapter_number, title, summary, content, status))
    
    if success and result:
        return True, result[0]['id']
    return False, "保存章节失败" if not success else "未返回章节ID"


def get_chapter(project_id: str, chapter_number: int) -> Tuple[bool, Dict[str, Any]]:
    """
    获取章节
    
    参数:
        project_id: 项目ID
        chapter_number: 章节编号
    
    返回:
        (成功标志, 章节数据或错误信息)
    """
    query = """
    SELECT * FROM chapters 
    WHERE project_id = %s AND chapter_number = %s
    """
    success, result = execute_query(query, (project_id, chapter_number))
    
    if success:
        if result:
            return True, dict(result[0])
        return False, "章节不存在"
    return False, result


def get_all_chapters(project_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    获取项目的所有章节
    
    参数:
        project_id: 项目ID
    
    返回:
        (成功标志, 章节列表或错误信息)
    """
    query = """
    SELECT * FROM chapters 
    WHERE project_id = %s
    ORDER BY chapter_number
    """
    success, result = execute_query(query, (project_id,))
    
    if success:
        return True, [dict(item) for item in result]
    return False, result


def save_outline(project_id: str, skeleton: str, structure: Dict[str, Any]) -> Tuple[bool, str]:
    """
    保存大纲
    
    参数:
        project_id: 项目ID
        skeleton: 故事骨架
        structure: 结构化大纲信息
    
    返回:
        (成功标志, 大纲ID或错误信息)
    """
    # 检查大纲是否已存在
    check_query = """
    SELECT id FROM outlines 
    WHERE project_id = %s
    """
    success, result = execute_query(check_query, (project_id,))
    
    if success:
        if result:
            # 更新现有大纲
            update_query = """
            UPDATE outlines 
            SET skeleton = %s, structure = %s, updated_at = NOW()
            WHERE project_id = %s
            RETURNING id
            """
            success, result = execute_query(update_query, (skeleton, Json(structure), project_id))
        else:
            # 创建新大纲
            insert_query = """
            INSERT INTO outlines (project_id, skeleton, structure)
            VALUES (%s, %s, %s)
            RETURNING id
            """
            success, result = execute_query(insert_query, (project_id, skeleton, Json(structure)))
    
    if success and result:
        return True, result[0]['id']
    return False, "保存大纲失败" if not success else "未返回大纲ID"


def get_outline(project_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    获取大纲
    
    参数:
        project_id: 项目ID
    
    返回:
        (成功标志, 大纲数据或错误信息)
    """
    query = """
    SELECT * FROM outlines 
    WHERE project_id = %s
    """
    success, result = execute_query(query, (project_id,))
    
    if success:
        if result:
            return True, dict(result[0])
        return False, "大纲不存在"
    return False, result


def save_version_history(project_id: str, entity_type: str, entity_id: str, 
                        version_data: Dict[str, Any], comment: Optional[str] = None) -> Tuple[bool, str]:
    """
    保存版本历史
    
    参数:
        project_id: 项目ID
        entity_type: 实体类型 (memory, element, graph)
        entity_id: 实体ID
        version_data: 版本数据
        comment: 用户注释
    
    返回:
        (成功标志, 版本ID或错误信息)
    """
    query = """
    INSERT INTO version_history (project_id, entity_type, entity_id, version_data, user_comment)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """
    success, result = execute_query(query, (project_id, entity_type, entity_id, Json(version_data), comment))
    
    if success and result:
        return True, result[0]['id']
    return False, "保存版本历史失败" if not success else "未返回版本ID"


def get_version_history(project_id: str, entity_type: Optional[str] = None, 
                       entity_id: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    获取版本历史
    
    参数:
        project_id: 项目ID
        entity_type: 可选的实体类型过滤
        entity_id: 可选的实体ID过滤
    
    返回:
        (成功标志, 版本历史列表或错误信息)
    """
    params = [project_id]
    query = "SELECT * FROM version_history WHERE project_id = %s"
    
    if entity_type:
        query += " AND entity_type = %s"
        params.append(entity_type)
    
    if entity_id:
        query += " AND entity_id = %s"
        params.append(entity_id)
    
    query += " ORDER BY created_at DESC"
    
    success, result = execute_query(query, tuple(params))
    
    if success:
        return True, [dict(item) for item in result]
    return False, result


def get_project_summary(project_id: str) -> Tuple[bool, Dict[str, Any]]:
    """
    获取项目摘要
    
    参数:
        project_id: 项目ID
    
    返回:
        (成功标志, 项目摘要或错误信息)
    """
    query = """
    SELECT * FROM project_summary 
    WHERE project_id = %s
    """
    success, result = execute_query(query, (project_id,))
    
    if success:
        if result:
            return True, dict(result[0])
        return False, "项目不存在"
    return False, result


# 向量数据库相关函数
# 注意：这些函数需要实际的向量嵌入模型支持

def save_vector_memory(memory_id: str, embedding: List[float]) -> Tuple[bool, str]:
    """
    保存向量记忆
    
    参数:
        memory_id: 记忆ID
        embedding: 向量嵌入
    
    返回:
        (成功标志, 向量ID或错误信息)
    """
    query = """
    INSERT INTO vector_memories (memory_id, embedding)
    VALUES (%s, %s)
    RETURNING id
    """
    success, result = execute_query(query, (memory_id, embedding))
    
    if success and result:
        return True, result[0]['id']
    return False, "保存向量记忆失败" if not success else "未返回向量ID"


def search_related_memories(project_id: str, query_embedding: List[float], 
                          limit: int = 5) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    搜索相关记忆
    
    参数:
        project_id: 项目ID
        query_embedding: 查询向量
        limit: 返回结果数量限制
    
    返回:
        (成功标志, 相关记忆列表或错误信息)
    """
    query = """
    SELECT 
        me.id AS memory_id,
        me.entry_type,
        me.content,
        me.metadata,
        1 - (vm.embedding <=> %s) AS similarity
    FROM 
        memory_entries me
    JOIN 
        vector_memories vm ON me.id = vm.memory_id
    WHERE 
        me.project_id = %s
    ORDER BY 
        similarity DESC
    LIMIT %s
    """
    success, result = execute_query(query, (query_embedding, project_id, limit))
    
    if success:
        return True, [dict(item) for item in result]
    return False, result
