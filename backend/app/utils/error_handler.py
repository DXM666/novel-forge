"""
错误处理模块 - 提供统一的错误处理机制
"""
from typing import Dict, Any, Optional, Callable, Union, Type
from functools import wraps
import time
import traceback

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 自定义错误代码
class ErrorCode:
    # 通用错误
    GENERAL_ERROR = "E000"
    VALIDATION_ERROR = "E001"
    
    # 数据库错误
    DB_CONNECTION_ERROR = "DB001"
    DB_QUERY_ERROR = "DB002"
    DB_TRANSACTION_ERROR = "DB003"
    
    # AI服务错误
    AI_SERVICE_ERROR = "AI001"
    AI_TIMEOUT_ERROR = "AI002"
    AI_RATE_LIMIT_ERROR = "AI003"
    
    # 缓存错误
    CACHE_ERROR = "CACHE001"
    
    # 向量存储错误
    VECTOR_STORE_ERROR = "VS001"
    
    # 认证错误
    AUTH_ERROR = "AUTH001"
    UNAUTHORIZED = "AUTH002"
    FORBIDDEN = "AUTH003"

# 应用错误基类
class AppError(Exception):
    """应用错误基类"""
    
    def __init__(
        self, 
        code: str = ErrorCode.GENERAL_ERROR, 
        message: str = "应用错误", 
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        original_error: Optional[Exception] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.original_error = original_error
        
        # 记录错误堆栈
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["traceback"] = traceback.format_exc()
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }

# 数据库错误类
class DatabaseError(AppError):
    """数据库错误类"""
    
    def __init__(
        self, 
        message: str = "数据库操作错误", 
        code: str = ErrorCode.DB_QUERY_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            original_error=original_error
        )

# AI服务错误类
class AIServiceError(AppError):
    """AI服务错误类"""
    
    def __init__(
        self, 
        message: str = "AI服务错误", 
        code: str = ErrorCode.AI_SERVICE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            original_error=original_error
        )

# 缓存错误类
class CacheError(AppError):
    """缓存错误类"""
    
    def __init__(
        self, 
        message: str = "缓存操作错误", 
        code: str = ErrorCode.CACHE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            original_error=original_error
        )

# 向量存储错误类
class VectorStoreError(AppError):
    """向量存储错误类"""
    
    def __init__(
        self, 
        message: str = "向量存储操作错误", 
        code: str = ErrorCode.VECTOR_STORE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            original_error=original_error
        )

# 认证错误类
class AuthError(AppError):
    """认证错误类"""
    
    def __init__(
        self, 
        message: str = "认证错误", 
        code: str = ErrorCode.AUTH_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            code=code,
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
            original_error=original_error
        )

# 错误处理装饰器
def handle_errors(
    error_map: Optional[Dict[Type[Exception], Type[AppError]]] = None,
    default_error_class: Type[AppError] = AppError
):
    """
    错误处理装饰器
    
    参数:
        error_map: 异常类型到应用错误类型的映射
        default_error_class: 默认的错误类
    """
    error_map = error_map or {}
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AppError as e:
                # 应用错误直接向上传递
                logger.error(f"应用错误: {e.code} - {e.message}")
                if e.details.get("traceback"):
                    logger.debug(f"错误堆栈: {e.details['traceback']}")
                raise
            except Exception as e:
                # 将其他异常转换为应用错误
                error_class = error_map.get(type(e), default_error_class)
                app_error = error_class(
                    message=f"操作失败: {str(e)}",
                    original_error=e
                )
                
                logger.error(f"捕获到异常: {type(e).__name__}, 转换为应用错误: {app_error.code}")
                logger.debug(f"原始错误: {e}")
                logger.debug(f"堆栈跟踪: {traceback.format_exc()}")
                
                raise app_error
        
        return wrapper
    
    return decorator

# 数据库操作重试装饰器
def retry_db_operation(
    max_retries: int = 3, 
    retry_delay: float = 0.5,
    backoff_factor: float = 2.0,
    exceptions_to_retry: tuple = (DatabaseError,)
):
    """
    数据库操作重试装饰器
    
    参数:
        max_retries: 最大重试次数
        retry_delay: 初始重试延迟（秒）
        backoff_factor: 重试延迟的增长因子（指数级增长）
        exceptions_to_retry: 需要重试的异常类型
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = retry_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"操作失败 (尝试 {attempt+1}/{max_retries+1}): {str(e)}, "
                            f"将在 {current_delay:.2f} 秒后重试"
                        )
                        
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(f"操作在 {max_retries+1} 次尝试后最终失败: {str(e)}")
            
            raise last_exception
        
        return wrapper
    
    return decorator

# FastAPI错误处理器
async def app_exception_handler(request: Request, exc: AppError):
    """
    应用错误处理器
    
    参数:
        request: FastAPI请求对象
        exc: 应用错误实例
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

# HTTP异常处理器
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理器
    
    参数:
        request: FastAPI请求对象
        exc: HTTP异常实例
    """
    app_error = AppError(
        code=f"HTTP{exc.status_code}",
        message=exc.detail,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=app_error.to_dict()
    )

# 验证错误处理器
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    验证错误处理器
    
    参数:
        request: FastAPI请求对象
        exc: 验证错误实例
    """
    app_error = AppError(
        code=ErrorCode.VALIDATION_ERROR,
        message="输入验证失败",
        details={"errors": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    
    return JSONResponse(
        status_code=app_error.status_code,
        content=app_error.to_dict()
    )

# 注册错误处理器
def register_exception_handlers(app):
    """
    注册所有异常处理器
    
    参数:
        app: FastAPI应用实例
    """
    # 应用错误处理器
    app.add_exception_handler(AppError, app_exception_handler)
    
    # HTTP异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # 验证错误处理器
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # 全局异常处理器 - 捕获所有未处理的异常
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {type(exc).__name__} - {str(exc)}")
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
        
        app_error = AppError(
            message=f"服务器内部错误: {str(exc)}",
            details={"type": type(exc).__name__}
        )
        
        return JSONResponse(
            status_code=app_error.status_code,
            content=app_error.to_dict()
        )
