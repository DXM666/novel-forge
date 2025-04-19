import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # 后端配置
    host: str = "0.0.0.0"
    port: int = 8000

    # AI 配置
    use_openai: bool = bool(os.getenv("OPENAI_API_KEY"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    # 本地模型路径或配置
    local_model_path: str = os.getenv("LOCAL_MODEL_PATH", "")
    memory_type: str = os.getenv("MEMORY_TYPE", "in_memory")  # 可选: redis, file

    class Config:
        env_file = ".env"

settings = Settings()
