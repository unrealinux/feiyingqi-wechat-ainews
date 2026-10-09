"""生成端 AI 味重试：不合格就带着命中词重写一次；两次都不合格则 fail-closed。

发布层（src/publisher.py）已经有一道门禁，但那是"写完打回"。这里测的是上游：
让模型在第一遍就被要求改，而不是等发布时才发现。
"""

from types import SimpleNamespace

import pytest

from src.fetcher import NewsItem
from src.summarizer import LLMUnavailableError, Summarizer, ThinMaterialError


SLOP = "首先，赋能生态。其次，打造闭环链路。最后，综上所述，这件事具有深远的意义。"
HUMAN = (
    "上午 10 点，我把同一个问题问了两遍。答案不一样。第一遍说 3 天，第二遍说一周。"
    "差别在哪？我把两段输出并排贴出来，发现它把时区算错了。就这一处。改完再跑，答案对上了。"
)


def _spec(paragraph: str) -> dict:
    return {
        "meta_line": "2026年1月1日 ｜ 测试",
        "title": "测试标题",
        "subtitle": "副标题",
        "lead": [paragraph, paragraph],
        "sections": [
            {"heading": "第一节", "accent": "red",
             "blocks": [{"type": "p", "text": paragraph}, {"type": "p", "text": paragraph}]},
            {"heading": "第二节", "accent": "green", "blocks": [{"type": "p", "text": paragraph}]},
            {"heading": "第三节", "accent": "red", "blocks": [{"type": "p", "text": paragraph}]},
        ],
        "closing": [paragraph, paragraph],
        "sources": ["1. 机构《标题》 https://example.com/a",
                    "2. 机构《标题》 https://example.com/b"],
    }


class FakeClient:
    """按顺序吐 spec 的假 LLM，同时记录每次收到的 user_prompt。"""

    def __init__(self, payloads):
        self._payloads = payloads
        self.prompts = []
        self.temperatures = []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.prompts.append(kwargs["messages"][-1]["content"])
        self.temperatures.append(kwargs["temperature"])
        payload = self._payloads[min(len(self.prompts) - 1, len(self._payloads) - 1)]
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=_json(payload)))]
        )


def _json(payload) -> str:
    import json
    return json.dumps(payload, ensure_ascii=False)


@pytest.fixture()
def summarizer():
    s = Summarizer()
    s.model = "test-model"
    return s


def _news():
    return [NewsItem(title="某模型发布", url="https://example.com/n",
                     source="Example",
                     description="该模型推理速度提升 37%，训练用了 12000 张卡。")]


def test_sloppy_first_draft_is_rewritten_with_feedback(summarizer):
    summarizer.client = FakeClient([_spec(SLOP), _spec(HUMAN)])

    spec = summarizer.generate_editorial_spec(_news(), allow_mock=False)

    assert len(summarizer.client.prompts) == 2, "第一稿 AI 味过重应触发一次重写"
    assert "AI 味过重" in summarizer.client.prompts[1], "重写提示里要带上被拦的原因"
    assert "赋能" in summarizer.client.prompts[1], "重写提示里要列出行命中词"
    assert "37%" in summarizer.client.prompts[1], "重写提示里要带上素材里的具体事实"
    assert "12000" in summarizer.client.prompts[1], (
        "AI 味高的常见根因是没细节可写，重写时要喂素材里现成的数字"
    )
    assert summarizer.client.temperatures[1] > summarizer.client.temperatures[0], (
        "AI 味重写要放开温度，否则同一模型只会再写一遍同款套话"
    )
    assert spec["lead"][0] == HUMAN


def test_fail_closed_when_both_drafts_are_sloppy(summarizer):
    summarizer.client = FakeClient([_spec(SLOP), _spec(SLOP)])

    # 两稿都是 AI 味 → 报 ThinMaterialError（素材没有细节可写），
    # 调度层据此补抓素材重试，而不是把同一份素材再重写第三次。
    with pytest.raises(ThinMaterialError):
        summarizer.generate_editorial_spec(_news(), allow_mock=False)

    assert len(summarizer.client.prompts) == 2, "重试次数封顶 2 次，不能无限重写"
