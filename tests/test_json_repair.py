"""模型吐出来的 JSON 不合法时：先修，修不好再带着错误原因重写。

2026-10-28 16:00 定时任务：agnes 连续两次返回坏 JSON（尾随逗号 / 多余换行），
两次都被判「JSON 解析失败」，当天下午那篇没生成。这里把两类补救钉住。
"""

from types import SimpleNamespace

import pytest

from src.editorial_template import extract_json
from src.fetcher import NewsItem
from src.summarizer import LLMUnavailableError, Summarizer


def test_trailing_comma_is_repaired():
    assert extract_json('{"a": 1, "b": [1, 2,], }') == {"a": 1, "b": [1, 2]}


def test_raw_newline_inside_string_is_tolerated():
    assert extract_json('{"a": "第一行\n第二行"}')["a"] == "第一行\n第二行"


def test_normal_comma_is_not_eaten():
    """修尾随逗号不能误伤正常分隔符（", " 后面跟键名）。"""
    assert extract_json('{"a": 1, "b": "x, y"}') == {"a": 1, "b": "x, y"}


def test_broken_json_still_raises():
    with pytest.raises(Exception, match="JSON 解析失败"):
        extract_json('{"a" 1}')


class _RawClient:
    """按顺序返回原始文本（含坏 JSON），记录每次的 user_prompt。"""

    def __init__(self, raws):
        self._raws = raws
        self.prompts = []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.prompts.append(kwargs["messages"][-1]["content"])
        idx = min(len(self.prompts) - 1, len(self._raws) - 1)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self._raws[idx]))]
        )


GOOD_SPEC = (
    '{"meta_line":"2026年1月1日 ｜ 测试","title":"测试标题","subtitle":"副标题",'
    '"lead":["上午 10 点我把同一个问题问了两遍。答案不一样。","第一遍说 3 天，第二遍说一周。"],'
    '"sections":[{"heading":"第一节","accent":"red","blocks":[{"type":"p","text":"就这一处。"}]},'
    '{"heading":"第二节","accent":"green","blocks":[{"type":"p","text":"改完再跑。"}]},'
    '{"heading":"第三节","accent":"red","blocks":[{"type":"p","text":"答案对上了。"}]}],'
    '"closing":["差别在哪？","我把两段输出并排贴出来。"],'
    '"sources":["1. 机构《标题》 https://example.com/a","2. 机构《标题》 https://example.com/b"]}'
)


def test_bad_json_gets_the_parse_error_as_feedback(monkeypatch):
    """第二稿必须被告知"上一稿不是合法 JSON"，否则只会原样再错一次。"""
    summarizer = Summarizer()
    summarizer.model = "test-model"
    summarizer.client = _RawClient(['{"a" 1}', GOOD_SPEC])

    spec = summarizer.generate_editorial_spec(
        [NewsItem(title="t", url="https://example.com/n", source="s", description="d")],
        allow_mock=False,
    )

    assert spec["title"] == "测试标题"
    assert len(summarizer.client.prompts) == 2
    assert "不是合法 JSON" in summarizer.client.prompts[1]


def test_two_bad_jsons_fail_closed():
    summarizer = Summarizer()
    summarizer.model = "test-model"
    summarizer.client = _RawClient(['{"a" 1}', '{"b" 2}'])

    with pytest.raises(LLMUnavailableError):
        summarizer.generate_editorial_spec(
            [NewsItem(title="t", url="https://example.com/n", source="s", description="d")],
            allow_mock=False,
        )
