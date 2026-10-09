"""发布前 AI 味门禁测试。

AGENTS.md 红线：低质/模板化内容 = 平台降权。unified_publisher.publish()
必须在建草稿之前拦住 AI 味过重的稿子（检测来自 Easel 的 src/ai_score.py）。
"""

import pytest

import src.publisher as publisher_module
from src.unified_publisher import UnifiedPublisher


AI_SLOP = (
    "近年来，随着人工智能技术的不断发展，AI 正在深度赋能各行各业。\n\n"
    "首先，它能够打造全新的生态闭环。其次，它重构了全链路的底层逻辑。最后，"
    "它为企业提供了降本增效的可能。\n\n"
    "综上所述，人工智能具有深远的意义，毋庸置疑，它必将引领产业升级，不可否认，"
    "这是一条必由之路。"
)

HUMAN_LIKE = (
    "上周三下午 4 点，我在群里看到有人问：这个模型到底能干什么？\n\n"
    "我试了 3 次。第一次它把日期算错了，第二次漏了附件，第三次才给对。"
    "20 分钟花在等它重试上。\n\n"
    "所以别急着上生产。先用一周，拿真实数据跑，看看它错在哪。"
)


@pytest.fixture()
def publisher(monkeypatch):
    """构造一个不碰网络、不写 output/ 的发布器。"""
    pub = UnifiedPublisher()
    pub.app_id = "test_app_id"
    pub.app_secret = "test_app_secret"
    monkeypatch.setattr(pub, "_save_article", lambda *a, **k: ("a.md", "a.html"))
    monkeypatch.setattr(pub, "_get_default_cover", lambda: None)
    return pub


def test_ai_slop_is_blocked_before_draft(publisher, monkeypatch):
    calls = []
    monkeypatch.setattr(
        publisher_module, "publish_article",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    result = publisher.publish(title="测试", content=AI_SLOP)

    assert result["success"] is False
    assert "AI 味" in result["error"]
    assert result["ai_score"]["total_score"] >= result["ai_score"]["threshold"]
    assert result["ai_score"]["hit_phrases"], "应报告命中的套话样本"
    assert calls == [], "门禁必须先于建草稿，不能调用 publish_article"


def test_human_like_content_passes_gate(publisher, monkeypatch):
    calls = []
    monkeypatch.setattr(
        publisher_module, "publish_article",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    result = publisher.publish(title="测试", content=HUMAN_LIKE)

    assert result["success"] is True
    assert len(calls) == 1, "通过门禁后应正常走到发布层"


def test_threshold_is_overridable(publisher, monkeypatch):
    monkeypatch.setattr(publisher_module, "publish_article", lambda **kwargs: True)

    result = publisher.publish(title="测试", content=AI_SLOP, ai_threshold=100.0)

    assert result["success"] is True


def test_choke_point_blocks_before_touching_wechat(monkeypatch):
    """scheduler / main 直达 src.publisher.publish_article() 的路径也要被拦住。"""
    def _boom(*a, **k):
        raise AssertionError("门禁必须早于 WeChatPublisher 构造（否则会先换 token/建草稿）")

    monkeypatch.setattr(publisher_module, "WeChatPublisher", _boom)

    assert publisher_module.publish_article(title="测试", content=AI_SLOP) is False


def test_choke_point_strips_html_before_scoring(monkeypatch):
    """scheduler 传的是渲染好的 HTML，标签不能把 AI 味稀释掉。"""
    monkeypatch.setattr(
        publisher_module, "WeChatPublisher",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("应当被门禁拦住")),
    )
    html_slop = "<p>首先，赋能生态。</p><p>其次，打造闭环链路。</p><p>综上所述，具有深远的意义。</p>"

    assert publisher_module.publish_article(
        title="测试", content=html_slop, content_is_html=True
    ) is False
