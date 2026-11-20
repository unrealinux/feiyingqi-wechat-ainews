"""封面线索：出图 prompt 要贴着文章内容，不是只靠标题选固定主题。

2026-11-20：封面只看标题 → pick_theme → 固定英文 prompt，正文写了什么完全无关。
Agnes 出图接口只吃文字（image_url 被明确拒绝），所以走语义层注入。
"""

from unittest.mock import patch

from src.fetcher import NewsItem
from src.cover_context import cover_context, product_names, scene_hints


SPEC = {
    "title": "Agnes 把 Agent 成本砍到 1/27",
    "subtitle": "双系统决策让智能体提速 14 倍",
    "sections": [
        {"heading": "成本结构变了，不是跑分变了"},
        {"heading": "办公文档里怎么落地"},
    ],
}
ITEMS = [NewsItem("Agnes 让 Agent 效率提速 14 倍", "https://a", "量子位", "成本降到 1/27")]


def test_context_combines_spec_and_material():
    ctx = cover_context(SPEC, ITEMS)
    assert "双系统决策" in ctx
    assert "成本结构" in ctx
    assert "Agnes" in ctx
    assert ctx.count("Agnes") <= 2, "重复片段应去重"


def test_product_names_and_scene_hints():
    names = product_names(SPEC, ITEMS)
    assert any("Agnes" in n for n in names)
    hints = scene_hints("办公文档里的智能体工作台")
    assert "办公" in hints and "文档" in hints


def test_cover_prompt_includes_article_context():
    """端到端：generate_ai_photo_cover 发给 Agnes 的 prompt 带文章线索。"""
    from src import ai_photo_cover as apc

    captured = {}

    def fake_fetch(api_key, prompt, endpoint="", size="", timeout=0):
        captured["prompt"] = prompt
        return b"fake-jpeg"  # 走不到 _compose 没关系，这里只验证 prompt

    with patch.object(apc, "_fetch_agnes_image", side_effect=fake_fetch), \
         patch("src.config.load_config", return_value={
             "agnes": {"api_key": "sk-test", "base_url": "https://api.agnes-ai.cn/v1"}
         }), \
         patch.object(apc, "_compose", return_value=b"out"):
        apc.generate_ai_photo_cover(
            "Agnes 把成本砍到 1/27", "/tmp/x.jpg", spec=SPEC, news_items=ITEMS
        )

    p = captured["prompt"]
    assert "Agnes" in p
    assert "双系统决策" in p or "成本结构" in p
    assert "no text" in p, "出图仍然不能带文字"
