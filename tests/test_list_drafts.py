"""回归测试：WeChatPublisher.list_drafts 的标题解析与中文解码。

历史上这里读的是 content.title（微信 draft/batchget 并不返回该键，
标题在 content.news_item[0].title），导致草稿箱里每一篇都显示「(无标题)」。
同时该接口返回 text/plain 且不带 charset，requests 默认按 ISO-8859-1 解码，
中文标题会变成乱码。
"""

import json
from unittest.mock import patch

import pytest

from src.publisher import WeChatPublisher


class _FakeResponse:
    """尽量贴近 requests 的真实行为：encoding 默认 ISO-8859-1，json() 按 encoding 解码。"""

    def __init__(self, payload: dict):
        self.content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.encoding = "ISO-8859-1"

    @property
    def text(self):
        return self.content.decode(self.encoding)

    def json(self):
        return json.loads(self.text)


def _payload(*drafts):
    """drafts: (title, media_id) 或 (None, media_id) 表示无标题。"""
    items = []
    for title, media_id in drafts:
        news_item = [{"title": title}] if title is not None else []
        items.append({"media_id": media_id, "content": {"news_item": news_item}})
    return {"item": items, "total_count": len(items)}


@pytest.fixture
def publisher():
    pub = WeChatPublisher()
    pub.get_access_token = lambda: "fake-token"
    return pub


def _call(pub, payload):
    with patch("src.publisher.requests.post", return_value=_FakeResponse(payload)):
        return pub.list_drafts()


def test_reads_title_from_news_item(publisher):
    """标题必须从 news_item[0].title 取。"""
    result = _call(publisher, _payload(("当 AI 巨头开始 自我预警", "mid-1")))
    assert result == [("当 AI 巨头开始 自我预警", "mid-1")]


def test_chinese_title_is_not_mojibake(publisher):
    """中文标题不得被 ISO-8859-1 解码成乱码。"""
    title = "硅谷精英的恐惧：当AI变成生物武器的威胁"
    result = _call(publisher, _payload((title, "mid-2")))
    assert result[0][0] == title
    assert "å" not in result[0][0] and "ç" not in result[0][0]


def test_preserves_original_order(publisher):
    payload = _payload(("第一篇", "a"), ("第二篇", "b"), ("第三篇", "c"))
    assert [t for t, _ in _call(publisher, payload)] == ["第一篇", "第二篇", "第三篇"]


def test_falls_back_to_content_title(publisher):
    """news_item 缺失时退回 content.title（兼容老数据）。"""
    payload = {"item": [{"media_id": "m", "content": {"title": "旧格式标题"}}]}
    assert _call(publisher, payload) == [("旧格式标题", "m")]


def test_placeholder_when_no_title_anywhere(publisher):
    payload = {"item": [{"media_id": "m", "content": {}}]}
    assert _call(publisher, payload) == [("(无标题)", "m")]


def test_empty_draft_box(publisher):
    assert _call(publisher, {"item": [], "total_count": 0}) == []


def test_returns_empty_list_when_no_token():
    pub = WeChatPublisher()
    pub.get_access_token = lambda: None
    assert pub.list_drafts() == []


def test_swallows_transport_error(publisher):
    """网络异常不应抛给调用方（干跑/巡检脚本依赖这个行为）。"""
    with patch("src.publisher.requests.post", side_effect=RuntimeError("boom")):
        assert publisher.list_drafts() == []
