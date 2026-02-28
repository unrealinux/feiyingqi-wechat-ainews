"""
Unit Tests for AI News Publisher

运行测试：
python -m pytest tests/ -v
"""

import pytest
import unittest
from datetime import datetime
from pathlib import Path


class TestNewsItem(unittest.TestCase):
    """测试 NewsItem 类"""
    
    def test_create_news_item(self):
        from src.fetcher import NewsItem
        
        item = NewsItem(
            title="Test Title",
            url="https://example.com",
            source="Test Source",
            description="Test description"
        )
        
        self.assertEqual(item.title, "Test Title")
        self.assertEqual(item.url, "https://example.com")
        self.assertEqual(item.source, "Test Source")
    
    def test_news_item_hash(self):
        from src.fetcher import NewsItem
        
        item1 = NewsItem("Title", "https://example.com")
        item2 = NewsItem("Title", "https://example.com")
        item3 = NewsItem("Different Title", "https://example.com")
        
        self.assertEqual(item1, item2)
        self.assertNotEqual(item1, item3)
    
    def test_news_item_to_dict(self):
        from src.fetcher import NewsItem
        
        item = NewsItem("Title", "https://example.com", "Source", "Desc")
        data = item.to_dict()
        
        self.assertEqual(data["title"], "Title")
        self.assertEqual(data["url"], "https://example.com")
        self.assertEqual(data["source"], "Source")


class TestSummarizer(unittest.TestCase):
    """测试 Summarizer 类"""
    
    def test_mock_summarize(self):
        from src.summarizer import Summarizer
        from src.fetcher import NewsItem
        
        summarizer = Summarizer()
        news_items = [
            NewsItem("Test News", "https://example.com", "Test")
        ]
        
        article = summarizer._mock_summarize(news_items)
        
        self.assertIn("AI 资讯日报", article)
        self.assertIsInstance(article, str)
        self.assertTrue(len(article) > 100)


class TestPublisher(unittest.TestCase):
    """测试 Publisher 类"""
    
    def test_markdown_to_html(self):
        from src.publisher import WeChatPublisher
        
        publisher = WeChatPublisher()
        
        markdown = """# Title

## Section

**Bold text**

> Quote
"""
        
        html = publisher.markdown_to_html(markdown)
        
        self.assertIn("<h1", html)
        self.assertIn("<h2", html)
        self.assertIn("<strong", html)
        self.assertIn("<blockquote", html)


class TestConfig(unittest.TestCase):
    """测试配置加载"""
    
    def test_load_config(self):
        from src.config import load_config
        
        config = load_config()
        
        self.assertIn("wechat", config)
        self.assertIn("openai", config)
        self.assertIn("news", config)
    
    def test_get_news_config(self):
        from src.config import load_config, get_news_config
        
        config = load_config()
        news_config = get_news_config(config)
        
        self.assertIn("search_keywords", news_config)
        self.assertIn("max_news", news_config)


class TestScheduler(unittest.TestCase):
    """测试 Scheduler 模块"""
    
    def test_run_once_returns_bool(self):
        from src.scheduler import run_once
        
        result = run_once()
        
        self.assertIsInstance(result, bool)


class TestDeduplication(unittest.TestCase):
    """测试去重功能"""
    
    def test_deduplicate_news(self):
        from src.fetcher import NewsItem, NewsFetcher
        
        fetcher = NewsFetcher()
        
        items = [
            NewsItem("Same Title", "https://a.com"),
            NewsItem("Same Title", "https://a.com"),
            NewsItem("Different Title", "https://b.com"),
        ]
        
        unique = fetcher._deduplicate(items)
        
        self.assertEqual(len(unique), 2)


class TestDateFilter(unittest.TestCase):
    """测试日期过滤"""
    
    def test_filter_recent_news(self):
        from src.fetcher import NewsItem, NewsFetcher
        from datetime import datetime, timedelta
        
        fetcher = NewsFetcher()
        
        today = datetime.now().strftime("%Y-%m-%d")
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        
        items = [
            NewsItem("Recent", "https://a.com", published_at=today),
            NewsItem("Old", "https://b.com", published_at=old_date),
        ]
        
        filtered = fetcher._filter_by_date(items, days=7)
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].title, "Recent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
