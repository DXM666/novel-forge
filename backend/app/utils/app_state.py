"""
应用状态管理模块 - 提供全局应用状态的管理和访问
"""
from typing import Dict, Any, Optional, List, Set
import time
import threading
from enum import Enum

from .logging_utils import get_logger

# 获取日志记录器
logger = get_logger(__name__)

class ServiceStatus(str, Enum):
    """服务状态枚举"""
    STARTING = "starting"      # 服务正在启动
    RUNNING = "running"        # 服务正常运行
    DEGRADED = "degraded"      # 服务部分功能受限
    UNAVAILABLE = "unavailable"  # 服务不可用
    MAINTENANCE = "maintenance"  # 服务维护中
    STOPPING = "stopping"      # 服务正在停止

class AppState:
    """应用状态管理类，维护全局应用状态"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppState, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        """初始化应用状态"""
        # 基本状态信息
        self._start_time = time.time()
        self._status = ServiceStatus.STARTING
        self._maintenance_mode = False
        
        # 组件状态
        self._component_status = {}
        
        # 性能指标
        self._request_count = 0
        self._error_count = 0
        self._avg_response_time = 0.0
        
        # 活跃会话
        self._active_sessions = set()
        
        # 自定义状态数据
        self._custom_state = {}
        
        # 记录启动
        logger.info("应用状态管理器初始化")
    
    @property
    def uptime_seconds(self) -> float:
        """获取应用运行时间（秒）"""
        return time.time() - self._start_time
    
    @property
    def uptime_formatted(self) -> str:
        """获取格式化的应用运行时间"""
        seconds = self.uptime_seconds
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{int(days)}天")
        if hours > 0 or days > 0:
            parts.append(f"{int(hours)}小时")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{int(minutes)}分钟")
        parts.append(f"{int(seconds)}秒")
        
        return " ".join(parts)
    
    @property
    def status(self) -> ServiceStatus:
        """获取当前服务状态"""
        return self._status
    
    @status.setter
    def status(self, value: ServiceStatus):
        """设置当前服务状态"""
        old_status = self._status
        self._status = value
        logger.info(f"应用状态从 {old_status} 变更为 {value}")
    
    def set_component_status(self, component: str, status: ServiceStatus, message: Optional[str] = None):
        """
        设置组件状态
        
        参数:
            component: 组件名称
            status: 组件状态
            message: 状态说明信息
        """
        old_status = self._component_status.get(component, {}).get("status")
        self._component_status[component] = {
            "status": status,
            "message": message,
            "last_update": time.time()
        }
        
        if old_status != status:
            logger.info(f"组件 {component} 状态从 {old_status} 变更为 {status}")
            if message:
                logger.info(f"组件 {component} 状态信息: {message}")
            
            # 更新整体应用状态
            self._update_overall_status()
    
    def get_component_status(self, component: str) -> Dict[str, Any]:
        """
        获取组件状态
        
        参数:
            component: 组件名称
            
        返回:
            组件状态字典
        """
        return self._component_status.get(component, {"status": None, "message": None})
    
    def _update_overall_status(self):
        """更新整体应用状态"""
        # 如果处于维护模式，优先返回维护状态
        if self._maintenance_mode:
            self.status = ServiceStatus.MAINTENANCE
            return
        
        # 检查所有组件状态，决定整体状态
        statuses = [info["status"] for info in self._component_status.values()]
        
        if not statuses:
            # 没有组件状态记录
            return
            
        if ServiceStatus.UNAVAILABLE in statuses:
            self.status = ServiceStatus.DEGRADED
        elif all(s == ServiceStatus.RUNNING for s in statuses):
            self.status = ServiceStatus.RUNNING
        else:
            self.status = ServiceStatus.DEGRADED
    
    def enter_maintenance_mode(self, message: Optional[str] = None):
        """进入维护模式"""
        self._maintenance_mode = True
        self.status = ServiceStatus.MAINTENANCE
        logger.warning(f"应用进入维护模式 {message or ''}")
    
    def exit_maintenance_mode(self):
        """退出维护模式"""
        self._maintenance_mode = False
        logger.info("应用退出维护模式")
        self._update_overall_status()
    
    def track_request(self, response_time: float, is_error: bool = False):
        """
        跟踪请求统计
        
        参数:
            response_time: 响应时间（秒）
            is_error: 是否为错误请求
        """
        self._request_count += 1
        if is_error:
            self._error_count += 1
        
        # 更新平均响应时间
        if self._request_count == 1:
            self._avg_response_time = response_time
        else:
            # 指数移动平均
            alpha = 0.05  # 权重因子
            self._avg_response_time = (1 - alpha) * self._avg_response_time + alpha * response_time
    
    def add_session(self, session_id: str):
        """
        添加活跃会话
        
        参数:
            session_id: 会话ID
        """
        self._active_sessions.add(session_id)
    
    def remove_session(self, session_id: str):
        """
        移除活跃会话
        
        参数:
            session_id: 会话ID
        """
        if session_id in self._active_sessions:
            self._active_sessions.remove(session_id)
    
    @property
    def active_session_count(self) -> int:
        """获取活跃会话数量"""
        return len(self._active_sessions)
    
    def set_custom_state(self, key: str, value: Any):
        """
        设置自定义状态
        
        参数:
            key: 状态键
            value: 状态值
        """
        self._custom_state[key] = value
    
    def get_custom_state(self, key: str, default: Any = None) -> Any:
        """
        获取自定义状态
        
        参数:
            key: 状态键
            default: 默认值
            
        返回:
            状态值
        """
        return self._custom_state.get(key, default)
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态摘要
        
        返回:
            健康状态字典
        """
        return {
            "status": self.status,
            "uptime": self.uptime_seconds,
            "uptime_formatted": self.uptime_formatted,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": (self._error_count / self._request_count) if self._request_count > 0 else 0,
            "avg_response_time": self._avg_response_time,
            "active_sessions": self.active_session_count,
            "components": self._component_status
        }
    
    def reset_metrics(self):
        """重置性能指标"""
        self._request_count = 0
        self._error_count = 0
        self._avg_response_time = 0.0
        logger.info("应用性能指标已重置")

# 单例实例
app_state = AppState()

# 简便访问函数
def get_app_state() -> AppState:
    """获取应用状态实例"""
    return app_state
