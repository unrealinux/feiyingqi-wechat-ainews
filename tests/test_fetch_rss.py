"""RSS 素材必须剥成纯文本。

2026-10 接 AI 工具更新源（GitHub Releases / changelog）后发现：release notes 的
summary 是 HTML，标签会原样进 prompt 素材，白占 token 还干扰排版。
"""

import requests

from src.fetcher import NewsFetcher


ATOM_WITH_HTML_SUMMARY = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>v1.2.3</title>
    <link href="https://example.com/releases/1.2.3"/>
    <updated>2026-10-10T00:00:00Z</updated>
    <summary type="html">&lt;h2&gt;新增决策模型&lt;/h2&gt;
      &lt;p&gt;可以在终端直接用 &lt;code&gt;run --ask&lt;/code&gt; 提问。&lt;/p&gt;</summary>
  </entry>
</feed>""".encode("utf-8")


class _FakeResponse:
    status_code = 200
    content = ATOM_WITH_HTML_SUMMARY


def test_rss_summary_is_stripped_to_plain_text(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse())

    items = NewsFetcher()._fetch_rss("某工具 Releases", "https://example.com/feed")

    assert len(items) == 1
    item = items[0]
    assert item.title == "v1.2.3"
    assert item.url == "https://example.com/releases/1.2.3"
    assert "<" not in item.description and ">" not in item.description
    assert "新增决策模型" in item.description
    assert "run --ask" in item.description


def test_rss_returns_empty_on_http_error(monkeypatch):
    class _Fail:
        status_code = 404
        content = b""

    monkeypatch.setattr(requests, "get", lambda *a, **k: _Fail())

    assert NewsFetcher()._fetch_rss("挂掉的源", "https://example.com/gone") == []
