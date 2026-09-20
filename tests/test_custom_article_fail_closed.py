"""回归测试：custom_article 在 LLM 不可用时必须 fail-closed。

AGENTS.md 红线：禁止模板化洗稿。历史版本在每个 generate_* 末尾挂了
_get_*_template_article() 兜底（28 个同构模板），已整体移除。
本测试确保这个兜底不会以任何形式复活。
"""

import inspect
import re

import pytest

from src.custom_article import CustomArticleGenerator, generate_custom_article
from src.summarizer import LLMUnavailableError


ALL_GENERATORS = [
    "generate_note_tools_review",
    "generate_search_tools_review",
    "generate_code_tools_review",
    "generate_video_tools_review",
    "generate_audio_tools_review",
    "generate_office_tools_review",
    "generate_design_tools_review",
    "generate_marketing_tools_review",
    "generate_data_tools_review",
    "generate_education_tools_review",
    "generate_medical_tools_review",
    "generate_finance_tools_review",
    "generate_legal_tools_review",
    "generate_image_tools_review",
    "generate_meeting_tools_review",
]


def test_all_generators_still_exist():
    """15 个横评入口都还在（只是去掉了兜底）。"""
    for name in ALL_GENERATORS:
        assert callable(getattr(CustomArticleGenerator, name)), name


def test_each_generator_ends_with_fail_closed():
    """每个 generate_* 的最后一步必须是 raise，而不是 return 模板。"""
    for name in ALL_GENERATORS:
        src = inspect.getsource(getattr(CustomArticleGenerator, name))
        tail = [ln for ln in src.rstrip().splitlines() if ln.strip()]
        assert "raise LLMUnavailableError" in tail[-2] or "raise LLMUnavailableError" in tail[-3], (
            f"{name} 结尾没有 fail-closed：{tail[-2:]}"
        )


def test_no_template_fallback_method_left():
    """任何 _get_*template* 方法都不应存在。"""
    src = inspect.getsource(inspect.getmodule(CustomArticleGenerator))
    leftovers = re.findall(r"def (_get_\w*template\w*)", src)
    assert leftovers == [], f"发现残留的模板兜底方法: {leftovers}"


def test_raises_when_llm_unavailable(monkeypatch):
    """真实调用路径：LLM 全挂 → LLMUnavailableError，绝不返回预写模板。"""
    gen = CustomArticleGenerator()
    monkeypatch.setattr(gen.domestic_llm, "is_available", lambda: False)
    monkeypatch.setattr(gen.summarizer, "client", None)

    with pytest.raises(LLMUnavailableError):
        gen.generate_meeting_tools_review()


def test_convenience_function_fails_closed(monkeypatch):
    monkeypatch.setattr(
        CustomArticleGenerator,
        "__init__",
        lambda self: (
            setattr(self, "domestic_llm", type("D", (), {"is_available": lambda _s: False})()),
            setattr(self, "summarizer", type("S", (), {"client": None})()),
        )[-1],
    )
    with pytest.raises(LLMUnavailableError):
        generate_custom_article("meeting_tools_review")
