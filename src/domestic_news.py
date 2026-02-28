"""
Domestic News Sources - 国内新闻源

优化国内访问：百度、微博、知乎、36kr、量子位、机器之心等
"""

import os
import re
import json
import logging
from typing import List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DOMESTIC_SITES = {
    # 中文科技媒体
    "36kr": {
        "url": "https://www.36kr.com/information/AI/",
        "selector": "article",
        "name": "36kr"
    },
    "量子位": {
        "url": "https://www.qbitai.com/",
        "selector": "article",
        "name": "量子位"
    },
    "机器之心": {
        "url": "https://www.jiqizhixin.com/",
        "selector": "article",
        "name": "机器之心"
    },
    "虎嗅": {
        "url": "https://www.huxiu.com/",
        "selector": "article",
        "name": "虎嗅"
    },
    "知乎": {
        "url": "https://www.zhihu.com/topic/19550517/hot",
        "selector": ".List-item",
        "name": "知乎"
    },
    "微博": {
        "url": "https://weibo.com/hot/search",
        "selector": "tr",
        "name": "微博"
    },
    "百度": {
        "url": "https://top.baidu.com/board?tab=realtime",
        "selector": ".item-wrap",
        "name": "百度热搜"
    },
}


def fetch_domestic_news(max_workers: int = 5) -> List:
    """并发获取国内新闻"""
    from src.fetcher import NewsItem
    
    results = []
    
    logger.info("Fetching domestic news sources...")
    
    def fetch_single_site(site_name: str, site_config: dict) -> List:
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            }
            
            response = requests.get(
                site_config["url"], 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.select(site_config["selector"])[:5]
            
            items = []
            for article in articles:
                title = ""
                link = ""
                
                # 尝试多种选择器
                title_elem = (
                    article.find("a") or 
                    article.find("h2") or 
                    article.find("h3") or
                    article.find(class_=re.compile("title", re.I))
                )
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get("href", "")
                    if href:
                        if href.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(site_config["url"])
                            link = f"{parsed.scheme}://{parsed.netloc}{href}"
                        elif href.startswith("http"):
                            link = href
                
                # 过滤无效标题
                if title and len(title) > 10 and "广告" not in title:
                    items.append(NewsItem(
                        title=title,
                        url=link or site_config["url"],
                        source=site_name,
                        description=f"来源：{site_name}",
                        published_at=datetime.now().strftime("%Y-%m-%d")
                    ))
            
            logger.info(f"  ✓ {site_name}: {len(items)} 条")
            return items
            
        except Exception as e:
            logger.warning(f"  ✗ {site_name}: {str(e)[:50]}")
            return []
    
    # 并发获取
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_single_site, name, config): name 
            for name, config in DOMESTIC_SITES.items()
        }
        
        for future in as_completed(futures):
            try:
                items = future.result()
                results.extend(items)
            except Exception as e:
                pass
    
    return results


def search_baidu(keyword: str, max_results: int = 10) -> List:
    """百度搜索"""
    from src.fetcher import NewsItem
    
    try:
        import requests
        
        url = "https://www.baidu.com/s"
        params = {
            "wd": keyword,
            "rn": max_results
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = "utf-8"
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        
        results = []
        for item in soup.select(".result")[:max_results]:
            title_elem = item.find("h3")
            if title_elem:
                title = title_elem.get_text(strip=True)
                link = item.find("a")
                href = link.get("href", "") if link else ""
                
                if title and href:
                    results.append(NewsItem(
                        title=title,
                        url=href,
                        source="百度",
                        description=f"百度搜索: {keyword}",
                        published_at=datetime.now().strftime("%Y-%m-%d")
                    ))
        
        return results
        
    except Exception as e:
        logger.warning(f"Baidu search failed: {e}")
        return []


def get_zhihu_hot() -> List:
    """知乎热榜"""
    from src.fetcher import NewsItem
    
    try:
        import requests
        
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.zhihu.com/"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = []
            
            for item in data.get("data", [])[:10]:
                title = item.get("target", {}).get("title", "")
                url = f"https://www.zhihu.com/question/{item.get('target', {}).get('id', '')}"
                
                if title:
                    items.append(NewsItem(
                        title=title,
                        url=url,
                        source="知乎",
                        description=f"热度: {item.get('detail_text', '')}",
                        published_at=datetime.now().strftime("%Y-%m-%d")
                    ))
            
            return items
            
    except Exception as e:
        logger.warning(f"Zhihu hot failed: {e}")
    
    return []


def get_weibo_hot() -> List:
    """微博热搜"""
    from src.fetcher import NewsItem
    
    try:
        import requests
        
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = []
            
            for item in data.get("data", {}).get("realtime", [])[:15]:
                word = item.get("word", "")
                raw_url = item.get("raw_url", "")
                
                if word and "AI" in word or "人工智能" in word or "大模型" in word or "GPT" in word:
                    items.append(NewsItem(
                        title=word,
                        url=f"https://s.weibo.com/weibo?q={word}",
                        source="微博",
                        description=f"热度: {item.get('num', '')}",
                        published_at=datetime.now().strftime("%Y-%m-%d")
                    ))
            
            return items
            
    except Exception as e:
        logger.warning(f"Weibo hot failed: {e}")
    
    return []


def fetch_all_domestic() -> List:
    """获取所有国内新闻"""
    all_news = []
    
    logger.info("="*50)
    logger.info("Fetching domestic news sources...")
    logger.info("="*50)
    
    # 知乎
    logger.info("Fetching Zhihu hot...")
    zhihu_news = get_zhihu_hot()
    all_news.extend(zhihu_news)
    
    # 微博
    logger.info("Fetching Weibo hot...")
    weibo_news = get_weibo_hot()
    all_news.extend(weibo_news)
    
    # 网站采集
    logger.info("Fetching domestic sites...")
    site_news = fetch_domestic_news()
    all_news.extend(site_news)
    
    logger.info("="*50)
    logger.info(f"Domestic news total: {len(all_news)}")
    logger.info("="*50)
    
    return all_news


if __name__ == "__main__":
    print("Testing domestic news sources...")
    news = fetch_all_domestic()
    print(f"\nTotal: {len(news)}")
    for item in news[:5]:
        print(f"  - [{item.source}] {item.title[:40]}")
