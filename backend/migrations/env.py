"""
Alembic环境配置
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 导入模型定义
from app.models import Base

# 加载Alembic配置
config = context.config

# 从环境变量获取数据库URL
db_url = os.environ.get(
    "DATABASE_URL",
    f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
    f"{os.environ.get('POSTGRES_PORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'novel_forge')}"
)

# 覆盖配置中的sqlalchemy.url
config.set_main_option("sqlalchemy.url", db_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标元数据
target_metadata = Base.metadata

def run_migrations_offline():
    """
    在"离线"模式下运行迁移
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """
    在"在线"模式下运行迁移
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
