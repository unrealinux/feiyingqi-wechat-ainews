"""护栏测试：测试进程内绝不允许写线上微信账号。

背景（真实事故）：tests/test_main.py::TestScheduler::test_run_once_returns_bool
原先是直接调 run_once() 的。run_once 会抓新闻、调 LLM、出封面，最后走到
publish_article() → create_draft()，也就是真实写入公众号草稿箱。
结果是每跑一次 pytest 就往草稿箱塞一篇真实草稿（01:33:13 / 01:42:48 /
14:44 的草稿均与 pytest 运行时刻一一对应）。

publisher 现在会在检测到 pytest 上下文时直接拒绝这些写操作。
"""

import json
import os

import pytest

from src.publisher import LiveWriteBlockedInTest, WeChatPublisher


WRITE_OPERATIONS = [
    ("create_draft", ("标题", "<p>正文</p>")),
    ("delete_draft", ("some-media-id",)),
    ("publish_draft", ("some-media-id",)),
    ("update_draft_cover", ("some-media-id", "some-thumb-id")),
    ("_upload_media", ("output/cover.png", "image")),
]


@pytest.fixture
def live_ctx(monkeypatch):
    """模拟 pytest 运行时的上下文变量。"""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_x.py::test_y (call)")
    monkeypatch.delenv("ALLOW_LIVE_WECHAT_IN_TEST", raising=False)


def test_test_context_is_detected(live_ctx):
    """pytest 确实设置了 PYTEST_CURRENT_TEST（护栏依赖这个前提）。"""
    assert os.environ.get("PYTEST_CURRENT_TEST")


@pytest.mark.parametrize("name,args", WRITE_OPERATIONS, ids=[n for n, _ in WRITE_OPERATIONS])
def test_write_ops_refused_in_test_context(live_ctx, name, args):
    """五个写操作在测试上下文内必须直接抛错，且不发出任何网络请求。"""
    from unittest.mock import patch

    pub = WeChatPublisher()
    pub.get_access_token = lambda: "fake-token"  # 若护栏失效也不该真的去调微信

    with patch("src.publisher.requests.post") as m_post:
        with pytest.raises(LiveWriteBlockedInTest):
            getattr(pub, name)(*args)
    assert not m_post.called, f"{name} 在测试上下文内仍发出了网络请求"


def test_read_only_list_drafts_is_not_blocked(live_ctx):
    """只读的 list_drafts 必须照常可用（护栏只拦写操作）。"""
    from unittest.mock import patch

    class _Resp:
        encoding = "utf-8"
        content = json.dumps(
            {"item": [{"media_id": "m", "content": {"news_item": [{"title": "只读可查"}]}}]},
            ensure_ascii=False,
        ).encode("utf-8")

        def json(self):
            return json.loads(self.content.decode("utf-8"))

    pub = WeChatPublisher()
    pub.get_access_token = lambda: "fake-token"
    with patch("src.publisher.requests.post", return_value=_Resp()):
        assert pub.list_drafts() == [("只读可查", "m")]


def test_explicit_opt_out_is_honoured(monkeypatch):
    """确需联调时，显式设置 ALLOW_LIVE_WECHAT_IN_TEST=1 可以放行护栏。"""
    from unittest.mock import patch

    monkeypatch.setenv("PYTEST_CURRENT_TEST", "tests/test_x.py::test_y (call)")
    monkeypatch.setenv("ALLOW_LIVE_WECHAT_IN_TEST", "1")

    pub = WeChatPublisher()
    pub.get_access_token = lambda: "fake-token"
    with patch("src.publisher.requests.post", side_effect=RuntimeError("网络被 mock")):
        # 放行后不再抛 LiveWriteBlockedInTest，而是走到 requests（此处被 mock 成异常）
        assert pub.delete_draft("some-media-id") is False


def test_production_is_unaffected(monkeypatch):
    """生产链路（定时任务/CLI）不带 PYTEST_CURRENT_TEST，护栏不得误伤。"""
    from unittest.mock import patch

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("ALLOW_LIVE_WECHAT_IN_TEST", raising=False)

    pub = WeChatPublisher()
    pub.get_access_token = lambda: "fake-token"
    with patch("src.publisher.requests.post", side_effect=RuntimeError("网络被 mock")):
        assert pub.delete_draft("some-media-id") is False
