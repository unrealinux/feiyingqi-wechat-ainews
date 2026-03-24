import os
import yaml
from pathlib import Path


def load_config(config_path: str = "config.yaml") -> dict:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config


def get_wechat_config(config: dict) -> dict:
    return config.get("wechat", {})


def get_openai_config(config: dict) -> dict:
    return config.get("openai", {})


def get_news_config(config: dict) -> dict:
    return config.get("news", {})


def get_publish_config(config: dict) -> dict:
    return config.get("publish", {})


def get_scheduler_config(config: dict) -> dict:
    return config.get("scheduler", {})


def get_llm_config(config: dict) -> dict:
    """获取LLM配置"""
    return config.get("llm", {})


def get_deepseek_config(config: dict) -> dict:
    """获取DeepSeek配置"""
    return config.get("deepseek", {})


def get_zhipu_config(config: dict) -> dict:
    """获取智谱AI配置"""
    return config.get("zhipu", {})


def get_siliconflow_config(config: dict) -> dict:
    """获取SiliconFlow配置"""
    return config.get("siliconflow", {})
