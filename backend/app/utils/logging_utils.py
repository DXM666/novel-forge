"""
日志工具模块 - 提供统一的日志配置和管理
"""
import os
import logging
import logging.handlers
from typing import Optional

# 日志级别映射
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 全局日志配置状态标志
_is_configured = False

def configure_logging(
    level: str = "info", 
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> None:
    """
    配置全局日志系统
    
    参数:
        level: 日志级别 (debug, info, warning, error, critical)
        log_file: 可选的日志文件路径
        log_format: 自定义日志格式
        max_bytes: 单个日志文件的最大字节数
        backup_count: 保留的备份文件数量
    """
    global _is_configured
    
    if _is_configured:
        return
    
    # 设置日志级别
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
    
    # 设置默认日志格式
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 创建格式化器
    formatter = logging.Formatter(log_format)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 如果提供了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建滚动文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 标记为已配置
    _is_configured = True
    
    logging.info("日志系统已配置完成")

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    参数:
        name: 日志记录器名称
    
    返回:
        日志记录器实例
    """
    # 确保全局日志已配置
    if not _is_configured:
        configure_logging()
    
    # 返回指定名称的日志记录器
    return logging.getLogger(name)

# 默认首次导入时配置
configure_logging()
