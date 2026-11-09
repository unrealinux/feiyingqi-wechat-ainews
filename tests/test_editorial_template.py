"""editorial_template 渲染器回归测试（深读排版母版）"""

import pytest

from src import editorial_template as et


def _spec(**overrides):
    spec = {
        "meta_line": "2026年9月16日 ｜ 测试",
        "title": "主标题\n第二行",
        "subtitle": "一句话副标题",
        "lead": ["开头一", "开头二"],
        "sections": [
            {"heading": "第一节", "accent": "red",
             "blocks": [{"type": "p", "text": "正文 **加粗**"},
                        {"type": "datacard", "lines": [
                            {"label": "指标", "note": "注释", "value": "97.6%"}]}]},
            {"heading": "第二节", "accent": "green",
             "blocks": [{"type": "bars", "caption": "对比", "rows": [
                 {"label": "我方", "value": 41.4, "color": "red"},
                 {"label": "对手", "value": 31.4, "color": "green"}]}]},
            {"heading": "第三节", "accent": "red",
             "blocks": [{"type": "bullets", "items": ["**要点**：说明"]}]},
        ],
        "closing": ["收束一", "收束二"],
        "sources": ["1. 来源甲", "2. 来源乙", "3. 来源丙"],
    }
    spec.update(overrides)
    return spec


def test_render_uses_editorial_palette_and_structure():
    html = et.render(_spec())
    assert html.startswith("<section")
    assert et.BG in html and et.ACCENT_PRIMARY in html and et.ACCENT_SECOND in html
    assert "主标题<br>第二行" in html          # 手工断行
    assert "壹" in html and "贰" in html and "叁" in html
    assert "border-left:4px solid" in html      # 数据卡 / 图表
    assert "width:41.4%" in html                # 条形图宽度 = 数值本身
    assert "数据来源（均真实可查）" in html
    assert "text-indent:2em" in html


def test_inline_bold_and_escaping():
    html = et.render(_spec(lead=["危险 <script>alert(1)</script> **粗**"]))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<strong>粗</strong>" in html


def test_markdown_link_in_body_downgrades_to_plain_text():
    """正文不支持站外链接：`[标题](url)` 不能以字面方括号出现在正文里。"""
    html = et.render(_spec(sections=[
        {"heading": "第一节", "accent": "red",
         "blocks": [{"type": "p", "text": "见[量子位这篇](https://qbitai.com/1.html)"}]},
        {"heading": "第二节", "accent": "green",
         "blocks": [{"type": "bullets", "items": ["[36kr](https://36kr.com/p/1)"]}]},
        {"heading": "第三节", "accent": "red",
         "blocks": [{"type": "quote", "text": "[虎嗅](https://huxiu.com/a/1.html)"}]},
    ]))
    assert "[量子位这篇]" not in html and "https://qbitai.com/1.html" not in html
    assert "见量子位这篇" in html
    assert "[36kr]" not in html and "https://36kr.com/p/1" not in html
    assert "[虎嗅]" not in html and "https://huxiu.com/a/1.html" not in html


def test_sources_keep_their_urls_for_traceability():
    """sources 是唯一保留链接的地方：溯源不能丢。"""
    html = et.render(_spec(sources=[
        "1. [量子位：某标题](https://qbitai.com/1.html)",
        "2. 机器之心《另一篇》",
    ]))
    assert "https://qbitai.com/1.html" in html
    assert "[量子位：某标题]" not in html
    assert "量子位：某标题 https://qbitai.com/1.html" in html


@pytest.mark.parametrize("field", ["title", "subtitle", "lead", "sections", "closing", "sources"])
def test_missing_required_field_rejected(field):
    spec = _spec()
    spec[field] = [] if field != "title" and field != "subtitle" else ""
    with pytest.raises(et.EditorialSpecError):
        et.render(spec)


def test_requires_at_least_two_sources():
    with pytest.raises(et.EditorialSpecError):
        et.render(_spec(sources=["1. 只有一个来源"]))


def test_requires_at_least_three_sections():
    spec = _spec()
    spec["sections"] = spec["sections"][:2]
    with pytest.raises(et.EditorialSpecError):
        et.render(spec)


def test_unknown_block_type_rejected():
    spec = _spec()
    spec["sections"][0]["blocks"] = [{"type": "marquee", "text": "x"}]
    with pytest.raises(et.EditorialSpecError):
        et.render(spec)


@pytest.mark.parametrize("raw", [
    '{"a": 1}',
    '```json\n{"a": 1}\n```',
    '好的，这是结果：{"a": 1} 以上。',
])
def test_extract_json_tolerates_wrapping(raw):
    assert et.extract_json(raw) == {"a": 1}


def test_extract_json_raises_on_garbage():
    with pytest.raises(et.EditorialSpecError):
        et.extract_json("没有 JSON")


def test_draft_title_strips_line_breaks_and_caps_length():
    assert et.draft_title({"title": "第一行\n第二行"}) == "第一行 第二行"
    assert len(et.draft_title({"title": "长" * 200})) == 64


def test_ground_numeric_blocks_drops_unsourced_numbers():
    spec = _spec()
    spec["sections"][1]["blocks"] = [{"type": "bars", "caption": "对比", "rows": [
        {"label": "有出处", "value": 41.4, "color": "red"},
        {"label": "也有出处", "value": 31.4, "color": "green"},
        {"label": "编的", "value": 65.0, "color": "green"},
    ]}]
    dropped = et.ground_numeric_blocks(spec, "素材里有 41.4% 和 31.4%，但没有别的数")
    rows = spec["sections"][1]["blocks"][0]["rows"]
    assert [r["value"] for r in rows] == [41.4, 31.4]
    assert any("65.0" in d for d in dropped)
    assert not any("41.4" in d for d in dropped)


def test_ground_numeric_blocks_removes_section_when_all_blocks_dropped():
    spec = _spec()
    spec["sections"][1]["blocks"] = [{"type": "bars", "rows": [
        {"label": "A", "value": 1.0}, {"label": "B", "value": 2.0}]}]
    before = len(spec["sections"])
    et.ground_numeric_blocks(spec, "素材里没有这两个数")
    assert len(spec["sections"]) == before - 1
    assert all(s.get("heading") != "第二节" for s in spec["sections"])


def test_find_blacklisted_terms_flags_mouse_mistranslation():
    assert et.find_blacklisted_terms(_spec(lead=["鼠标大脑皮层实验"])) == ["鼠标"]
    assert et.find_blacklisted_terms(_spec(lead=["小鼠大脑皮层实验"])) == []


def test_find_ungrounded_numbers_audits_prose_only():
    spec = _spec(lead=["开头"])
    spec["sections"][0]["blocks"] = [{"type": "p", "text": "官方称 97.6% 的准确率，另称 88.8% 的提升"}]
    flagged = et.find_ungrounded_numbers(spec, "素材里只有 97.6%")
    assert flagged == ["88.8"]


class TestStepsBlock:
    """steps 块：操作指南的主干（序号 + 动作 + 会看到什么）。"""

    def _spec_with_steps(self, items):
        return _spec(sections=[
            {"heading": "安装", "accent": "red", "blocks": [{"type": "steps", "items": items}]},
            {"heading": "第二节", "accent": "green", "blocks": [{"type": "p", "text": "正文"}]},
            {"heading": "第三节", "accent": "red", "blocks": [{"type": "p", "text": "正文"}]},
        ])

    def test_numbers_steps_and_keeps_detail(self):
        html = et.render(self._spec_with_steps([
            {"title": "下载客户端", "detail": "访问 https://example.com ，选对应系统"},
            {"title": "初始化工作区", "detail": "选一个独立目录"},
        ]))

        assert "1.</span> <strong>下载客户端</strong>" in html
        assert "2.</span> <strong>初始化工作区</strong>" in html
        assert "https://example.com" in html
        assert "选一个独立目录" in html

    def test_accepts_plain_strings(self):
        html = et.render(self._spec_with_steps(["打开设置", "接入 API Key"]))

        assert "打开设置" in html and "接入 API Key" in html

    def test_empty_steps_is_rejected(self):
        with pytest.raises(et.EditorialSpecError):
            et.render(self._spec_with_steps([]))

    def test_step_without_title_is_rejected(self):
        with pytest.raises(et.EditorialSpecError):
            et.render(self._spec_with_steps([{"detail": "只有细节没有标题"}]))

    def test_steps_survive_numeric_grounding(self):
        """steps 里不是图表数据，不该被数字闸删掉。"""
        spec = self._spec_with_steps([{"title": "三步走完", "detail": "第 3 步"}])

        dropped = et.ground_numeric_blocks(spec, "素材里没有任何数字")

        assert dropped == []
        assert "三步走完" in et.render(spec)


def test_bullet_items_written_as_dicts_are_flattened():
    """模型偶尔把 bullet 条目写成 {"text": ...}，不能把 dict 直接印进正文。"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.editorial_template import render

    spec = {
        "meta_line": "2026年1月1日 ｜ 测试", "title": "T", "subtitle": "S",
        "lead": ["第一段。"],
        "sections": [
            {"heading": "一", "accent": "red",
             "blocks": [{"type": "bullets", "items": [{"text": "字典条目"}, "字符串条目"]}]},
            {"heading": "二", "accent": "green", "blocks": [{"type": "p", "text": "x"}]},
            {"heading": "三", "accent": "red", "blocks": [{"type": "p", "text": "y"}]},
        ],
        "closing": ["收束一。", "收束二。"], "sources": ["1. a", "2. b"],
    }
    html = render(spec)
    assert "· 字典条目" in html
    assert "· 字符串条目" in html
    assert "{'text'" not in html
