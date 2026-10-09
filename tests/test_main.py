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
    """测试 Scheduler 模块

    重要：绝不能直接调 run_once()。它会抓新闻、调 LLM、出封面，最后
    一路走到 create_draft()—— 那是真实写线上草稿箱的写操作。
    历史上这个用例就是那么写的，导致每跑一次 pytest 就往草稿箱塞一篇真实草稿。
    这里改为把流水线的外部边界（抓取/LLM/渲染/发布）全部 mock 掉，
    只验证 run_once 自身的契约：返回 bool、不抛异常、且真的调用了发布。
    """

    def test_run_once_returns_bool_without_touching_wechat(self):
        from unittest.mock import patch, MagicMock
        from src.scheduler import run_once

        with patch("src.fetcher.fetch_news", return_value=[MagicMock()]) as m_fetch, \
             patch("src.summarizer.Summarizer.generate_editorial_spec",
                   return_value={"title": "单元测试标题"}) as m_llm, \
             patch("src.editorial_template.draft_title", return_value="单元测试标题"), \
             patch("src.editorial_template.render", return_value="<p>正文</p>"), \
             patch("src.ai_photo_cover.generate_ai_photo_cover", return_value=(None, None)), \
             patch("src.cover_generator.generate_gradient_cover", return_value=None), \
             patch("src.publisher.publish_article", return_value=True) as m_publish:
            result = run_once()

        self.assertIsInstance(result, bool)
        self.assertTrue(result)
        self.assertTrue(m_fetch.called, "应当抓取新闻")
        self.assertTrue(m_llm.called, "应当调用 LLM 产出结构化内容")
        self.assertTrue(m_publish.called, "应当走到发布步骤")
        # 发布层已被 mock，真实草稿不可能被创建
        self.assertEqual(
            m_publish.call_args.kwargs.get("auto_publish"),
            False,
            "必须只建草稿（auto_publish=False），绝不群发",
        )

    def test_run_once_fails_closed_when_llm_unavailable(self):
        """LLM 不可用时必须 fail-closed 返回 False，而不是塞一篇 mock 稿。"""
        from unittest.mock import patch, MagicMock
        from src.scheduler import run_once
        from src.summarizer import LLMUnavailableError

        with patch("src.fetcher.fetch_news", return_value=[MagicMock()]), \
             patch("src.summarizer.Summarizer.generate_editorial_spec",
                   side_effect=LLMUnavailableError("no llm")), \
             patch("src.publisher.publish_article") as m_publish:
            result = run_once()

        self.assertFalse(result)
        self.assertFalse(m_publish.called, "LLM 不可用时不得进入发布步骤")

    def test_run_once_notifies_when_nothing_gets_published(self):
        """AI 味门禁/LLM 失败导致当天没稿时必须发告警，不能只写日志。"""
        from unittest.mock import patch, MagicMock
        from src.scheduler import run_once
        from src.summarizer import LLMUnavailableError

        with patch("src.fetcher.fetch_news", return_value=[MagicMock()]), \
             patch("src.summarizer.Summarizer.generate_editorial_spec",
                   side_effect=LLMUnavailableError("AI 味过重（56.0 >= 45.0）")), \
             patch("src.publisher.publish_article") as m_publish, \
             patch("src.monitoring.send_run_notification") as m_notify:
            result = run_once()

        self.assertFalse(result)
        self.assertFalse(m_publish.called)
        m_notify.assert_called_once()
        status, details = m_notify.call_args.args
        self.assertEqual(status, "error")
        self.assertIn("AI 味", details["error"])

    def test_run_once_refetches_when_material_is_too_thin(self):
        """素材太薄时应该补抓素材重试一次，而不是把同一份素材反复重写。"""
        from unittest.mock import patch, MagicMock
        from src.scheduler import run_once
        from src.summarizer import ThinMaterialError

        def _first_thin_then_ok(_items, **_kw):
            if _first_thin_then_ok.calls == 0:
                _first_thin_then_ok.calls += 1
                raise ThinMaterialError("两稿都被判 AI 味过重")
            return {"title": "重试成功的标题"}

        _first_thin_then_ok.calls = 0
        extra_item = MagicMock()

        with patch("src.fetcher.fetch_news", return_value=[extra_item]) as m_fetch, \
             patch("src.summarizer.Summarizer.generate_editorial_spec",
                   side_effect=_first_thin_then_ok) as m_llm, \
             patch("src.editorial_template.draft_title", return_value="单元测试标题"), \
             patch("src.editorial_template.render", return_value="<p>正文</p>"), \
             patch("src.ai_photo_cover.generate_ai_photo_cover", return_value=(None, None)), \
             patch("src.cover_generator.generate_gradient_cover", return_value=None), \
             patch("src.publisher.publish_article", return_value=True) as m_publish:
            result = run_once()

        self.assertTrue(result)
        self.assertEqual(m_llm.call_count, 2, "素材太薄应重试一次")
        self.assertGreaterEqual(m_fetch.call_count, 2, "重试前应补抓素材")
        self.assertTrue(m_publish.called)

    def test_refetch_more_merges_without_dropping_original(self):
        """补抓只增不减，且按 URL 去重；补抓失败不能把原有素材弄丢。"""
        from unittest.mock import patch
        from src.scheduler import _refetch_more
        from src.fetcher import NewsItem

        original = [NewsItem("旧闻", "https://a.com")]

        with patch("src.fetcher.fetch_news",
                   return_value=[NewsItem("旧闻", "https://a.com"),
                                 NewsItem("新出现", "https://b.com")]):
            merged = _refetch_more(original)
        self.assertEqual([i.url for i in merged], ["https://a.com", "https://b.com"])

        with patch("src.fetcher.fetch_news", side_effect=RuntimeError("断网")):
            self.assertEqual(_refetch_more(original)[0].url, "https://a.com")


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
