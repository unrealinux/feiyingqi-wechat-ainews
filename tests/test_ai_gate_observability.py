"""AI 味门禁的观测层：打分记入 JSONL，失败留本地告警底账。

没有配 webhook（FEISHU/SLACK/DINGTALK 都是空的），所以"今天为什么没稿"
只能靠这两个本地文件回答；阈值 45 也该由这里的真实分布来决定。
"""

import json

import pytest

import src.monitoring as monitoring
import src.publisher as publisher_module
from src.monitoring import read_ai_scores, record_ai_score, record_alert, summarize_ai_scores

from tests.test_ai_score_gate import AI_SLOP


def _report(score, phrases=(), vocab=()):
    return {"total_score": score, "hit_phrases": list(phrases), "hit_vocab": list(vocab)}


def test_score_records_round_trip(isolate_monitoring_logs):
    record_ai_score("publish_gate", "标题", _report(52.0, ["综上所述"], ["赋能"]), 45.0, False)
    record_ai_score("generation", "标题", _report(12.0), 45.0, True)

    records = read_ai_scores()

    assert [r["score"] for r in records] == [52.0, 12.0]
    assert records[0]["source"] == "publish_gate"
    assert records[0]["passed"] is False


def test_summarize_reports_block_rate_and_percentiles():
    records = [{"score": s, "passed": s < 45, "hit_phrases": ["综上所述"] if s >= 45 else [],
                "hit_vocab": ["赋能"] if s >= 45 else []}
               for s in (5, 10, 20, 30, 50, 60, 70, 80, 90, 95)]

    stats = summarize_ai_scores(records)

    assert stats["total"] == 10
    assert stats["blocked"] == 6
    assert stats["block_rate"] == 0.6
    assert stats["p50"] == 50.0
    assert stats["top_hits"][0] == ("综上所述", 6)


def test_summarize_handles_empty_input():
    stats = summarize_ai_scores([])

    assert stats["total"] == 0
    assert stats["block_rate"] == 0.0
    assert stats["p50"] is None


def test_corrupt_lines_are_skipped(isolate_monitoring_logs):
    monitoring.AI_GATE_LOG.write_text(
        '{"score": 10, "passed": true}\n不是 JSON\n{"score": 60, "passed": false}\n',
        encoding="utf-8",
    )

    assert len(read_ai_scores()) == 2


def test_recording_never_breaks_the_main_flow(tmp_path, monkeypatch):
    """观测写不进去（比如路径不可写）也不能让流水线挂掉。"""
    monkeypatch.setattr(monitoring, "AI_GATE_LOG", tmp_path / "nope" / "x.jsonl")
    (tmp_path / "nope").write_text("", encoding="utf-8")  # 目录位置被文件占了

    record_ai_score("generation", "标题", _report(10.0), 45.0, True)  # 不抛异常即通过


def test_alert_lands_in_the_local_ledger(isolate_monitoring_logs):
    record_alert("AI 味过重（56.0 >= 45.0）")

    line = (isolate_monitoring_logs / "alerts.jsonl").read_text(encoding="utf-8").strip()

    assert "AI 味过重" in json.loads(line)["reason"]


def test_publish_gate_writes_a_record(monkeypatch):
    """真实路径：发布层被拦时，观测文件里要留下证据。"""
    monkeypatch.setattr(
        publisher_module, "WeChatPublisher",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("应当被门禁拦住")),
    )

    assert publisher_module.publish_article(title="测试", content=AI_SLOP) is False

    records = read_ai_scores()
    assert len(records) == 1
    assert records[0]["source"] == "publish_gate"
    assert records[0]["passed"] is False
