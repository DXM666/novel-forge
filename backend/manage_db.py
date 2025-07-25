"""
数据库管理脚本 - 提供数据库迁移和管理功能
"""
import os
import sys
import argparse
import logging
from alembic import command
from alembic.config import Config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 获取Alembic配置
def get_alembic_config():
    """获取Alembic配置"""
    config = Config("alembic.ini")
    
    # 从环境变量获取数据库URL
    db_url = os.environ.get(
        "DATABASE_URL",
        f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:"
        f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@"
        f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
        f"{os.environ.get('POSTGRES_PORT', '5432')}/"
        f"{os.environ.get('POSTGRES_DB', 'novel_forge')}"
    )
    
    # 设置数据库URL
    config.set_main_option("sqlalchemy.url", db_url)
    
    return config

def upgrade(revision="head"):
    """升级数据库到指定版本"""
    config = get_alembic_config()
    logger.info(f"正在升级数据库到版本: {revision}")
    command.upgrade(config, revision)
    logger.info("数据库升级完成")

def downgrade(revision):
    """降级数据库到指定版本"""
    config = get_alembic_config()
    logger.info(f"正在降级数据库到版本: {revision}")
    command.downgrade(config, revision)
    logger.info("数据库降级完成")

def revision(message):
    """创建新的迁移脚本"""
    config = get_alembic_config()
    logger.info(f"正在创建新的迁移脚本: {message}")
    command.revision(config, message=message, autogenerate=True)
    logger.info("迁移脚本创建完成")

def current():
    """显示当前数据库版本"""
    config = get_alembic_config()
    command.current(config, verbose=True)

def history():
    """显示迁移历史"""
    config = get_alembic_config()
    command.history(config, verbose=True)

def init_db():
    """初始化数据库"""
    from app.models import init_db as init_models_db
    logger.info("正在初始化数据库模型...")
    init_models_db()
    logger.info("数据库模型初始化完成")
    
    # 执行迁移
    upgrade()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="数据库管理工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 升级命令
    upgrade_parser = subparsers.add_parser("upgrade", help="升级数据库")
    upgrade_parser.add_argument("--revision", default="head", help="目标版本，默认为最新版本")
    
    # 降级命令
    downgrade_parser = subparsers.add_parser("downgrade", help="降级数据库")
    downgrade_parser.add_argument("revision", help="目标版本")
    
    # 创建迁移脚本命令
    revision_parser = subparsers.add_parser("revision", help="创建新的迁移脚本")
    revision_parser.add_argument("message", help="迁移说明")
    
    # 当前版本命令
    subparsers.add_parser("current", help="显示当前数据库版本")
    
    # 历史命令
    subparsers.add_parser("history", help="显示迁移历史")
    
    # 初始化数据库命令
    subparsers.add_parser("init", help="初始化数据库")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 执行命令
    if args.command == "upgrade":
        upgrade(args.revision)
    elif args.command == "downgrade":
        downgrade(args.revision)
    elif args.command == "revision":
        revision(args.message)
    elif args.command == "current":
        current()
    elif args.command == "history":
        history()
    elif args.command == "init":
        init_db()
    else:
        parser.print_help()
