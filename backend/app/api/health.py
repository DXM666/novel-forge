"""
健康检查API路由 - 提供应用健康状态监控接口
"""
from fastapi import APIRouter, Depends, Request
from typing import Dict, Any

from ..utils.app_state import get_app_state, ServiceStatus
from ..utils.logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 创建路由
router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def health_check(request: Request) -> Dict[str, Any]:
    """
    健康检查接口，返回应用的基本健康状态
    """
    app_state = get_app_state()
    
    # 获取基本健康状态
    health_data = {
        "status": app_state.status,
        "uptime": app_state.uptime_formatted,
        "environment": request.app.state.env
    }
    
    return health_data

@router.get("/status")
async def detailed_status() -> Dict[str, Any]:
    """
    获取详细的应用状态信息，包括各组件状态和性能指标
    """
    app_state = get_app_state()
    return app_state.get_health_status()

@router.post("/maintenance", status_code=202)
async def set_maintenance_mode(enable: bool = True, message: str = None) -> Dict[str, Any]:
    """
    设置维护模式
    
    参数:
        enable: 是否启用维护模式
        message: 维护说明信息
    """
    app_state = get_app_state()
    
    if enable:
        app_state.enter_maintenance_mode(message)
        logger.warning(f"手动设置应用进入维护模式: {message}")
        return {"status": "maintenance", "message": "应用已进入维护模式"}
    else:
        app_state.exit_maintenance_mode()
        logger.info("手动设置应用退出维护模式")
        return {"status": app_state.status, "message": "应用已退出维护模式"}

@router.post("/reset-metrics", status_code=202)
async def reset_metrics() -> Dict[str, str]:
    """重置应用性能指标"""
    app_state = get_app_state()
    app_state.reset_metrics()
    
    return {"message": "应用性能指标已重置"}
