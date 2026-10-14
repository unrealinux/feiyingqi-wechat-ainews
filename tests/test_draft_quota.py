"""每天 ≤1 篇的护栏。

2026-10-14 踩到的坑：`draft/batchget` 只返回**未发布**的草稿 —— 当天那篇一旦发出
就被移出草稿箱，计数变 0，护栏失效，结果同一天建了第二篇。
所以改为“本地台账 + 微信未发布草稿”取较大值。
"""

import datetime

import pytest
import requests

import src.monitoring as monitoring
import src.publisher as publisher_module
from src.monitoring import count_local_drafts_today, record_draft_created
from src.publisher import count_drafts_created_today


def _batchget_response(items=(), errcode=0):
    class _Resp:
        def json(self):
            data = {"item": list(items)}
            if errcode:
                data["errcode"] = errcode
            return data

    return _Resp()


def test_ledger_counts_only_today(tmp_path):
    record_draft_created("今天的稿子", "media1")
    record_draft_created("今天的稿子 2", "media2")
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(
        timespec="seconds"
    )
    with open(monitoring.DRAFT_LEDGER, "a", encoding="utf-8") as f:
        f.write(f'{{"time": "{yesterday}", "title": "昨天的稿子"}}\n')

    assert count_local_drafts_today() == 2


def test_api_alone_misses_published_drafts(monkeypatch):
    """核心回归：草稿箱是空的时候，靠本地台账也要能拦住第二篇。"""
    record_draft_created("今天已发出去的那篇", "media-x")
    monkeypatch.setattr(publisher_module.requests, "post", lambda *a, **k: _batchget_response([]))
    monkeypatch.setattr(
        publisher_module, "WeChatPublisher", lambda *a, **k: type("P", (), {"get_access_token": lambda self: "t"})()
    )

    assert count_drafts_created_today() == 1


def test_api_error_falls_back_to_ledger(monkeypatch):
    record_draft_created("今天的稿子", "media-y")
    monkeypatch.setattr(
        publisher_module.requests, "post", lambda *a, **k: _batchget_response(errcode=48001)
    )
    monkeypatch.setattr(
        publisher_module, "WeChatPublisher", lambda *a, **k: type("P", (), {"get_access_token": lambda self: "t"})()
    )

    assert count_drafts_created_today() == 1


def test_zero_when_nothing_was_created(monkeypatch):
    monkeypatch.setattr(publisher_module.requests, "post", lambda *a, **k: _batchget_response([]))
    monkeypatch.setattr(
        publisher_module, "WeChatPublisher", lambda *a, **k: type("P", (), {"get_access_token": lambda self: "t"})()
    )

    assert count_drafts_created_today() == 0


def test_unpublished_draft_in_wechat_also_counts(monkeypatch):
    """微信侧未发布的草稿要算数（比如有人在后台手动建了一篇）。"""
    now = int(datetime.datetime.now().timestamp())
    monkeypatch.setattr(
        publisher_module.requests,
        "post",
        lambda *a, **k: _batchget_response([{"update_time": now}]),
    )
    monkeypatch.setattr(
        publisher_module, "WeChatPublisher", lambda *a, **k: type("P", (), {"get_access_token": lambda self: "t"})()
    )

    assert count_drafts_created_today() == 1


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    """任何漏网的请求都直接失败，别把测试打到微信接口上。"""
    def _boom(*a, **k):
        raise AssertionError("测试里不该发真实请求")

    monkeypatch.setattr(requests, "post", _boom)
