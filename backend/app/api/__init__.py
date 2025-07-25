"""
API路由模块 - 集中管理所有API路由
"""
from fastapi import APIRouter

# 创建根路由
api_router = APIRouter()

# 导入并注册各子路由
from .health import router as health_router

# 注册子路由
api_router.include_router(health_router)
