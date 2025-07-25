import os
import logging
from typing import Dict, Any, List, Optional

from psycopg2.extras import Json, RealDictCursor

# 导入统一的数据库连接管理
from .database.db_utils import (
    get_db_connection, release_db_connection, execute_query, 
    db_transaction, retry_on_error
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """初始化数据库表结构"""
    try:
        with db_transaction() as (conn, cursor):
            # 创建存储文本内容的表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                memory_id VARCHAR(255) PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            # 创建存储小说结构化数据的表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS novel_elements (
                id SERIAL PRIMARY KEY,
                novel_id VARCHAR(255) NOT NULL,
                element_type VARCHAR(50) NOT NULL,  -- character, location, item, outline, chapter
                element_id VARCHAR(255) NOT NULL,    -- 如character_1, location_2等
                data JSONB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(novel_id, element_type, element_id)
            );
            """)
            
            # 创建存储LangGraph状态的表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_states (
                thread_id VARCHAR(255) PRIMARY KEY,
                state JSONB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            # 创建版本历史表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS version_history (
                id SERIAL PRIMARY KEY,
                memory_id VARCHAR(255) NOT NULL,
                version INT NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_id, version)
            );
            """)
            
            logger.info("数据库表初始化完成")
    except Exception as e:
        logger.error(f"初始化数据库失败: {e}")
        raise


class BaseMemoryStore:
    """基础内存存储接口"""
    def get(self, memory_id: str) -> str:
        """获取内存内容"""
        raise NotImplementedError()

    def add(self, memory_id: str, text: str):
        """添加内存内容"""
        raise NotImplementedError()


class PostgresMemoryStore(BaseMemoryStore):
    """PostgreSQL实现的内存存储"""
    
    def __init__(self):
        """初始化PostgreSQL存储"""
        # 确保数据库表已创建
        init_db()
    
    @retry_on_error(max_retries=3)
    def get(self, memory_id: str) -> str:
        """获取内存内容"""
        try:
            query = "SELECT text FROM memories WHERE memory_id = %s"
            result = execute_query(query, (memory_id,))
            row = result.fetchone()
            return row[0] if row else ""
        except Exception as e:
            logger.error(f"获取内存失败: {e}")
            return ""
    
    @retry_on_error(max_retries=3)
    def add(self, memory_id: str, text: str):
        """添加或更新内存内容"""
        try:
            with db_transaction() as (conn, cursor):
                # 先检查是否存在
                cursor.execute(
                    "SELECT text FROM memories WHERE memory_id = %s",
                    (memory_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    # 存在则更新
                    prev_text = result[0]
                    new_text = prev_text + text
                    cursor.execute(
                        """UPDATE memories 
                           SET text = %s, updated_at = CURRENT_TIMESTAMP 
                           WHERE memory_id = %s""",
                        (new_text, memory_id)
                    )
                    # 添加版本历史
                    cursor.execute(
                        """INSERT INTO version_history (memory_id, version, text)
                           VALUES (%s, (SELECT COUNT(*) FROM version_history WHERE memory_id = %s) + 1, %s)""",
                        (memory_id, memory_id, new_text)
                    )
                else:
                    # 不存在则插入
                    cursor.execute(
                        """INSERT INTO memories (memory_id, text)
                           VALUES (%s, %s)""",
                        (memory_id, text)
                    )
                    # 添加初始版本
                    cursor.execute(
                        """INSERT INTO version_history (memory_id, version, text)
                           VALUES (%s, 1, %s)""",
                        (memory_id, text)
                    )
        except Exception as e:
            logger.error(f"添加内存失败: {e}")
            raise
    
    @retry_on_error(max_retries=3)
    def get_version_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """获取内存版本历史"""
        try:
            query = """
            SELECT version, text, created_at 
            FROM version_history 
            WHERE memory_id = %s 
            ORDER BY version DESC
            """
            result = execute_query(query, (memory_id,), cursor_factory=RealDictCursor)
            return result.fetchall() if result else []
        except Exception as e:
            logger.error(f"获取版本历史失败: {e}")
            return []
    
    @retry_on_error(max_retries=3)
    def restore_version(self, memory_id: str, version: int) -> bool:
        """恢复到指定版本"""
        try:
            with db_transaction() as (conn, cursor):
                # 获取指定版本内容
                cursor.execute(
                    "SELECT text FROM version_history WHERE memory_id = %s AND version = %s",
                    (memory_id, version)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False
                    
                # 更新当前内容
                cursor.execute(
                    """UPDATE memories 
                       SET text = %s, updated_at = CURRENT_TIMESTAMP 
                       WHERE memory_id = %s""",
                    (result[0], memory_id)
                )
                
                # 添加新版本（恢复操作也会生成新版本）
                cursor.execute(
                    """INSERT INTO version_history (memory_id, version, text)
                       VALUES (%s, (SELECT COUNT(*) FROM version_history WHERE memory_id = %s) + 1, %s)""",
                    (memory_id, memory_id, result[0])
                )
                
                return True
                
        except Exception as e:
            logger.error(f"恢复版本失败: {e}")
            return False


class NovelElementStore:
    """小说元素存储（角色、地点、物品、大纲等）"""
    
    def __init__(self):
        """初始化存储"""
        # 确保数据库表已创建
        init_db()
    
    def save_element(self, novel_id: str, element_type: str, element_id: str, data: Dict[str, Any]) -> bool:
        """保存小说元素"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO novel_elements (novel_id, element_type, element_id, data)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (novel_id, element_type, element_id)
                   DO UPDATE SET data = %s, updated_at = CURRENT_TIMESTAMP""",
                (novel_id, element_type, element_id, Json(data), Json(data))
            )
            
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"保存元素失败: {e}")
            return False
        finally:
            if conn:
                release_connection(conn)
    
    def get_element(self, novel_id: str, element_type: str, element_id: str) -> Optional[Dict[str, Any]]:
        """获取小说元素"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                """SELECT data FROM novel_elements 
                   WHERE novel_id = %s AND element_type = %s AND element_id = %s""",
                (novel_id, element_type, element_id)
            )
            
            result = cursor.fetchone()
            return result['data'] if result else None
        except Exception as e:
            logger.error(f"获取元素失败: {e}")
            return None
        finally:
            if conn:
                release_connection(conn)
    
    def get_elements_by_type(self, novel_id: str, element_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的所有元素"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                """SELECT element_id, data FROM novel_elements 
                   WHERE novel_id = %s AND element_type = %s
                   ORDER BY element_id""",
                (novel_id, element_type)
            )
            
            results = cursor.fetchall()
            return [item['data'] for item in results] if results else []
        except Exception as e:
            logger.error(f"获取元素列表失败: {e}")
            return []
        finally:
            if conn:
                release_connection(conn)
    
    def delete_element(self, novel_id: str, element_type: str, element_id: str) -> bool:
        """删除小说元素"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """DELETE FROM novel_elements 
                   WHERE novel_id = %s AND element_type = %s AND element_id = %s""",
                (novel_id, element_type, element_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"删除元素失败: {e}")
            return False
        finally:
            if conn:
                release_connection(conn)
    
    def get_novel_data(self, novel_id: str) -> Dict[str, Any]:
        """获取小说的所有数据"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 获取所有元素
            cursor.execute(
                """SELECT element_type, element_id, data FROM novel_elements 
                   WHERE novel_id = %s
                   ORDER BY element_type, element_id""",
                (novel_id,)
            )
            
            results = cursor.fetchall()
            
            # 组织数据结构
            novel_data = {
                "characters": [],
                "locations": [],
                "items": [],
                "outline": None,
                "chapters": []
            }
            
            for item in results:
                if item['element_type'] == 'character':
                    novel_data['characters'].append(item['data'])
                elif item['element_type'] == 'location':
                    novel_data['locations'].append(item['data'])
                elif item['element_type'] == 'item':
                    novel_data['items'].append(item['data'])
                elif item['element_type'] == 'outline':
                    novel_data['outline'] = item['data']
                elif item['element_type'] == 'chapter':
                    novel_data['chapters'].append(item['data'])
            
            return novel_data
        except Exception as e:
            logger.error(f"获取小说数据失败: {e}")
            return {
                "characters": [],
                "locations": [],
                "items": [],
                "outline": None,
                "chapters": []
            }
        finally:
            if conn:
                release_connection(conn)


class LangGraphStateStore:
    """LangGraph状态存储"""
    
    def __init__(self):
        """初始化存储"""
        # 确保数据库表已创建
        init_db()
    
    def save_state(self, thread_id: str, state: Dict[str, Any]) -> bool:
        """保存LangGraph状态"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO graph_states (thread_id, state)
                   VALUES (%s, %s)
                   ON CONFLICT (thread_id)
                   DO UPDATE SET state = %s, updated_at = CURRENT_TIMESTAMP""",
                (thread_id, Json(state), Json(state))
            )
            
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"保存状态失败: {e}")
            return False
        finally:
            if conn:
                release_connection(conn)
    
    def load_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载LangGraph状态"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute(
                "SELECT state FROM graph_states WHERE thread_id = %s",
                (thread_id,)
            )
            
            result = cursor.fetchone()
            return result['state'] if result else None
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return None
        finally:
            if conn:
                release_connection(conn)
    
    def delete_state(self, thread_id: str) -> bool:
        """删除LangGraph状态"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM graph_states WHERE thread_id = %s",
                (thread_id,)
            )
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"删除状态失败: {e}")
            return False
        finally:
            if conn:
                release_connection(conn)


# 创建存储实例
memory_store = PostgresMemoryStore()
element_store = NovelElementStore()
graph_store = LangGraphStateStore()

# 确保应用启动时初始化数据库
try:
    init_db()
except Exception as e:
    logger.error(f"数据库初始化失败，应用可能无法正常工作: {e}")
