"""
配置验证模块 - 负责验证应用配置的完整性和正确性
"""
from typing import List, Dict, Any, Tuple, Optional
import re
import os

from ..config import settings
from .logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

class ConfigError(Exception):
    """配置错误异常类"""
    pass

def validate_db_config() -> Tuple[bool, List[str]]:
    """
    验证数据库配置
    
    返回:
        (是否验证通过, 错误信息列表)
    """
    errors = []
    
    # 检查必要的数据库配置
    if not settings.db_config.get('dbname'):
        errors.append("缺少数据库名称配置")
    
    if not settings.db_config.get('user'):
        errors.append("缺少数据库用户名配置")
    
    # 检查数据库URL格式
    if settings.database_url:
        url_pattern = r'^postgresql://[^:]+:[^@]+@[^:]+:\d+/\w+$'
        if not re.match(url_pattern, settings.database_url):
            errors.append(f"数据库URL格式不正确: {settings.database_url}")
    else:
        errors.append("缺少数据库URL配置")
    
    return len(errors) == 0, errors

def validate_redis_config() -> Tuple[bool, List[str]]:
    """
    验证Redis配置
    
    返回:
        (是否验证通过, 错误信息列表)
    """
    errors = []
    
    # 如果使用Redis缓存，检查相关配置
    if settings.cache_type == 'redis':
        if not settings.redis_host:
            errors.append("使用Redis缓存但未配置redis_host")
        
        if not settings.redis_port:
            errors.append("使用Redis缓存但未配置redis_port")
        
        # 端口需要是整数
        try:
            port = int(settings.redis_port)
            if port <= 0 or port > 65535:
                errors.append(f"Redis端口配置无效: {port}")
        except (ValueError, TypeError):
            errors.append(f"Redis端口必须是整数: {settings.redis_port}")
    
    return len(errors) == 0, errors

def validate_ai_model_config() -> Tuple[bool, List[str]]:
    """
    验证AI模型配置
    
    返回:
        (是否验证通过, 错误信息列表)
    """
    errors = []
    
    # 检查模型提供商配置
    if settings.model_provider == 'openai':
        if not settings.openai_api_key:
            errors.append("使用OpenAI但未配置openai_api_key")
        
        if not settings.openai_model:
            errors.append("使用OpenAI但未配置openai_model")
    
    elif settings.model_provider == 'local':
        if not settings.local_model_path:
            errors.append("使用本地模型但未配置local_model_path")
        
        # 检查本地模型文件是否存在
        if settings.local_model_path and not os.path.exists(settings.local_model_path):
            errors.append(f"本地模型路径不存在: {settings.local_model_path}")
    
    elif settings.model_provider == 'huggingface':
        if not settings.huggingface_model:
            errors.append("使用HuggingFace但未配置huggingface_model")
    
    return len(errors) == 0, errors

def validate_vector_store_config() -> Tuple[bool, List[str]]:
    """
    验证向量存储配置
    
    返回:
        (是否验证通过, 错误信息列表)
    """
    errors = []
    
    # 根据配置的向量存储类型验证
    if settings.vector_store_provider == 'pinecone':
        if not settings.pinecone_api_key:
            errors.append("使用Pinecone但未配置pinecone_api_key")
        
        if not settings.pinecone_env:
            errors.append("使用Pinecone但未配置pinecone_env")
    
    elif settings.vector_store_provider == 'weaviate':
        if not settings.weaviate_url:
            errors.append("使用Weaviate但未配置weaviate_url")
    
    elif settings.vector_store_provider == 'chroma':
        # Chroma可以使用默认配置，所以这里没有严格验证
        pass
    
    return len(errors) == 0, errors

def validate_all_configs() -> Tuple[bool, Dict[str, List[str]]]:
    """
    验证所有配置
    
    返回:
        (是否全部验证通过, 分类错误信息字典)
    """
    error_dict = {}
    all_valid = True
    
    # 验证数据库配置
    db_valid, db_errors = validate_db_config()
    if not db_valid:
        error_dict['database'] = db_errors
        all_valid = False
    
    # 验证Redis配置
    redis_valid, redis_errors = validate_redis_config()
    if not redis_valid:
        error_dict['redis'] = redis_errors
        all_valid = False
    
    # 验证AI模型配置
    ai_valid, ai_errors = validate_ai_model_config()
    if not ai_valid:
        error_dict['ai_model'] = ai_errors
        all_valid = False
    
    # 验证向量存储配置
    vector_valid, vector_errors = validate_vector_store_config()
    if not vector_valid:
        error_dict['vector_store'] = vector_errors
        all_valid = False
    
    return all_valid, error_dict

def print_validation_results(all_valid: bool, error_dict: Dict[str, List[str]]) -> None:
    """
    打印配置验证结果
    
    参数:
        all_valid: 是否全部验证通过
        error_dict: 分类错误信息字典
    """
    if all_valid:
        logger.info("✅ 所有配置验证通过")
        return
    
    logger.error("❌ 配置验证失败")
    
    for category, errors in error_dict.items():
        logger.error(f"[{category}] 配置错误:")
        for error in errors:
            logger.error(f"  - {error}")

def validate_config(exit_on_error: bool = False) -> bool:
    """
    验证配置并决定是否在错误时退出
    
    参数:
        exit_on_error: 当验证失败时是否退出程序
        
    返回:
        是否验证通过
    """
    all_valid, error_dict = validate_all_configs()
    print_validation_results(all_valid, error_dict)
    
    if not all_valid and exit_on_error:
        logger.critical("由于配置错误，应用将退出")
        import sys
        sys.exit(1)
    
    return all_valid
