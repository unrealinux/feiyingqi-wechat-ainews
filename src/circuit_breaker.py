"""
Circuit Breaker - 熔断器模式实现
用于防止级联故障，增强系统稳定性
"""
import time
import threading
import logging
from typing import Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps

from src.logger import get_logger


logger = get_logger(__name__)


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 半开


@dataclass
class CircuitStats:
    """熔断器统计"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    state_change_times: int = 0
    
    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,        # 连续失败次数阈值
        success_threshold: int = 3,         # 半开状态下连续成功次数
        timeout: float = 30.0,              # 熔断超时时间(秒)
        excluded_exceptions: tuple = (),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.excluded_exceptions = excluded_exceptions
        
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._lock = threading.RLock()
        self._last_state_change = time.time()
    
    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # 检查是否超时
                if time.time() - self._last_state_change >= self.timeout:
                    logger.info(f"Circuit breaker [{self.name}] transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
                    self._last_state_change = time.time()
                    self._stats.state_change_times += 1
            return self._state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数，带熔断保护
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值
        
        Raises:
            CircuitBreakerOpenError: 熔断器开启时
            Exception: 函数执行失败时
        """
        # 检查状态
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker [{self.name}] is OPEN"
            )
        
        # 执行函数
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.excluded_exceptions:
            # 排除的异常不计入熔断
            raise
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """成功回调"""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.successful_calls += 1
            self._stats.consecutive_successes += 1
            self._stats.consecutive_failures = 0
            self._stats.last_success_time = time.time()
            
            # 半开状态下连续成功
            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.success_threshold:
                    logger.info(f"Circuit breaker [{self.name}] transitioning to CLOSED")
                    self._state = CircuitState.CLOSED
                    self._last_state_change = time.time()
                    self._stats.state_change_times += 1
                    self._stats.consecutive_successes = 0
    
    def _on_failure(self):
        """失败回调"""
        with self._lock:
            self._stats.total_calls += 1
            self._stats.failed_calls += 1
            self._stats.consecutive_failures += 1
            self._stats.consecutive_successes = 0
            self._stats.last_failure_time = time.time()
            
            # 触发熔断
            if self._state == CircuitState.CLOSED:
                if self._stats.consecutive_failures >= self.failure_threshold:
                    logger.warning(
                        f"Circuit breaker [{self.name}] OPENING "
                        f"(failures: {self._stats.consecutive_failures})"
                    )
                    self._state = CircuitState.OPEN
                    self._last_state_change = time.time()
                    self._stats.state_change_times += 1
            
            # 半开状态下失败
            elif self._state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit breaker [{self.name}] reopening")
                self._state = CircuitState.OPEN
                self._last_state_change = time.time()
                self._stats.state_change_times += 1
    
    def reset(self):
        """手动重置熔断器"""
        with self._lock:
            logger.info(f"Circuit breaker [{self.name}] manually reset")
            self._state = CircuitState.CLOSED
            self._stats = CircuitStats()
            self._last_state_change = time.time()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "total_calls": self._stats.total_calls,
                "successful_calls": self._stats.successful_calls,
                "failed_calls": self._stats.failed_calls,
                "failure_rate": f"{self._stats.failure_rate:.2%}",
                "consecutive_failures": self._stats.consecutive_failures,
                "state_change_times": self._stats.state_change_times,
            }


class CircuitBreakerOpenError(Exception):
    """熔断器开启异常"""
    pass


def circuit_breaker(
    name: str = None,
    failure_threshold: int = 5,
    success_threshold: int = 3,
    timeout: float = 30.0,
):
    """熔断器装饰器
    
    Args:
        name: 熔断器名称(默认使用函数名)
        failure_threshold: 连续失败次数阈值
        success_threshold: 半开状态下连续成功次数
        timeout: 熔断超时时间
    
    Usage:
        @circuit_breaker("my_service", failure_threshold=3)
        def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        _breaker = CircuitBreaker(
            breaker_name,
            failure_threshold,
            success_threshold,
            timeout
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return _breaker.call(func, *args, **kwargs)
        
        # 暴露熔断器
        wrapper.circuit_breaker = _breaker
        return wrapper
    
    return decorator


# 全局熔断器管理器
_circuit_breakers: dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """获取或创建熔断器"""
    with _breakers_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name)
        return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict[str, dict]:
    """获取所有熔断器状态"""
    return {
        name: breaker.get_stats()
        for name, breaker in _circuit_breakers.items()
    }


def reset_all_circuit_breakers():
    """重置所有熔断器"""
    for breaker in _circuit_breakers.values():
        breaker.reset()
    logger.info("All circuit breakers reset")
