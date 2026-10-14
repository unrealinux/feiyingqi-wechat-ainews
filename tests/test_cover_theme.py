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
