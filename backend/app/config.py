import os
from pydantic_settings import BaseSettings
from enum import Enum

class ModelMode(str, Enum):
    api = "api"      # 接口调用
    local = "local"  # 本地模型

class Settings(BaseSettings):
    # 后端配置
    host: str = "0.0.0.0"
    port: int = 8000

    # AI 配置
    mode: ModelMode = ModelMode(os.getenv("MODE", "api"))  # "api" or "local"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    # 本地模型路径或配置
    local_model_path: str = os.getenv("LOCAL_MODEL_PATH", "")
    memory_type: str = os.getenv("MEMORY_TYPE", "in_memory")  # 可选: redis, file

    class Config:
        env_file = ".env"

settings = Settings()
