"""封面主题选择：主题必须跟文章内容对得上。

2026-10-14 事故：标题里的“自动化”命中了 robot（工业机械臂）主题，给一篇
“职场 AI 工作台”的文章配了工厂机械臂封面。这里把几个高频误配钉成回归。
"""

from src.ai_photo_cover import _THEMES, pick_theme


class TestKeywordThemes:
    def test_office_automation_is_not_a_robot_arm(self):
        assert pick_theme("WorkBuddy 自动化：把重复劳动变成 Agent 资产") == "workbench"

    def test_real_industrial_robotics_still_hits_robot(self):
        assert pick_theme("工厂自动化产线上的人形机器人") == "robot"
        assert pick_theme("具身智能：机器人如何理解物理世界") == "robot"

    def test_agent_and_tool_articles_get_a_desk(self):
        # 同分平局会按日期选，断言“落在桌面场景”而不是具体哪个（都不是工厂/机房）
        for title in ("智能体团队怎么分工", "AI 笔记工具横评"):
            assert pick_theme(title) in {"office", "workbench"}, title

    def test_dev_tools_get_a_desk_not_a_factory(self):
        # office/workbench 都是“桌面”场景，两个都算对；关键是别出工厂/机房/芯片
        for title in ("Cursor 编程助手更新了", "AI 代码工具横评"):
            assert pick_theme(title) in {"office", "workbench"}, title

    def test_hardware_articles_keep_their_themes(self):
        assert pick_theme("英伟达新一代芯片的制程") == "chip"
        assert pick_theme("数据中心能耗困局") == "datacenter"

    def test_no_keyword_falls_back_deterministically(self):
        """没命中关键词时按日期轮换，同一天结果稳定，不能随机。"""
        assert pick_theme("一个不带关键词的标题") == pick_theme("另一个也不带关键词的标题")


class TestThemeSpecs:
    def test_every_theme_has_keywords_and_a_prompt(self):
        for name, spec in _THEMES.items():
            assert spec["keywords"], name
            assert len(spec["prompt"]) > 80, name

    def test_prompts_forbid_text_in_the_image(self):
        """项目约定：封面上不叠任何文字。"""
        for name, spec in _THEMES.items():
            assert "no text" in spec["prompt"].lower() or "without text" in spec["prompt"].lower(), name

    def test_ambiguous_keyword_is_not_claimed_twice(self):
        """“自动化”只能属于一个主题，否则同分平局会让封面随日期跳。"""
        owners = [n for n, s in _THEMES.items() if "自动化" in s["keywords"]]
        assert owners == ["workbench"]


class TestImageEndpoint:
    """文生图端点跟文本 LLM 共用 agnes.base_url，别再多一个只能改代码的硬编码。"""

    def test_default_when_base_url_missing(self):
        from src.ai_photo_cover import AGNES_API_BASE, _image_endpoint

        assert _image_endpoint({"agnes": {}}) == f"{AGNES_API_BASE}/images/generations"

    def test_respects_configured_base_url(self):
        from src.ai_photo_cover import _image_endpoint

        cfg = {"agnes": {"base_url": "https://proxy.example.com/v1"}}
        assert _image_endpoint(cfg) == "https://proxy.example.com/v1/images/generations"

    def test_trailing_slash_does_not_double_up(self):
        from src.ai_photo_cover import _image_endpoint

        cfg = {"agnes": {"base_url": "https://proxy.example.com/v1/"}}
        assert _image_endpoint(cfg) == "https://proxy.example.com/v1/images/generations"


class TestFontLookup:
    """字体候选表必须跨平台：Linux 上没有 msyh.ttc，写死 Windows 路径就出不了图。"""

    def test_finds_a_cjk_font_on_this_machine(self):
        from src.fonts import find_font

        for bold in (True, False):
            path = find_font(bold=bold)
            assert path, f"本机找不到中文字体（bold={bold}），封面会退化成兜底图"

    def test_load_font_never_raises(self):
        from src.fonts import load_font

        assert load_font(24) is not None
        assert load_font(24, bold=False) is not None

    def test_brand_cover_builds_without_font_error(self, tmp_path):
        """品牌风封面（工具指南用的那张）在 Linux 上要能真的画出来。"""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from build_workbuddy_cover import build

        out = tmp_path / "cover.jpg"
        build(
            str(out),
            title_lines=["标题第一行", "标题第二行"],
            kicker="测试 · 2026-11-13",
            subtitle="副标题",
            footer="页脚",
            variant="steps",
            steps_label="一 → 二 → 三",
        )
        assert out.exists() and out.stat().st_size > 5000
