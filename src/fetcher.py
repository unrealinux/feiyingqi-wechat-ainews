"""
AI News Fetcher - 高性能新闻获取模块

支持多源并发获取、智能重试、缓存机制
参考 feiqingqiWechatMP 优化，集成代理支持和错误处理
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from src.config import load_config, get_news_config
from src.proxy import get_requests_proxy, is_proxy_enabled
from src.errors import with_retry, create_app_error, AppError, ErrorType
from src.health import inc_fetched, inc_fetch_failure
from src.mock_data import is_mock_mode_enabled, generate_mock_news, MockNewsItem


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class NewsItem:
    """新闻项目"""
    
    __slots__ = ['title', 'url', 'source', 'description', 'published_at', '_hash']
    
    def __init__(self, title: str, url: str, source: str = "", 
                 description: str = "", published_at: str = ""):
        self.title = title.strip() if title else ""
        self.url = url.strip() if url else ""
        self.source = source.strip() if source else ""
        self.description = description.strip()[:500] if description else ""
        self.published_at = published_at or datetime.now().strftime("%Y-%m-%d")
        self._hash = hashlib.md5(f"{self.title}{self.url}".encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "description": self.description,
            "published_at": self.published_at
        }
    
    def __repr__(self):
        return f"NewsItem(source={self.source}, title={self.title[:30]}...)"
    
    def __eq__(self, other):
        if not isinstance(other, NewsItem):
            return False
        return self._hash == other._hash
    
    def __hash__(self):
        return hash(self._hash)


class NewsFetcher:
    """新闻获取器 - 支持多源并发"""
    
    RSS_FEEDS = {
        "OpenAI Blog": "https://openai.com/blog/rss.xml",
        "36kr": "https://36kr.com/feed/",
        "量子位": "https://www.qbitai.com/feed/",
        "MIT Tech Review": "https://www.technologyreview.com/feed/",
    }
    
    AI_NEWS_SITES = [
        {"name": "量子位", "url": "https://www.qbitai.com/", "selector": "article"},
        {"name": "机器之心", "url": "https://www.jiqizhixin.com/", "selector": "article"},
    ]
    
    AI_KEYWORDS = ["AI", "GPT", "LLM", "machine learning", "deep learning", 
                   "OpenAI", "Google", "Meta", "Anthropic", "Claude", "Gemini", 
                   "模型", "人工智能", "大模型"]
    
    def __init__(self):
        self.config = load_config()
        self.news_config = get_news_config(self.config)
        self.max_workers = 10
        self.timeout = 8
        self.max_retries = 2
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # 代理配置
        self.proxies = get_requests_proxy()
        self.use_proxy = is_proxy_enabled()
        
        # 模拟数据模式
        self.use_mock = is_mock_mode_enabled()
        if self.use_mock:
            logger.info("模拟数据模式已启用")
        
        # 健康监控
        self._health_checker = None
        try:
            import src.health as health_module
            self._health_checker = health_module.get_health_checker()
        except (ImportError, AttributeError):
            pass
    
    def fetch_all(self) -> List[NewsItem]:
        """获取所有新闻源"""
        start_time = time.time()
        max_news = self.news_config.get("max_news", 15)
        exclude_keywords = self.news_config.get("exclude_keywords", [])
        sources = self.news_config.get("sources", {})
        
        # 检查模拟数据模式
        if self.use_mock:
            logger.info("使用模拟数据模式...")
            mock_items = generate_mock_news(count=max_news)
            # 转换为 NewsItem 格式
            all_news = [
                NewsItem(
                    title=item.title,
                    url=item.url,
                    source=item.source,
                    description=item.description,
                    published_at=item.published_at
                )
                for item in mock_items
            ]
            
            # 更新健康监控
            if self._health_checker:
                self._health_checker.inc_fetched(len(all_news))
            
            elapsed = time.time() - start_time
            logger.info("="*50)
            logger.info(f"模拟数据完成：{len(all_news)} 条新闻 | 耗时：{elapsed:.1f}s")
            logger.info("="*50)
            
            return all_news
        
        all_news: List[NewsItem] = []
        tasks = []
        
        logger.info("\n" + "="*50)
        logger.info("开始获取新闻")
        logger.info("="*50)
        
        if sources.get("search", True):
            keywords = self.news_config.get("search_keywords", [])
            for kw in keywords:
                tasks.append(("search", kw, max_news))
        
        if sources.get("rss", False):
            for name, url in self.RSS_FEEDS.items():
                tasks.append(("rss", name, url))
        
        if sources.get("hackernews", False):
            tasks.append(("hackernews", None, None))
        
        if sources.get("websites", False):
            for site in self.AI_NEWS_SITES:
                tasks.append(("website", site["name"], site))
        
        logger.info(f"共 {len(tasks)} 个获取任务")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {}
            
            for task in tasks:
                task_type, param1, param2 = task
                if task_type == "search":
                    future = executor.submit(self._search_with_retry, param1, param2)
                elif task_type == "rss":
                    future = executor.submit(self._fetch_rss_with_retry, param1, param2)
                elif task_type == "hackernews":
                    future = executor.submit(self._fetch_hackernews_with_retry)
                elif task_type == "website":
                    future = executor.submit(self._fetch_website_with_retry, param1)
                else:
                    continue
                future_to_task[future] = task
            
            for future in as_completed(future_to_task, timeout=self.timeout * 2):
                task_type, param1, _ = future_to_task[future]
                try:
                    results = future.result()
                    if results:
                        for item in results:
                            if item.title and self._should_include(item, exclude_keywords):
                                all_news.append(item)
                        logger.info(f"  ✓ {task_type}: +{len(results)} 条")
                        
                        # 更新健康监控
                        if self._health_checker:
                            self._health_checker.inc_fetched(len(results))
                except Exception as e:
                    logger.debug(f"  ✗ {task_type}: {str(e)[:50]}")
                    
                    # 更新健康监控
                    if self._health_checker:
                        self._health_checker.inc_fetch_failure(1)
        
        all_news = self._deduplicate(all_news)
        all_news = self._filter_by_date(all_news, days=7)
        all_news = all_news[:max_news]
        
        elapsed = time.time() - start_time
        logger.info("="*50)
        logger.info(f"完成：{len(all_news)} 条新闻 | 耗时：{elapsed:.1f}s")
        logger.info("="*50)
        
        return all_news
    
    def _search_with_retry(self, keyword: str, max_results: int) -> List[NewsItem]:
        return self._retry(self._search_news, keyword, max_results)
    
    def _fetch_rss_with_retry(self, name: str, url: str) -> List[NewsItem]:
        return self._retry(self._fetch_rss, name, url)
    
    def _fetch_hackernews_with_retry(self) -> List[NewsItem]:
        return self._retry(self._fetch_hackernews)
    
    def _fetch_website_with_retry(self, name: str) -> List[NewsItem]:
        return self._retry(self._fetch_website, name)
    
    def _retry(self, func, *args, **kwargs) -> List[NewsItem]:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))
        logger.debug(f"Retry failed: {func.__name__}: {last_error}")
        return []
    
    def _search_news(self, keyword: str, max_results: int) -> List[NewsItem]:
        try:
            exa_api_key = os.environ.get("EXA_API_KEY", "")
            if exa_api_key:
                from exa_py import Exa
                exa = Exa(api_key=exa_api_key)
                results = exa.search(
                    query=keyword,
                    num_results=max_results,
                    type="auto",
                    start_published_date=datetime.now().strftime("%Y-%m-%d")
                )
                return [NewsItem(
                    title=r.title, url=r.url, source=r.domain,
                    description=(r.text or "")[:200]
                ) for r in results.results if r.title]
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Exa search failed: {e}")
        
        return []
    
    def _fetch_rss(self, name: str, url: str) -> List[NewsItem]:
        import feedparser
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:3]:
            title = entry.get("title", "")
            if title:
                results.append(NewsItem(
                    title=title,
                    url=entry.get("link", ""),
                    source=name,
                    description=(entry.get("summary", "") or "")[:200],
                    published_at=self._parse_date(entry.get("published", ""))
                ))
        return results
    
    def _fetch_hackernews(self) -> List[NewsItem]:
        import requests
        response = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=self.timeout
        )
        story_ids = response.json()[:10]
        
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._fetch_hn_story, sid): sid 
                for sid in story_ids
            }
            for future in as_completed(futures):
                try:
                    story = future.result()
                    if story:
                        results.append(story)
                except:
                    pass
        return results
    
    def _fetch_hn_story(self, story_id: int) -> Optional[NewsItem]:
        import requests
        url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        response = requests.get(url, timeout=self.timeout)
        story = response.json()
        
        if not story or story.get("type") != "story":
            return None
        
        title = story.get("title", "")
        if not any(kw.lower() in title.lower() for kw in self.AI_KEYWORDS):
            return None
        
        return NewsItem(
            title=title,
            url=story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            source="HackerNews",
            description=f"Score: {story.get('score', 0)}"
        )
    
    def _fetch_website(self, name: str) -> List[NewsItem]:
        site = next((s for s in self.AI_NEWS_SITES if s["name"] == name), None)
        if not site:
            return []
        
        import requests
        from bs4 import BeautifulSoup
        
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        response = requests.get(site["url"], headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.select(site["selector"])[:5]
        
        results = []
        for article in articles:
            title_elem = article.find("a") or article.find("h2") or article.find("h3")
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            if len(title) < 10:
                continue
            
            link = title_elem.get("href", "")
            if link and not link.startswith("http"):
                link = site["url"] + link
            
            results.append(NewsItem(
                title=title, url=link or site["url"], source=name
            ))
        
        return results
    
    def _should_include(self, item: NewsItem, exclude_keywords: List[str]) -> bool:
        text = f"{item.title} {item.description}".lower()
        for kw in exclude_keywords:
            if kw.lower() in text:
                return False
        return bool(item.title and len(item.title) > 5)
    
    def _deduplicate(self, news: List[NewsItem]) -> List[NewsItem]:
        seen = set()
        unique = []
        for item in news:
            if item._hash not in seen:
                seen.add(item._hash)
                unique.append(item)
        return unique
    
    def _filter_by_date(self, news: List[NewsItem], days: int = 7) -> List[NewsItem]:
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        for item in news:
            try:
                item_date = datetime.strptime(item.published_at, "%Y-%m-%d")
                if item_date >= cutoff:
                    filtered.append(item)
            except:
                filtered.append(item)
        return filtered
    
    def _parse_date(self, date_str: str) -> str:
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")


def fetch_news() -> List[NewsItem]:
    """获取新闻的便捷函数"""
    fetcher = NewsFetcher()
    return fetcher.fetch_all()


def get_mock_news(count: int = 5) -> List[NewsItem]:
    """模拟数据（兜底）"""
    today = datetime.now().strftime("%Y-%m-%d")
    mock_data = [
        NewsItem("OpenAI 发布最新 GPT-5 模型，性能大幅提升", 
                 "https://openai.com/blog/gpt-5", "OpenAI", 
                 "OpenAI 宣布推出 GPT-5，新模型在推理能力和多模态理解方面有显著突破", today),
        NewsItem("Google DeepMind 发布 AlphaFold 3，预测精度再创新高", 
                 "https://deepmind.google/blog/alphafold-3", "Google DeepMind", 
                 "DeepMind 最新蛋白质结构预测模型，能够预测蛋白质与其他分子的相互作用", today),
        NewsItem("微软推出 Copilot+ PC，AI 功能全面集成 Windows", 
                 "https://microsoft.com/copilot", "Microsoft", 
                 "微软发布新一代 PC 架构，AI 能力深度集成到操作系统层面", today),
        NewsItem("Anthropic 发布 Claude 4，主打安全性和可控性", 
                 "https://anthropic.com/claude-4", "Anthropic", 
                 "Claude 4 在安全对齐方面取得重大进展，同时保持强大的推理能力", today),
        NewsItem("Meta 开源 Llama 4，性能超越闭源模型", 
                 "https://meta.com/llama", "Meta", 
                 "Meta 发布 Llama 4 系列模型，参数规模和创新架构引发业界关注", today),
    ]
    return mock_data[:count]


if __name__ == "__main__":
    news = fetch_news()
    print(f"\n获取 {len(news)} 条新闻:")
    for item in news[:10]:
        print(f"  - [{item.source}] {item.title[:50]}...")
