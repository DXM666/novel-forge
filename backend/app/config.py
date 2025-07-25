"""
配置模块 - 管理所有系统配置参数
为项目提供集中化的配置管理
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from pydantic_settings import BaseSettings
from enum import Enum


class ModelMode(str, Enum):
    """AI模型运行模式"""
    api = "api"      # 接口调用
    local = "local"  # 本地模型


class CacheType(str, Enum):
    """缓存类型"""
    memory = "memory"  # 内存缓存
    redis = "redis"    # Redis缓存


class LogLevel(str, Enum):
    """日志级别"""
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class Settings(BaseSettings):
    """App统一配置类"""
    # 后端服务配置
    app_name: str = "NovelForge"
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    root_path: str = ""
    
    # 日志配置
    log_level: LogLevel = LogLevel(os.getenv("LOG_LEVEL", "info"))
    log_file: Optional[str] = os.getenv("LOG_FILE", None)
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 数据库配置
    postgres_db: str = os.getenv("POSTGRES_DB", "novel_forge")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    db_pool_min_size: int = int(os.getenv("DB_POOL_MIN_SIZE", "1"))
    db_pool_max_size: int = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
    
    # 缓存配置
    cache_type: CacheType = CacheType(os.getenv("CACHE_TYPE", "memory"))
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # 默认1小时
    
    # AI 模型配置
    ai_mode: ModelMode = ModelMode(os.getenv("AI_MODE", "api"))  # "api" or "local"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: Optional[str] = os.getenv("OPENAI_API_BASE")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    local_model_path: str = os.getenv("LOCAL_MODEL_PATH", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama2")
    
    # 向量存储配置
    vector_store_provider: Optional[str] = os.getenv("VECTOR_STORE_PROVIDER")  # pinecone, weaviate, chroma等
    pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
    pinecone_env: str = os.getenv("PINECONE_ENV", "us-west1-gcp")
    pinecone_index: str = os.getenv("PINECONE_INDEX", "novel-forge")
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    weaviate_api_key: Optional[str] = os.getenv("WEAVIATE_API_KEY")
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8000"))
    
    # 语言嵌入模型配置
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # 上下文管理配置
    max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", "4000"))
    max_prompt_tokens: int = int(os.getenv("MAX_PROMPT_TOKENS", "2000"))
    max_response_tokens: int = int(os.getenv("MAX_RESPONSE_TOKENS", "2000"))
    
    # CORS配置
    cors_origins: List[str] = json.loads(os.getenv("CORS_ORIGINS", "[\"http://localhost\", \"http://localhost:5173\", \"http://localhost:3000\"]"))
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # 安全配置
    secret_key: str = os.getenv("SECRET_KEY", "supersecretkey")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    @property
    def database_url(self) -> str:
        """PostgreSQL连接URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def db_config(self) -> Dict[str, Any]:
        """PostgreSQL连接配置字典"""
        return {
            'dbname': self.postgres_db,
            'user': self.postgres_user,
            'password': self.postgres_password,
            'host': self.postgres_host,
            'port': self.postgres_port,
        }
    
    @property
    def redis_url(self) -> str:
        """Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局配置实例
settings = Settings()
