"""
Config Hot Reload - 配置热加载模块
"""
import os
import time
import hashlib
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from src.logger import get_logger


logger = get_logger(__name__)


@dataclass
class ConfigState:
    """配置状态"""
    config: Dict[str, Any]
    last_modified: float
    checksum: str


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件事件处理器"""
    
    def __init__(self, config_path: str, on_change: Callable[[], None]):
        self.config_path = Path(config_path)
        self.on_change = on_change
        self._last_reload = 0
        self._debounce_seconds = 1
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        event_path = Path(event.src_path)
        if event_path.resolve() == self.config_path.resolve():
            # 防抖处理
            current_time = time.time()
            if current_time - self._last_reload > self._debounce_seconds:
                self._last_reload = current_time
                logger.info(f"Config file changed: {event_path}")
                self.on_change()


class ConfigHotReload:
    """配置热加载器"""
    
    def __init__(self, config_path: str = "config.yaml", reload_callback: Optional[Callable] = None):
        self.config_path = Path(config_path)
        self.reload_callback = reload_callback
        self._observer: Optional[Observer] = None
        self._config_state: Optional[ConfigState] = None
        self._lock = threading.RLock()
        self._last_checksum = ""
    
    def start(self):
        """启动配置监听"""
        if self._observer is not None:
            logger.warning("Config hot reload already started")
            return
        
        # 初始加载
        self.reload()
        
        # 启动文件监听
        self._observer = Observer()
        handler = ConfigFileHandler(str(self.config_path), self.reload)
        self._observer.schedule(handler, str(self.config_path.parent), recursive=False)
        self._observer.start()
        
        logger.info(f"Config hot reload started: {self.config_path}")
    
    def stop(self):
        """停止配置监听"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Config hot reload stopped")
    
    def reload(self):
        """重新加载配置"""
        with self._lock:
            try:
                # 计算新的checksum
                content = self.config_path.read_text(encoding='utf-8')
                new_checksum = hashlib.md5(content.encode()).hexdigest()
                
                # 检查是否有变化
                if new_checksum == self._last_checksum:
                    logger.debug("Config file unchanged, skipping reload")
                    return
                
                self._last_checksum = new_checksum
                
                # 重新加载配置
                from src.config import load_config
                new_config = load_config(str(self.config_path))
                
                self._config_state = ConfigState(
                    config=new_config,
                    last_modified=time.time(),
                    checksum=new_checksum
                )
                
                logger.info(f"Config reloaded successfully (checksum: {new_checksum[:8]}...)")
                
                # 调用回调函数
                if self.reload_callback:
                    self.reload_callback(new_config)
                
                return new_config
                
            except Exception as e:
                logger.error(f"Failed to reload config: {e}")
                return self._config_state.config if self._config_state else {}
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        with self._lock:
            if self._config_state:
                return self._config_state.config
            return {}


# 全局配置热加载器
_config_reloader: Optional[ConfigHotReload] = None


def start_config_reload(config_path: str = "config.yaml", callback: Optional[Callable] = None) -> ConfigHotReload:
    """启动配置热加载"""
    global _config_reloader
    _config_reloader = ConfigHotReload(config_path, callback)
    _config_reloader.start()
    return _config_reloader


def stop_config_reload():
    """停止配置热加载"""
    global _config_reloader
    if _config_reloader:
        _config_reloader.stop()
        _config_reloader = None


def get_current_config() -> Dict[str, Any]:
    """获取当前配置"""
    if _config_reloader:
        return _config_reloader.get_config()
    return {}
