"""
测试新添加的功能模块
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestValidateConfig(unittest.TestCase):
    """测试配置验证模块"""
    
    def test_validate_wechat_config(self):
        """测试微信配置验证"""
        from src.validate_config import ConfigValidator, ValidationErrorType
        
        validator = ConfigValidator()
        
        # 测试无效配置
        config = {
            "wechat": {
                "app_id": "your_app_id_here",
                "app_secret": "your_app_secret_here"
            }
        }
        errors = validator.validate_wechat_config(config)
        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[0].error_type, ValidationErrorType.REQUIRED)
        
        # 测试有效配置
        config = {
            "wechat": {
                "app_id": "wx1234567890abcdef",
                "app_secret": "abcdef1234567890"
            }
        }
        errors = validator.validate_wechat_config(config)
        self.assertEqual(len(errors), 0)
    
    def test_validate_llm_config(self):
        """测试 LLM 配置验证"""
        from src.validate_config import ConfigValidator
        
        validator = ConfigValidator()
        
        # 测试无 LLM 配置
        config = {
            "openai": {"api_key": "your_openai_api_key_here"},
            "deepseek": {"api_key": ""},
            "zhipu": {"api_key": ""}
        }
        errors = validator.validate_llm_config(config)
        self.assertTrue(any(e.field == "llm" for e in errors))
        
        # 测试有效配置
        config = {
            "openai": {"api_key": "sk-1234567890abcdef1234567890abcdef1234567890abcdef"},
            "deepseek": {"api_key": ""},
            "zhipu": {"api_key": ""}
        }
        errors = validator.validate_llm_config(config)
        self.assertFalse(any(e.field == "llm" for e in errors))


class TestProxy(unittest.TestCase):
    """测试代理支持模块"""
    
    @patch.dict(os.environ, {"HTTP_PROXY": "http://127.0.0.1:7890", "HTTPS_PROXY": "http://127.0.0.1:7890"})
    def test_proxy_config_from_env(self):
        """测试从环境变量创建代理配置"""
        from src.proxy import ProxyConfig
        
        config = ProxyConfig.from_env()
        self.assertTrue(config.enabled)
        self.assertEqual(config.http, "http://127.0.0.1:7890")
        self.assertEqual(config.https, "http://127.0.0.1:7890")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_proxy_disabled(self):
        """测试代理禁用"""
        from src.proxy import ProxyManager
        
        manager = ProxyManager()
        self.assertFalse(manager.config.enabled)
        self.assertEqual(manager.get_requests_proxy(), {})


class TestErrors(unittest.TestCase):
    """测试错误处理模块"""
    
    def test_app_error(self):
        """测试 AppError 类"""
        from src.errors import AppError, ErrorType
        
        error = AppError("测试错误", ErrorType.NETWORK)
        self.assertEqual(error.message, "测试错误")
        self.assertEqual(error.error_type, ErrorType.NETWORK)
        self.assertTrue(error.is_recoverable)
        
        # 测试重试
        error_with_retry = error.with_retry()
        self.assertEqual(error_with_retry.retry_count, 1)
    
    def test_create_app_error(self):
        """测试创建 AppError"""
        from src.errors import create_app_error, ErrorType
        
        # 测试普通异常
        error = create_app_error(ValueError("测试错误"))
        self.assertEqual(error.error_type, ErrorType.UNKNOWN)
        
        # 测试超时异常
        error = create_app_error(TimeoutError("超时"))
        self.assertEqual(error.error_type, ErrorType.TIMEOUT)


class TestMockData(unittest.TestCase):
    """测试模拟数据模块"""
    
    def test_generate_mock_news(self):
        """测试生成模拟新闻"""
        from src.mock_data import MockDataGenerator
        
        generator = MockDataGenerator(seed=42)
        news = generator.generate_news(count=5)
        
        self.assertEqual(len(news), 5)
        self.assertTrue(all(hasattr(item, "title") for item in news))
        self.assertTrue(all(hasattr(item, "url") for item in news))
    
    def test_generate_mock_article(self):
        """测试生成模拟文章"""
        from src.mock_data import MockDataGenerator
        
        generator = MockDataGenerator(seed=42)
        news = generator.generate_news(count=5)
        article = generator.generate_article(news)
        
        self.assertIn("AI 资讯日报", article)
        self.assertTrue(len(article) > 100)


class TestHealth(unittest.TestCase):
    """测试健康检查模块"""
    
    def test_health_counters(self):
        """测试健康计数器"""
        from src.health import HealthChecker
        
        checker = HealthChecker()
        
        # 测试计数器
        checker.inc_fetched(10)
        checker.inc_fetch_failure(2)
        checker.inc_aggregated(8)
        checker.inc_generated(1)
        checker.inc_published(1)
        
        metrics = checker.get_business_metrics()
        self.assertEqual(metrics["counters"]["fetched"], 10)
        self.assertEqual(metrics["counters"]["fetch_failures"], 2)
        self.assertEqual(metrics["counters"]["aggregated"], 8)
        self.assertEqual(metrics["counters"]["generated"], 1)
        self.assertEqual(metrics["counters"]["published"], 1)
    
    def test_health_status(self):
        """测试健康状态"""
        from src.health import HealthChecker
        
        checker = HealthChecker()
        
        # 测试健康状态
        self.assertTrue(checker.is_business_healthy())
        
        # 模拟高失败率（需要超过阈值）
        checker.inc_fetched(10)
        checker.inc_fetch_failure(20)  # 66% 失败率
        self.assertFalse(checker.is_business_healthy())


class TestConfigHotReload(unittest.TestCase):
    """测试配置热重载模块"""
    
    def test_config_hot_reloader(self):
        """测试配置热重载器"""
        from src.config_hotreload import ConfigHotReloader
        
        # 创建临时配置文件
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"test": "value"}, f)
            config_path = f.name
        
        try:
            reloader = ConfigHotReloader(config_path=config_path, auto_reload=False)
            config = reloader.load()
            
            self.assertEqual(config["test"], "value")
            self.assertEqual(reloader.get_value("test"), "value")
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    unittest.main()
