"""标题/正文错配检测。

2026-10-10 事故：复用 output/article_*.html 发草稿时，标题是手写的，正文已被
08:00 定时任务覆盖 → 草稿箱里标题是 GPT-5、正文是另一篇。这里用最小的检查兜住。
"""

from src.publisher import _title_not_in_body


def test_detects_title_from_another_article():
    body = "<p>当 AI 学会说 不，代价是什么？</p><p>安全冗余与效率革命的底层逻辑冲突</p>"

    assert _title_not_in_body("GPT-5 与 Claude 4 的分野 不是能力，是信任", body)


def test_title_found_in_body_is_fine():
    body = "<p>当 AI 学会说 不，代价是什么？</p><p>正文…</p>"

    assert not _title_not_in_body("当 AI 学会说 不，代价是什么？", body)


def test_title_ignores_markup_and_line_breaks():
    """draft_title() 会把手工断行合成一行，标题带空格/换行也算命中。"""
    body = "<h1>当 AI 学会说\n不，代价是什么？</h1>"

    assert not _title_not_in_body("当 AI 学会说 不，代价是什么？", body)


def test_empty_title_is_not_flagged():
    assert not _title_not_in_body("", "<p>任意正文</p>")
