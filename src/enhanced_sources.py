"""
Enhanced News Sources - 增强版新闻源
新增更多国内新闻源和改进的抓取策略
"""
import re
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, quote

from src.logger import get_logger


logger = get_logger(__name__)


@dataclass
class NewsSource:
    """新闻源配置"""
    name: str
    url: str
    selector: Optional[str] = None
    title_selector: Optional[str] = None
    link_selector: Optional[str] = None
    desc_selector: Optional[str] = None
    date_selector: Optional[str] = None
    category: str = "general"
    language: str = "zh"
    requires_proxy: bool = False
    rate_limit: float = 1.0  # 请求间隔(秒)


class EnhancedNewsSources:
    """增强版新闻源管理器"""
    
    # 中文科技新闻源
    ZH_SOURCES = [
        NewsSource(
            name="知乎-科技",
            url="https://www.zhihu.com/topic/19550517/hot",
            selector=".List-item",
            title_selector=".ContentItem-title",
            link_selector="a.ContentItem-title",
            category="tech",
            rate_limit=2.0
        ),
        NewsSource(
            name="36kr-AI",
            url="https://www.36kr.com/information/AI/",
            selector=".article-item",
            title_selector=".article-title",
            link_selector="a",
            category="ai",
            rate_limit=1.5
        ),
        NewsSource(
            name="量子位",
            url="https://www.qbitai.com/",
            selector="article",
            title_selector="h2 a",
            category="ai",
            rate_limit=1.0
        ),
        NewsSource(
            name="机器之心",
            url="https://www.jiqizhixin.com/",
            selector="article",
            title_selector="h3 a",
            category="ai",
            rate_limit=1.0
        ),
        NewsSource(
            name="虎嗅",
            url="https://www.huxiu.com/",
            selector=".article-item",
            title_selector="h3 a",
            category="tech",
            rate_limit=1.5
        ),
        NewsSource(
            name="极客公园",
            url="https://www.geekpark.com/news",
            selector=".news-item",
            title_selector="h3 a",
            category="tech",
            rate_limit=1.0
        ),
        NewsSource(
            name="爱范儿",
            url="https://www.ifanr.com/",
            selector="article",
            title_selector="h2 a",
            category="tech",
            rate_limit=1.0
        ),
        NewsSource(
            name="少数派",
            url="https://sspai.com/",
            selector=".article-item",
            title_selector="h2 a",
            category="tech",
            rate_limit=1.0
        ),
        NewsSource(
            name="品玩",
            url="https://www.pingwest.com/",
            selector="article",
            title_selector="h3 a",
            category="tech",
            rate_limit=1.0
        ),
        NewsSource(
            name="钛媒体",
            url="https://www.tmtpost.com/",
            selector="article",
            title_selector="h2 a",
            category="tech",
            rate_limit=1.5
        ),
        NewsSource(
            name="雷峰网",
            url="https://www.leiphone.com/",
            selector="article",
            title_selector="h3 a",
            category="ai",
            rate_limit=1.0
        ),
        NewsSource(
            name="新智元",
            url="https://xinyaoyuan.com/",
            selector="article",
            title_selector="h2 a",
            category="ai",
            rate_limit=1.0
        ),
    ]
    
    # 英文AI新闻源
    EN_SOURCES = [
        NewsSource(
            name="HackerNews-AI",
            url="https://hn.algolia.com/?query=AI&tags=story",
            selector=".item-title",
            title_selector="a",
            category="ai",
            language="en",
            rate_limit=1.0
        ),
        NewsSource(
            name="TechCrunch-AI",
            url="https://techcrunch.com/category/artificial-intelligence/",
            selector="article",
            title_selector="h2 a",
            category="ai",
            language="en",
            rate_limit=2.0
        ),
        NewsSource(
            name="VentureBeat-AI",
            url="https://venturebeat.com/ai/",
            selector="article",
            title_selector="h2 a",
            category="ai",
            language="en",
            rate_limit=1.5
        ),
        NewsSource(
            name="MIT Technology Review-AI",
            url="https://www.technologyreview.com/feed/",
            selector="item",
            title_selector="title",
            category="ai",
            language="en",
            rate_limit=1.0
        ),
        NewsSource(
            name="Wired-AI",
            url="https://www.wired.com/tag/artificial-intelligence/",
            selector="article",
            title_selector="h2 a",
            category="ai",
            language="en",
            rate_limit=2.0
        ),
    ]
    
    # AI公司官方博客
    OFFICIAL_BLOGS = [
        NewsSource(name="OpenAI Blog", url="https://openai.com/blog/rss.xml", category="official", language="en"),
        NewsSource(name="DeepSeek Blog", url="https://www.deepseek.com/blog", category="official", language="en"),
        NewsSource(name="Anthropic Blog", url="https://www.anthropic.com/blog", category="official", language="en"),
        NewsSource(name="Google AI Blog", url="https://blog.google/technology/ai/", category="official", language="en"),
        NewsSource(name="Meta AI Blog", url="https://ai.meta.com/blog/", category="official", language="en"),
        NewsSource(name="Microsoft AI Blog", url="https://blogs.microsoft.com/ai/", category="official", language="en"),
        NewsSource(name="NVIDIA AI", url="https://blogs.nvidia.com/ai/", category="official", language="en"),
        NewsSource(name="Stability AI", url="https://stability.ai/blog", category="official", language="en"),
    ]
    
    def __init__(self, language: str = "zh"):
        self.language = language
        self._sources = self._load_sources()
    
    def _load_sources(self) -> List[NewsSource]:
        """加载新闻源"""
        if self.language == "zh":
            return self.ZH_SOURCES + self.OFFICIAL_BLOGS
        elif self.language == "en":
            return self.EN_SOURCES + self.OFFICIAL_BLOGS
        else:
            return self.ZH_SOURCES + self.EN_SOURCES + self.OFFICIAL_BLOGS
    
    def get_sources(self, category: Optional[str] = None) -> List[NewsSource]:
        """获取新闻源列表
        
        Args:
            category: 分类过滤
        
        Returns:
            新闻源列表
        """
        if category:
            return [s for s in self._sources if s.category == category]
        return self._sources
    
    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(set(s.category for s in self._sources))
    
    def add_source(self, source: NewsSource):
        """添加自定义新闻源"""
        self._sources.append(source)
        logger.info(f"Added news source: {source.name}")
    
    def remove_source(self, name: str) -> bool:
        """移除新闻源"""
        for i, s in enumerate(self._sources):
            if s.name == name:
                self._sources.pop(i)
                logger.info(f"Removed news source: {name}")
                return True
        return False


class ContentFilter:
    """内容过滤器 - 过滤低质量/重复内容"""
    
    # 过滤关键词
    FILTER_KEYWORDS = [
        "广告", "推广", "招聘", "兼职", "转让", "出售",
        "拼多多", "抖音", "快手", "小红书", "带货",
        "彩票", "赌博", "色情", "低俗",
        "ad:", "advertisement", "sponsored"
    ]
    
    # 标题过滤模式
    FILTER_PATTERNS = [
        r"^【.*】.*招聘",  # 招聘广告
        r"^【.*】.*转让",  # 转让广告
        r"^今日招聘",
        r"^急招",
        r".*联系我.*",
        r".*二维码.*",
    ]
    
    # 最小/最大标题长度
    MIN_TITLE_LENGTH = 8
    MAX_TITLE_LENGTH = 100
    
    # 最小描述长度
    MIN_DESC_LENGTH = 20
    
    @classmethod
    def is_valid_title(cls, title: str) -> bool:
        """验证标题是否有效"""
        if not title:
            return False
        
        title = title.strip()
        length = len(title)
        
        # 长度检查
        if length < cls.MIN_TITLE_LENGTH or length > cls.MAX_TITLE_LENGTH:
            return False
        
        # 关键词过滤
        for keyword in cls.FILTER_KEYWORDS:
            if keyword.lower() in title.lower():
                return False
        
        # 模式过滤
        for pattern in cls.FILTER_PATTERNS:
            if re.search(pattern, title):
                return False
        
        return True
    
    @classmethod
    def is_valid_description(cls, desc: str) -> bool:
        """验证描述是否有效"""
        if not desc:
            return True  # 描述可以为空
        
        # 长度检查
        if len(desc.strip()) < cls.MIN_DESC_LENGTH:
            return False
        
        # 关键词过滤
        for keyword in cls.FILTER_KEYWORDS:
            if keyword.lower() in desc.lower():
                return False
        
        return True
    
    @classmethod
    def clean_text(cls, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符
        text = text.replace('\u200b', '')  # 零宽空格
        text = text.replace('\ufeff', '')   # BOM
        
        return text.strip()


class Deduplicator:
    """新闻去重器"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self._seen_hashes: set = set()
        self._seen_titles: List[str] = []
    
    def is_duplicate(self, title: str, url: str = "") -> bool:
        """检查是否重复
        
        Args:
            title: 新闻标题
            url: 新闻链接
        
        Returns:
            是否重复
        """
        # URL精确匹配
        if url:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self._seen_hashes:
                return True
        
        # 标题精确匹配
        title = title.strip()
        if title in self._seen_titles:
            return True
        
        # 标题相似度匹配
        title_lower = title.lower()
        for seen_title in self._seen_titles:
            if self._calculate_similarity(title_lower, seen_title.lower()) >= self.similarity_threshold:
                return True
        
        # 添加到已见列表
        if url:
            self._seen_hashes.add(url_hash)
        self._seen_titles.append(title)
        
        return False
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度 (Jaccard系数)"""
        if not s1 or not s2:
            return 0.0
        
        # 字符级n-gram
        def get_ngrams(s: str, n: int = 3) -> set:
            return set(s[i:i+n] for i in range(len(s)-n+1))
        
        ngrams1 = get_ngrams(s1)
        ngrams2 = get_ngrams(s2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def reset(self):
        """重置去重器"""
        self._seen_hashes.clear()
        self._seen_titles.clear()
    
    def load_history(self, titles: List[str]):
        """从历史加载已见标题"""
        self._seen_titles.extend(titles)


def create_enhanced_fetcher(language: str = "zh") -> EnhancedNewsSources:
    """创建增强版新闻源"""
    return EnhancedNewsSources(language)
