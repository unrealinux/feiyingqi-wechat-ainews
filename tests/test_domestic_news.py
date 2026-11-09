"""国内新闻源解析：选择器必须真的能从页面里捞出标题链接。

这些站点的 DOM 会改，改了就抓 0 条，而流水线只是"没稿"，很难被注意到。
这里用固定 HTML 把「选择器 + 相对链接补全 + 短标题过滤」钉住。
"""

from unittest.mock import patch

import pytest

from src.domestic_news import DOMESTIC_SITES, fetch_domestic_news

# 每个站点一段能代表其真实结构的最小 HTML
_PAGES = {
    "https://www.36kr.com/information/AI/": """
        <a class="article-item-pic" href="/p/1"></a>
        <div class="article-item-info">
          <a class="article-item-title" href="/p/4062169952851589">机器人抢饭碗之前，先来和你抢对象了</a>
        </div>
        <a class="article-item-title" href="/p/2">短标题</a>
    """,
    "https://www.qbitai.com/": """
        <a href="https://www.qbitai.com/category/ai">分类</a>
        <a href="https://www.qbitai.com/2026/11/508498.html">黄仁勋承认出轨发全员信道歉！英伟达启动紧急调查</a>
    """,
    "https://www.huxiu.com/": """
        <a class="article-title" href="https://www.huxiu.com/article/4904244.html">黄仁勋的恋爱脑，伤到了哪些硅谷大佬</a>
    """,
    "https://top.baidu.com/board?tab=realtime": """
        <a class="title_dIF3B" href="https://www.baidu.com/s?wd=x">又一地官宣公办普高“愿上尽上”</a>
    """,
}


class _Response:
    def __init__(self, text: str):
        self.text = text
        self.status_code = 200


def _fake_get(url, **_kwargs):
    return _Response(_PAGES[url])


@pytest.mark.parametrize("site", sorted(DOMESTIC_SITES))
def test_each_site_extracts_title_and_absolute_url(site):
    with patch("requests.get", side_effect=_fake_get):
        items = fetch_domestic_news(max_workers=1, sites=[site])

    assert items, f"{site} 应该捞出至少一条"
    item = items[0]
    assert len(item.title) > 10
    assert item.url.startswith("http"), f"{site} 的链接要补成绝对地址：{item.url}"
    assert item.source == site


def test_short_titles_are_dropped():
    """36kr 页面里那段「短标题」不够长，不该进素材。"""
    with patch("requests.get", side_effect=_fake_get):
        items = fetch_domestic_news(max_workers=1, sites=["36kr"])

    assert [i.title for i in items] == ["机器人抢饭碗之前，先来和你抢对象了"]


def test_removed_dead_sources_are_gone():
    """知乎 401、微博 403、机器之心前端渲染：抓不到就别留配置项，免得天天报 0 条。"""
    from src.domestic_news import CONFIG_KEY_TO_SITE

    assert not {"知乎", "微博", "机器之心"} & set(DOMESTIC_SITES)
    assert not {"zhihu", "weibo", "jiqizhixin"} & set(CONFIG_KEY_TO_SITE)
