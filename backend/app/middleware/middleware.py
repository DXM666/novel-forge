"""
中间件注册模块 - 注册并配置所有中间件
"""
import time
import logging
from typing import List, Dict

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .error_handler import register_error_handlers

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_middlewares(app: FastAPI) -> None:
    """
    设置并注册所有中间件
    
    参数:
        app: FastAPI应用实例
    """
    # 设置CORS
    setup_cors_middleware(app)
    
    # 设置Gzip压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    logger.info("所有中间件已注册")

def setup_cors_middleware(app: FastAPI) -> None:
    """
    设置CORS中间件
    
    参数:
        app: FastAPI应用实例
    """
    origins = [
        "http://localhost",
        "http://localhost:5173",  # Vite默认端口
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        # 生产环境域名可以在这里添加
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info(f"CORS中间件已配置，允许的源: {origins}")
