"""选题/标题/可复制块三条硬约束（数据依据见 src/editorial_rules.py 顶部）。

这些规则是从 54 篇已发文章的阅读数据反推出来的，回归测试要钉住：
顶部那批标题必须过，底部那批（泛趋势/日报口吻）必须被拒。
"""

from src.editorial_rules import (
    TITLE_MAX,
    TITLE_MIN,
    has_copyable_block,
    has_tool_level_change,
    title_problems,
)
from src.fetcher import NewsItem


class TestTitleRules:
    def test_high_performing_titles_pass(self):
        """本号阅读最高的几篇，规则不能把它们拒掉。"""
        for title in (
            "当 1.7B 模型跑在本地终端 AI 智能体的底",   # 108
            "Cursor 把服务器 吞进了编辑器",              # 105
            "ChatGPT 的安全漏洞 正在被系统性利用",       # 88
            "WorkBuddy：从安装到Skill的首个任务闭环",     # 78
            "WorkBuddy 怎么接 MCP 和外部 API？实操避坑",  # 72
        ):
            assert title_problems(title) == [], title

    def test_trend_roundups_are_rejected(self):
        """底部那批：泛趋势、三款并列、说教式，没有落点。

        拦截依据分两种：日报腔（这周/三款）与新「没有具体工具名」；
        只要命中其中一条就算拦下，不要求两条同时命中。
        """
        for title in (
            "AI工具这周换了三件事",          # 这周 → 日报腔
            "三款新模型把多模态推到哪一步",   # 三款 → 泛化
            "模型不再只拼分数",              # 没有具体工具名
        ):
            assert title_problems(title), f"应当被拒: {title}"

    def test_real_news_titles_with_odd_verbs_pass(self):
        """真实标题的动词很发散，不能被动作词白名单误杀（11-16 08:00 的教训）。"""
        for title in (
            "DeepSeek 开始限额，GPT-6.2 却延期",
            "Cursor 把服务器搬进了编辑器",
            "通义千问把免费额度砍到每天 50 次",
        ):
            assert title_problems(title) == [], title

    def test_length_bounds(self):
        assert not any("长度" in p for p in title_problems("Cursor 更新后怎么接回本地工作流"))
        assert any("长度" in p for p in title_problems("Cursor 更新"))  # 太短
        long_title = "Cursor 更新之后本地工作流要怎么一步步接回来并且保证历史会话不丢"
        assert len(long_title) > TITLE_MAX
        assert any("长度" in p for p in title_problems(long_title))
        assert TITLE_MIN == 14 and TITLE_MAX == 30


class TestToolChangeGate:
    def test_version_pricing_and_quota_changes_count(self):
        items = [
            NewsItem("某模型发布新版本", "https://a", description="v2 版本上线，额度从 50 提到 200"),
            NewsItem("某公司融资", "https://b", description="完成 B 轮"),
        ]
        assert has_tool_level_change(items)

    def test_pure_opinion_material_does_not_count(self):
        items = [
            NewsItem("AI 会取代谁", "https://a", description="一份关于未来工作的观察"),
            NewsItem("行业观察", "https://b", description="大家都在讨论智能体"),
        ]
        assert not has_tool_level_change(items)

    def test_empty_material_does_not_pass(self):
        assert not has_tool_level_change([])


class TestCopyableBlock:
    def _spec(self, blocks):
        return {"sections": [{"heading": "一", "blocks": blocks}]}

    def test_steps_block_counts(self):
        assert has_copyable_block(
            self._spec([{"type": "steps", "items": [{"title": "打开设置"}]}])
        )

    def test_three_item_list_counts(self):
        assert has_copyable_block(
            self._spec([{"type": "bullets", "items": ["a", "b", "c"]}])
        )

    def test_prose_only_does_not_count(self):
        assert not has_copyable_block(
            self._spec([{"type": "p", "text": "只有一段观点。"},
                        {"type": "bullets", "items": ["只有一条"]}])
        )
