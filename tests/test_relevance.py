"""素材相关性筛选：AI 无关的热搜不能进 prompt。

2026-11-17 的实测问题：百度热搜是通用榜，素材里混进"养老金要崩盘""伊朗最高
领袖"，20 条里一半跟 AI 无关——既稀释选题（模型爱写"三款模型并列"），
也白烧 prompt token。
"""

from src.fetcher import NewsItem
from src.relevance import is_ai_related, select_relevant


def _item(title, desc=""):
    return NewsItem(title, "https://example.com/x", "测试", desc)


class TestIsAiRelated:
    def test_ai_items_match(self):
        for title in (
            "OpenAI 发布 GPT-6.2",
            "国产大模型开源了新版本",
            "Cursor 更新后怎么接回本地工作流",
            "算力租赁价格又涨了",
            "英伟达下一代 GPU 出货",
        ):
            assert is_ai_related(_item(title)), title

    def test_general_hot_search_does_not_match(self):
        for title in (
            "养老金要崩盘？有压力≠会崩盘",
            "东北糖葫芦已进化到巨无霸版本",
            "伊朗最高领袖下令结束非战非和状态",
        ):
            assert not is_ai_related(_item(title)), title

    def test_description_also_counts(self):
        assert is_ai_related(_item("某公司新动作", "推出自己的大模型服务"))


class TestSelectRelevant:
    def test_drops_noise_and_caps(self):
        items = [_item(f"AI 新闻 {i}") for i in range(5)]
        items += [_item("养老金要崩盘"), _item("糖葫芦涨价")]
        kept = select_relevant(items, limit=3)
        assert len(kept) == 3
        assert all("AI 新闻" in x.title for x in kept)

    def test_falls_back_when_nothing_matches(self):
        """词表漏了也要有素材——不能因为过滤把当天搞成零素材。"""
        items = [_item("某个完全陌生的领域"), _item("另一条")]
        assert len(select_relevant(items, limit=8)) == 2

    def test_empty_input(self):
        assert select_relevant([], limit=8) == []


def test_real_2026_11_17_misses_are_fixed():
    """实测漏掉的两条：公司名/术语不在词表里，会把真 AI 新闻筛掉。"""
    assert is_ai_related(_item("绿电进Token出！联想重新定义词元工厂"))
    assert is_ai_related(_item("Anthropic 上市，三个预测"))
