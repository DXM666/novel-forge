"""
错误处理中间件 - 提供统一的异常捕获和处理
"""
import time
import json
import logging
import traceback
from typing import Dict, Any, Callable, Awaitable, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorCode:
    """错误代码定义"""
    SUCCESS = 0
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    DATABASE_ERROR = 1002
    AUTH_ERROR = 1003
    NOT_FOUND = 1004
    PERMISSION_DENIED = 1005
    AI_MODEL_ERROR = 1006
    RATE_LIMIT_ERROR = 1007
    BAD_REQUEST = 1008
    VECTOR_DB_ERROR = 1009
    MEMORY_ERROR = 1010

class APIException(Exception):
    """API自定义异常基类"""
    def __init__(
        self, 
        message: str, 
        code: int = ErrorCode.UNKNOWN_ERROR, 
        status_code: int = 400, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class DatabaseError(APIException):
    """数据库错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.DATABASE_ERROR, 
            status_code=500,
            details=details
        )

class AuthError(APIException):
    """认证错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.AUTH_ERROR, 
            status_code=401,
            details=details
        )

class NotFoundError(APIException):
    """资源不存在错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.NOT_FOUND, 
            status_code=404,
            details=details
        )

class PermissionDeniedError(APIException):
    """权限错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.PERMISSION_DENIED, 
            status_code=403,
            details=details
        )

class AIModelError(APIException):
    """AI模型错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.AI_MODEL_ERROR, 
            status_code=500,
            details=details
        )

class RateLimitError(APIException):
    """速率限制错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.RATE_LIMIT_ERROR, 
            status_code=429,
            details=details
        )

class BadRequestError(APIException):
    """请求参数错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.BAD_REQUEST, 
            status_code=400,
            details=details
        )

class VectorDBError(APIException):
    """向量数据库错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.VECTOR_DB_ERROR, 
            status_code=500,
            details=details
        )

class MemoryError(APIException):
    """记忆系统错误"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message, 
            code=ErrorCode.MEMORY_ERROR, 
            status_code=500,
            details=details
        )

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        处理请求并捕获异常
        
        参数:
            request: FastAPI请求对象
            call_next: 调用下一个中间件的函数
        
        返回:
            Response对象
        """
        start_time = time.time()
        request_id = self._get_request_id(request)
        
        # 记录请求信息
        self._log_request(request, request_id)
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 记录处理时间
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            # 记录响应信息
            self._log_response(response, request_id, process_time)
            
            return response
            
        except ValidationError as exc:
            # 处理验证错误
            return self._handle_validation_error(exc, request_id)
        except APIException as exc:
            # 处理自定义API异常
            return self._handle_api_exception(exc, request_id)
        except Exception as exc:
            # 处理未预期的异常
            return self._handle_unexpected_error(exc, request_id)
    
    def _get_request_id(self, request: Request) -> str:
        """获取请求ID"""
        if "X-Request-ID" in request.headers:
            return request.headers["X-Request-ID"]
        return f"{time.time():.6f}"
    
    def _log_request(self, request: Request, request_id: str) -> None:
        """记录请求信息"""
        logger.info(
            f"Request [{request_id}]: {request.method} {request.url.path} "
            f"- ClientIP: {request.client.host}",
            extra={
                "request_id": request_id,
                "client_ip": request.client.host,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "headers": dict(request.headers)
            }
        )
    
    def _log_response(self, response: Response, request_id: str, process_time: float) -> None:
        """记录响应信息"""
        logger.info(
            f"Response [{request_id}]: Status {response.status_code} - Time: {process_time:.6f}s",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
                "headers": dict(response.headers)
            }
        )
    
    def _handle_validation_error(self, exc: ValidationError, request_id: str) -> JSONResponse:
        """处理验证错误"""
        error_details = [
            {
                "loc": err["loc"],
                "msg": err["msg"],
                "type": err["type"]
            }
            for err in exc.errors()
        ]
        
        logger.warning(
            f"Validation Error [{request_id}]: {str(exc)}",
            extra={
                "request_id": request_id,
                "error_details": error_details
            }
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "参数验证错误",
                "data": None,
                "error": {
                    "details": error_details
                }
            }
        )
    
    def _handle_api_exception(self, exc: APIException, request_id: str) -> JSONResponse:
        """处理自定义API异常"""
        logger.warning(
            f"API Exception [{request_id}]: {str(exc)}",
            extra={
                "request_id": request_id,
                "error_code": exc.code,
                "error_details": exc.details
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": None,
                "error": {
                    "details": exc.details
                }
            }
        )
    
    def _handle_unexpected_error(self, exc: Exception, request_id: str) -> JSONResponse:
        """处理未预期的异常"""
        error_traceback = traceback.format_exc()
        
        logger.error(
            f"Unexpected Error [{request_id}]: {str(exc)}",
            extra={
                "request_id": request_id,
                "error_traceback": error_traceback
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": ErrorCode.UNKNOWN_ERROR,
                "message": "服务器内部错误",
                "data": None,
                "error": {
                    "details": str(exc)
                }
            }
        )

def register_error_handlers(app: FastAPI) -> None:
    """注册错误处理器"""
    app.add_middleware(ErrorHandlerMiddleware)
    
    # 可以在这里添加更多特定的错误处理器
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        error_details = [
            {
                "loc": err["loc"],
                "msg": err["msg"],
                "type": err["type"]
            }
            for err in exc.errors()
        ]
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "参数验证错误",
                "data": None,
                "error": {
                    "details": error_details
                }
            }
        )
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": None,
                "error": {
                    "details": exc.details
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        error_traceback = traceback.format_exc()
        logger.error(f"Unexpected Error: {str(exc)}\n{error_traceback}")
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": ErrorCode.UNKNOWN_ERROR,
                "message": "服务器内部错误",
                "data": None,
                "error": {
                    "details": str(exc)
                }
            }
        )
