"""共用 fixture：测试绝不允许把观测/告警记录写进仓库的 logs/。"""

import pytest


@pytest.fixture(autouse=True)
def isolate_monitoring_logs(tmp_path, monkeypatch):
    """把 AI 味打分记录和告警底账重定向到 tmp_path，返回该目录。"""
    from src import monitoring

    monkeypatch.setattr(monitoring, "AI_GATE_LOG", tmp_path / "ai_gate.jsonl")
    monkeypatch.setattr(monitoring, "ALERT_LOG", tmp_path / "alerts.jsonl")
    return tmp_path
