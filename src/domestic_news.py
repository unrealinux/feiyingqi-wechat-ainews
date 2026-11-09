"""
Domestic News Sources - 国内新闻源

优化国内访问：36kr、量子位、虎嗅、百度热搜（选择器均为线上实测可用）
"""

import logging
from typing import List, Optional
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 每个站点只描述「标题链接」选哪一个（link_selector），抓取逻辑统一。
# 选择器必须对着线上页面实测过；抓不到就别留在这里，否则日志里天天是 0 条。
# 已移除的源（都无法直接 requests 抓）：
#   知乎  接口 401（要登录 cookie）、微博 接口 403、机器之心 列表前端渲染无静态 HTML
DOMESTIC_SITES = {
    "36kr": {
        "url": "https://www.36kr.com/information/AI/",
        "link_selector": "a.article-item-title",
        "name": "36kr",
    },
    "量子位": {
        "url": "https://www.qbitai.com/",
        "link_selector": 'a[href^="https://www.qbitai.com/20"]',
        "name": "量子位",
    },
    "虎嗅": {
        "url": "https://www.huxiu.com/",
        "link_selector": "a.article-title",
        "name": "虎嗅",
    },
    "百度": {
        "url": "https://top.baidu.com/board?tab=realtime",
        # 百度用 css-modules 哈希类名（title_dIF3B），前缀匹配比整串稳定
        "link_selector": 'a[class^="title_"]',
        "name": "百度热搜",
    },
}


def fetch_domestic_news(
    max_workers: int = 5, sites: Optional[List[str]] = None
) -> List:
    """并发获取国内新闻

    Args:
        sites: 只抓取这些 DOMESTIC_SITES 键（如 ["36kr", "量子位"]）；
               None 表示全部。
    """
    from src.fetcher import NewsItem

    results = []

    logger.info("Fetching domestic news sources...")

    def fetch_single_site(site_name: str, site_config: dict) -> List:
        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            response = requests.get(site_config["url"], headers=headers, timeout=10)

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            parsed = urlparse(site_config["url"])

            items = []
            for elem in soup.select(site_config["link_selector"])[:5]:
                title = elem.get_text(strip=True)
                href = elem.get("href") or ""

                if href.startswith("/"):
                    href = f"{parsed.scheme}://{parsed.netloc}{href}"

                # 过滤无效标题
                if title and len(title) > 10 and "广告" not in title:
                    items.append(
                        NewsItem(
                            title=title,
                            url=href if href.startswith("http") else site_config["url"],
                            source=site_name,
                            description=f"来源：{site_name}",
                            published_at=datetime.now().strftime("%Y-%m-%d"),
                        )
                    )

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
            if sites is None or name in sites
        }

        for future in as_completed(futures):
            try:
                items = future.result()
                results.extend(items)
            except Exception:
                pass

    return results


def search_baidu(keyword: str, max_results: int = 10) -> List:
    """百度搜索"""
    from src.fetcher import NewsItem

    try:
        import requests

        url = "https://www.baidu.com/s"
        params = {"wd": keyword, "rn": max_results}

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
                    results.append(
                        NewsItem(
                            title=title,
                            url=href,
                            source="百度",
                            description=f"百度搜索: {keyword}",
                            published_at=datetime.now().strftime("%Y-%m-%d"),
                        )
                    )

        return results

    except Exception as e:
        logger.warning(f"Baidu search failed: {e}")
        return []


# config.yaml news.domestic_sources 的键 → DOMESTIC_SITES 的键
# （只保留实测抓得到的站点；知乎/微博/机器之心见 DOMESTIC_SITES 上方说明）
CONFIG_KEY_TO_SITE = {
    "36kr": "36kr",
    "liangzi": "量子位",
    "huxiu": "虎嗅",
    "baidu": "百度",
}


def fetch_all_domestic(domestic_cfg: Optional[dict] = None) -> List:
    """获取所有国内新闻

    Args:
        domestic_cfg: config.yaml 的 news.domestic_sources 段；
                      None 表示不按配置过滤（全部启用）。
    """
    cfg = domestic_cfg if domestic_cfg is not None else {}

    def _on(key: str) -> bool:
        return bool(cfg.get(key, True))

    enabled_sites = [site for ckey, site in CONFIG_KEY_TO_SITE.items() if _on(ckey)]

    all_news = []

    logger.info("=" * 50)
    logger.info("Fetching domestic news sources...")
    logger.info("=" * 50)

    if enabled_sites:
        all_news.extend(fetch_domestic_news(sites=enabled_sites))

    logger.info("=" * 50)
    logger.info(f"Domestic news total: {len(all_news)}")
    logger.info("=" * 50)

    return all_news


if __name__ == "__main__":
    print("Testing domestic news sources...")
    news = fetch_all_domestic()
    print(f"\nTotal: {len(news)}")
    for item in news[:5]:
        print(f"  - [{item.source}] {item.title[:40]}")
