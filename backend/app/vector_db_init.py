"""
向量数据库初始化模块 - 负责创建和初始化向量数据库
支持PostgreSQL的pg_vector扩展或外部向量数据库
"""
import subprocess
from typing import Dict, Any, List, Optional, Tuple

from .database.db_utils import get_db_connection, release_db_connection, execute_query
from .config import settings
from .utils.logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

def check_pg_vector_extension() -> bool:
    """
    检查PostgreSQL是否已安装pg_vector扩展
    
    返回:
        是否已安装
    """
    query = "SELECT * FROM pg_extension WHERE extname = 'vector'"
    success, result = execute_query(query)
    
    if not success:
        logger.error(f"检查pg_vector扩展失败: {result}")
        return False
    
    return len(result) > 0

def create_pg_vector_extension() -> bool:
    """
    创建PostgreSQL的pg_vector扩展
    
    返回:
        是否成功
    """
    query = "CREATE EXTENSION IF NOT EXISTS vector"
    success, result = execute_query(query, fetch=False)
    
    if not success:
        logger.error(f"创建pg_vector扩展失败: {result}")
        return False
    
    logger.info("成功创建pg_vector扩展")
    return True

def create_vector_index() -> bool:
    """
    为向量记忆表创建向量索引
    
    返回:
        是否成功
    """
    # 检查表是否存在
    check_query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'vector_memories'
    )
    """
    success, result = execute_query(check_query)
    
    if not success:
        logger.error(f"检查向量记忆表失败: {result}")
        return False
    
    if not result or not result[0]['exists']:
        logger.warning("向量记忆表不存在，无法创建索引")
        return False
    
    # 添加向量列
    add_column_query = """
    ALTER TABLE vector_memories 
    ADD COLUMN IF NOT EXISTS embedding_vector vector(1536)
    """
    success, result = execute_query(add_column_query, fetch=False)
    
    if not success:
        logger.error(f"添加向量列失败: {result}")
        return False
    
    # 创建更新向量的触发器函数
    trigger_func_query = """
    CREATE OR REPLACE FUNCTION update_embedding_vector()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.embedding_vector = NEW.embedding::vector;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
    success, result = execute_query(trigger_func_query, fetch=False)
    
    if not success:
        logger.error(f"创建触发器函数失败: {result}")
        return False
    
    # 创建触发器
    trigger_query = """
    DROP TRIGGER IF EXISTS update_vector_memories_embedding_vector ON vector_memories;
    CREATE TRIGGER update_vector_memories_embedding_vector
    BEFORE INSERT OR UPDATE ON vector_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_embedding_vector();
    """
    success, result = execute_query(trigger_query, fetch=False)
    
    if not success:
        logger.error(f"创建触发器失败: {result}")
        return False
    
    # 创建向量索引
    index_query = """
    CREATE INDEX IF NOT EXISTS idx_vector_memories_embedding_vector 
    ON vector_memories USING ivfflat (embedding_vector vector_cosine_ops);
    """
    success, result = execute_query(index_query, fetch=False)
    
    if not success:
        logger.error(f"创建向量索引失败: {result}")
        return False
    
    logger.info("成功创建向量索引")
    return True

def update_existing_vectors() -> bool:
    """
    更新现有向量数据
    
    返回:
        是否成功
    """
    # 检查是否有需要更新的向量
    check_query = """
    SELECT COUNT(*) FROM vector_memories 
    WHERE embedding IS NOT NULL AND embedding_vector IS NULL
    """
    success, result = execute_query(check_query)
    
    if not success:
        logger.error(f"检查需要更新的向量失败: {result}")
        return False
    
    count = result[0]['count'] if result else 0
    if count == 0:
        logger.info("没有需要更新的向量")
        return True
    
    # 更新现有向量
    update_query = """
    UPDATE vector_memories 
    SET embedding_vector = embedding::vector
    WHERE embedding IS NOT NULL AND embedding_vector IS NULL
    """
    success, result = execute_query(update_query, fetch=False)
    
    if not success:
        logger.error(f"更新现有向量失败: {result}")
        return False
    
    logger.info(f"成功更新 {count} 个向量")
    return True

def init_vector_db() -> bool:
    """
    初始化向量数据库
    
    返回:
        是否成功
    """
    # 检查pg_vector扩展
    if not check_pg_vector_extension():
        logger.info("pg_vector扩展未安装，尝试安装...")
        if not create_pg_vector_extension():
            logger.error("无法创建pg_vector扩展，请确保PostgreSQL支持此扩展")
            return False
    
    # 创建向量索引
    if not create_vector_index():
        logger.error("创建向量索引失败")
        return False
    
    # 更新现有向量
    if not update_existing_vectors():
        logger.warning("更新现有向量失败，但可以继续使用")
    
    logger.info("向量数据库初始化成功")
    return True

def check_external_vector_db() -> bool:
    """
    检查外部向量数据库配置
    
    返回:
        是否配置正确
    """
    # 使用统一配置
    vector_db_type = settings.vector_store_provider or "postgres"
    
    if vector_db_type == "postgres":
        # 使用内置的PostgreSQL向量扩展
        return init_vector_db()
    elif vector_db_type == "pinecone":
        # 检查Pinecone配置
        api_key = settings.pinecone_api_key
        environment = settings.pinecone_env
        
        if not api_key or not environment:
            logger.error("缺少Pinecone配置: 需要pinecone_api_key和pinecone_env")
            return False
        
        logger.info("Pinecone配置正确")
        return True
    elif vector_db_type == "weaviate":
        # 检查Weaviate配置
        url = settings.weaviate_url
        
        if not url:
            logger.error("缺少Weaviate配置: 需要weaviate_url")
            return False
        
        logger.info("Weaviate配置正确")
        return True
    elif vector_db_type == "chroma":
        # 检查Chroma配置
        host = settings.chroma_host
        port = settings.chroma_port
        
        if not host:
            logger.warning("未指定chroma_host，将使用默认值（localhost）")
        
        logger.info("Chroma配置正确")
        return True
    else:
        logger.error(f"不支持的向量数据库类型: {vector_db_type}")
        return False

if __name__ == "__main__":
    # 直接运行此脚本可以初始化向量数据库
    if init_vector_db():
        print("向量数据库初始化成功")
    else:
        print("向量数据库初始化失败")
