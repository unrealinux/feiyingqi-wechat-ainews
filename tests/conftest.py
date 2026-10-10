"""共用 fixture：测试绝不允许把观测/告警记录写进仓库的 logs/。"""

import pytest


@pytest.fixture(autouse=True)
def isolate_monitoring_logs(tmp_path, monkeypatch):
    """把 AI 味打分记录和告警底账重定向到 tmp_path，返回该目录。"""
    from src import monitoring

    monkeypatch.setattr(monitoring, "AI_GATE_LOG", tmp_path / "ai_gate.jsonl")
    monkeypatch.setattr(monitoring, "ALERT_LOG", tmp_path / "alerts.jsonl")
    return tmp_path


@pytest.fixture(autouse=True, scope="session")
def ensure_config_yaml():
    """检出里没有 config.yaml 时，从 config.yaml.example 生成一份。

    为什么需要：config.yaml 在 .gitignore 里（里面有真实密钥），所以 CI 的检出
    从来就没有它，而一批测试会 `load_config()` 去读默认路径 —— 结果是
    「只有写代码那台机器上能过」：CI 上 19 failed / 12 errors，全部是
    FileNotFoundError: Config file not found: config.yaml。

    只在**缺失时**创建，绝不覆盖已有文件（本地那份带真实凭据）；
    跑完把这次创建的删掉，免得留下一个容易和真配置混淆的副本。
    """
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent
    target = root / "config.yaml"
    example = root / "config.yaml.example"

    created = False
    if not target.exists() and example.exists():
        target.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        created = True
    try:
        yield target
    finally:
        if created and target.exists():
            target.unlink()
