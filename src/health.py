"""
Health Check Module - 健康检查与系统监控
"""
import os
import sys
import time
import psutil
import platform
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.logger import get_logger


logger = get_logger(__name__)


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self._checks: Dict[str, Callable] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}
        self._register_default_checks()
    
    def _register_default_checks(self):
        """注册默认检查项"""
        self.register_check("system", self._check_system)
        self.register_check("disk", self._check_disk)
        self.register_check("memory", self._check_memory)
        self.register_check("network", self._check_network)
    
    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """注册健康检查项
        
        Args:
            name: 检查项名称
            check_func: 检查函数，返回HealthCheckResult
        """
        self._checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    def _check_system(self) -> HealthCheckResult:
        """检查系统信息"""
        try:
            details = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
            }
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="System is running",
                details=details
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system: {e}",
            )
    
    def _check_disk(self) -> HealthCheckResult:
        """检查磁盘空间"""
        try:
            usage = psutil.disk_usage('/')
            percent = usage.percent
            
            if percent > 95:
                status = HealthStatus.UNHEALTHY
                message = "Disk almost full"
            elif percent > 85:
                status = HealthStatus.DEGRADED
                message = "Disk space running low"
            else:
                status = HealthStatus.HEALTHY
                message = "Disk space OK"
            
            return HealthCheckResult(
                status=status,
                message=message,
                details={
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": percent
                }
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk: {e}",
            )
    
    def _check_memory(self) -> HealthCheckResult:
        """检查内存使用"""
        try:
            mem = psutil.virtual_memory()
            percent = mem.percent
            
            if percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "Memory critical"
            elif percent > 75:
                status = HealthStatus.DEGRADED
                message = "Memory high"
            else:
                status = HealthStatus.HEALTHY
                message = "Memory OK"
            
            return HealthCheckResult(
                status=status,
                message=message,
                details={
                    "total_gb": round(mem.total / (1024**3), 2),
                    "available_gb": round(mem.available / (1024**3), 2),
                    "percent": percent
                }
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check memory: {e}",
            )
    
    def _check_network(self) -> HealthCheckResult:
        """检查网络连接"""
        try:
            # 检查DNS解析
            import socket
            socket.setdefaulttimeout(5)
            socket.gethostbyname("www.baidu.com")
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Network is reachable",
                details={"dns": "ok"}
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Network issue: {e}",
            )
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """执行所有健康检查
        
        Returns:
            检查结果字典
        """
        results = {}
        
        for name, check_func in self._checks.items():
            start_time = time.time()
            try:
                result = check_func()
                result.duration_ms = (time.time() - start_time) * 1000
                results[name] = result
                self._last_results[name] = result
                
                status_emoji = {
                    HealthStatus.HEALTHY: "✅",
                    HealthStatus.DEGRADED: "⚠️",
                    HealthStatus.UNHEALTHY: "❌",
                    HealthStatus.UNKNOWN: "❓"
                }
                logger.info(f"Health check [{name}]: {status_emoji[result.status]} {result.message}")
                
            except Exception as e:
                logger.error(f"Health check [{name}] failed: {e}")
                results[name] = HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message=f"Check failed: {e}",
                    duration_ms=(time.time() - start_time) * 1000
                )
        
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """获取整体健康状态
        
        Returns:
            整体健康状态
        """
        if not self._last_results:
            return HealthStatus.UNKNOWN
        
        statuses = [r.status for r in self._last_results.values()]
        
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        if any(s == HealthStatus.UNKNOWN for s in statuses):
            return HealthStatus.UNKNOWN
        return HealthStatus.HEALTHY
    
    def get_status_report(self) -> Dict[str, Any]:
        """获取状态报告
        
        Returns:
            状态报告字典
        """
        overall = self.get_overall_status()
        results = self.check_all()
        
        return {
            "status": overall.value,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "duration_ms": round(result.duration_ms, 2),
                    "details": result.details
                }
                for name, result in results.items()
            }
        }


# 全局健康检查器实例
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """获取全局健康检查器"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def register_health_check(name: str, check_func: Callable[[], HealthCheckResult]):
    """注册自定义健康检查"""
    get_health_checker().register_check(name, check_func)


def check_health() -> Dict[str, Any]:
    """快速健康检查"""
    return get_health_checker().get_status_report()
