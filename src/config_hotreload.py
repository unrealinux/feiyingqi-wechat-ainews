"""
Config Hot Reload Module - 配置热重载模块

参考 feiqingqiWechatMP 的 config-hotreload.js 实现
监听配置文件变化，自动重新加载
"""
import os
import time
import yaml
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

from src.logger import get_logger


logger = get_logger(__name__)


@dataclass
class ReloadEvent:
    """重载事件"""
    config: Dict[str, Any]
    count: int
    timestamp: datetime
    file_path: str


class ConfigHotReloader:
    """配置热重载器"""
    
    def __init__(
        self,
        config_path: str = "config.yaml",
        watch_paths: Optional[List[str]] = None,
        debounce_seconds: float = 1.0,
        auto_reload: bool = True
    ):
        """
        初始化配置热重载器
        
        Args:
            config_path: 配置文件路径
            watch_paths: 需要监听的文件路径列表
            debounce_seconds: 防抖时间（秒）
            auto_reload: 是否自动重载
        """
        self.config_path = config_path
        self.watch_paths = watch_paths or [config_path, ".env"]
        self.debounce_seconds = debounce_seconds
        self.auto_reload = auto_reload
        
        self._config: Optional[Dict[str, Any]] = None
        self._load_count = 0
        self._watchers: Dict[str, threading.Thread] = {}
        self._debounce_timers: Dict[str, threading.Timer] = {}
        self._stop_event = threading.Event()
        self._callbacks: List[Callable[[ReloadEvent], None]] = []
        self._file_mtimes: Dict[str, float] = {}
    
    def load(self) -> Dict[str, Any]:
        """
        加载配置
        
        Returns:
            配置字典
        """
        try:
            # 读取配置文件
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            # 合并环境变量
            config = self._merge_env_vars(config)
            
            self._config = config
            self._load_count += 1
            
            # 触发回调
            event = ReloadEvent(
                config=config,
                count=self._load_count,
                timestamp=datetime.now(),
                file_path=self.config_path
            )
            self._notify_callbacks(event)
            
            logger.info(f"配置已重新加载 ({self._load_count}次)")
            return config
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            # 返回上一次有效的配置
            return self._config or {}
    
    def _merge_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """合并环境变量到配置"""
        # 微信配置
        if "wechat" not in config:
            config["wechat"] = {}
        
        if os.environ.get("WECHAT_APPID"):
            config["wechat"]["app_id"] = os.environ["WECHAT_APPID"]
        if os.environ.get("WECHAT_SECRET"):
            config["wechat"]["app_secret"] = os.environ["WECHAT_SECRET"]
        
        # OpenAI 配置
        if "openai" not in config:
            config["openai"] = {}
        
        if os.environ.get("OPENAI_API_KEY"):
            config["openai"]["api_key"] = os.environ["OPENAI_API_KEY"]
        if os.environ.get("OPENAI_MODEL"):
            config["openai"]["model"] = os.environ["OPENAI_MODEL"]
        
        # DeepSeek 配置
        if "deepseek" not in config:
            config["deepseek"] = {}
        
        if os.environ.get("DEEPSEEK_API_KEY"):
            config["deepseek"]["api_key"] = os.environ["DEEPSEEK_API_KEY"]
        if os.environ.get("DEEPSEEK_MODEL"):
            config["deepseek"]["model"] = os.environ["DEEPSEEK_MODEL"]
        
        # 智谱AI 配置
        if "zhipu" not in config:
            config["zhipu"] = {}
        
        if os.environ.get("ZHIPU_API_KEY"):
            config["zhipu"]["api_key"] = os.environ["ZHIPU_API_KEY"]
        if os.environ.get("ZHIPU_MODEL"):
            config["zhipu"]["model"] = os.environ["ZHIPU_MODEL"]
        
        return config
    
    def get(self) -> Optional[Dict[str, Any]]:
        """获取配置"""
        return self._config
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            path: 配置路径，使用点号分隔（如 "wechat.app_id"）
            default: 默认值
            
        Returns:
            配置值
        """
        if not self._config:
            return default
        
        keys = path.split(".")
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def watch(self):
        """开始监听文件变化"""
        if not self.auto_reload:
            logger.info("自动重载已禁用")
            return
        
        self._stop_event.clear()
        
        for file_path in self.watch_paths:
            if os.path.exists(file_path):
                self._watch_file(file_path)
        
        logger.info(f"已监听 {len(self._watch_paths)} 个配置文件")
    
    def _watch_file(self, file_path: str):
        """监听单个文件"""
        # 记录初始修改时间
        self._file_mtimes[file_path] = self._get_mtime(file_path)
        
        def watcher():
            while not self._stop_event.is_set():
                try:
                    current_mtime = self._get_mtime(file_path)
                    last_mtime = self._file_mtimes.get(file_path, 0)
                    
                    if current_mtime > last_mtime:
                        self._file_mtimes[file_path] = current_mtime
                        self._on_file_changed(file_path)
                    
                    time.sleep(1)  # 每秒检查一次
                except Exception as e:
                    logger.error(f"监听文件 {file_path} 失败: {e}")
                    time.sleep(5)
        
        thread = threading.Thread(target=watcher, daemon=True, name=f"watcher-{file_path}")
        thread.start()
        self._watchers[file_path] = thread
    
    def _get_mtime(self, file_path: str) -> float:
        """获取文件修改时间"""
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0
    
    def _on_file_changed(self, file_path: str):
        """文件变化处理"""
        logger.info(f"检测到文件变化: {file_path}")
        
        # 防抖处理
        if file_path in self._debounce_timers:
            self._debounce_timers[file_path].cancel()
        
        timer = threading.Timer(
            self.debounce_seconds,
            lambda: self._reload_config(file_path)
        )
        timer.start()
        self._debounce_timers[file_path] = timer
    
    def _reload_config(self, file_path: str):
        """重新加载配置"""
        try:
            logger.info(f"重新加载配置: {file_path}")
            self.load()
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
    
    def stop(self):
        """停止监听"""
        self._stop_event.set()
        
        # 取消所有防抖定时器
        for timer in self._debounce_timers.values():
            timer.cancel()
        
        self._debounce_timers.clear()
        self._watchers.clear()
        
        logger.info("配置监听已停止")
    
    def on_reload(self, callback: Callable[[ReloadEvent], None]):
        """
        注册重载回调
        
        Args:
            callback: 回调函数，接收 ReloadEvent 参数
        """
        self._callbacks.append(callback)
    
    def _notify_callbacks(self, event: ReloadEvent):
        """通知所有回调"""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")


# 全局配置热重载器
_hot_reloader: Optional[ConfigHotReloader] = None


def get_hot_reloader(
    config_path: str = "config.yaml",
    auto_reload: bool = True
) -> ConfigHotReloader:
    """获取全局配置热重载器"""
    global _hot_reloader
    if _hot_reloader is None:
        _hot_reloader = ConfigHotReloader(
            config_path=config_path,
            auto_reload=auto_reload
        )
    return _hot_reloader


def load_config() -> Dict[str, Any]:
    """加载配置的便捷函数"""
    return get_hot_reloader().load()


def get_config() -> Optional[Dict[str, Any]]:
    """获取配置的便捷函数"""
    return get_hot_reloader().get()


def get_config_value(path: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return get_hot_reloader().get_value(path, default)


def start_watching():
    """开始监听配置变化"""
    get_hot_reloader().watch()


def stop_watching():
    """停止监听配置变化"""
    get_hot_reloader().stop()


def on_config_reload(callback: Callable[[ReloadEvent], None]):
    """注册配置重载回调"""
    get_hot_reloader().on_reload(callback)


if __name__ == "__main__":
    # 测试代码
    def on_reload(event: ReloadEvent):
        print(f"配置已重载: {event.count}次, 文件: {event.file_path}")
    
    reloader = ConfigHotReloader()
    reloader.on_reload(on_reload)
    
    # 加载配置
    config = reloader.load()
    print(f"当前配置: {list(config.keys())}")
    
    # 获取特定值
    wechat_app_id = reloader.get_value("wechat.app_id", "未配置")
    print(f"微信 AppID: {wechat_app_id}")
    
    # 开始监听
    print("\n开始监听配置变化（按 Ctrl+C 停止）...")
    reloader.watch()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监听...")
        reloader.stop()
