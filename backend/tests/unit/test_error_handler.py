"""
错误处理中间件单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError

from app.middleware.error_handler import (
    ErrorHandlerMiddleware, APIException, 
    DatabaseError, AuthError, NotFoundError,
    ErrorCode
)

class TestErrorHandlerMiddleware:
    """错误处理中间件测试类"""
    
    def test_api_exception_hierarchy(self):
        """测试API异常层次结构"""
        # 创建基础API异常
        base_exc = APIException("基础异常")
        assert base_exc.message == "基础异常"
        assert base_exc.code == ErrorCode.UNKNOWN_ERROR
        assert base_exc.status_code == 400
        
        # 创建数据库异常
        db_exc = DatabaseError("数据库异常")
        assert db_exc.message == "数据库异常"
        assert db_exc.code == ErrorCode.DATABASE_ERROR
        assert db_exc.status_code == 500
        
        # 创建认证异常
        auth_exc = AuthError("认证异常")
        assert auth_exc.message == "认证异常"
        assert auth_exc.code == ErrorCode.AUTH_ERROR
        assert auth_exc.status_code == 401
        
        # 创建资源不存在异常
        not_found_exc = NotFoundError("资源不存在")
        assert not_found_exc.message == "资源不存在"
        assert not_found_exc.code == ErrorCode.NOT_FOUND
        assert not_found_exc.status_code == 404
    
    @pytest.mark.asyncio
    async def test_middleware_normal_flow(self):
        """测试中间件正常流程"""
        # 创建模拟应用
        app = FastAPI()
        
        # 创建模拟请求
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        # 创建模拟响应
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 200
        
        # 创建模拟回调
        async def mock_call_next(request):
            return mock_response
        
        # 创建中间件
        middleware = ErrorHandlerMiddleware(app)
        
        # 调用中间件
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # 验证结果
        assert response == mock_response
        assert "X-Process-Time" in response.headers
        assert "X-Request-ID" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_api_exception(self):
        """测试中间件处理API异常"""
        # 创建模拟应用
        app = FastAPI()
        
        # 创建模拟请求
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        # 创建抛出异常的回调
        async def mock_call_next(request):
            raise NotFoundError("资源不存在", details={"resource_id": "123"})
        
        # 创建中间件
        middleware = ErrorHandlerMiddleware(app)
        
        # 调用中间件
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # 验证结果
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        # 验证响应内容
        content = response.body.decode()
        assert "资源不存在" in content
        assert str(ErrorCode.NOT_FOUND) in content
        assert "resource_id" in content
    
    @pytest.mark.asyncio
    async def test_middleware_unexpected_exception(self):
        """测试中间件处理意外异常"""
        # 创建模拟应用
        app = FastAPI()
        
        # 创建模拟请求
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        # 创建抛出异常的回调
        async def mock_call_next(request):
            raise RuntimeError("意外错误")
        
        # 创建中间件
        middleware = ErrorHandlerMiddleware(app)
        
        # 调用中间件
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        # 验证结果
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        # 验证响应内容
        content = response.body.decode()
        assert "服务器内部错误" in content
        assert str(ErrorCode.UNKNOWN_ERROR) in content
