"""每日 16:00 的 WorkBuddy 稿：选题轮换与当日去重。

为什么要测：定时任务没人盯着跑，错了就是当天多一篇/重复一篇，事后才能发现。
两个纯函数（选题表、台账去重）先钉死，出稿与建草稿仍然靠 AI 味门禁兜住。
"""

import datetime
import sys
from pathlib import Path

import pytest

import src.monitoring as monitoring

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import gen_workbuddy_article as gw  # noqa: E402


def test_seven_presets_one_per_weekday():
    """一周七天各一个选题，否则必然出现“隔天重复同一套结构”。"""
    assert len(gw.PRESETS) == 7
    assert len({p["name"] for p in gw.PRESETS}) == 7
    assert len({p["cover_title"] for p in gw.PRESETS}) == 7
    for preset in gw.PRESETS:
        assert preset["chapters"], f"{preset['name']} 没有素材章节"
        assert preset["focus"].strip()


def test_preset_chapters_exist_or_skip_on_other_machines():
    """章节路径写错时静默跳过，正文就会用空素材出稿——这里钉住。"""
    if not gw.SKILL_DIR.exists():
        pytest.skip("本机没有装 workbuddy-guide 技能目录")
    missing = [
        rel for preset in gw.PRESETS for rel, _ in preset["chapters"]
        if not (gw.SKILL_DIR / rel).exists()
    ]
    assert not missing, f"技能目录里缺这些章节: {missing}"


def test_prefers_draft_box_over_ledger(monkeypatch):
    """用户手动删掉当天那篇后，不应该因为本地台账还记着就整天跳过。"""
    monkeypatch.setattr(gw, "_remote_material_titles", lambda _kw: [])
    monkeypatch.setattr(
        gw, "_ledger_material_titles", lambda _kw: ["WorkBuddy 已经删掉的稿"]
    )
    assert gw.material_titles_today("workbuddy") == []


def test_falls_back_to_ledger_when_box_unreadable(monkeypatch):
    monkeypatch.setattr(gw, "_remote_material_titles", lambda _kw: None)
    monkeypatch.setattr(gw, "_ledger_material_titles", lambda _kw: ["WorkBuddy 台账里的稿"])
    assert gw.material_titles_today("workbuddy") == ["WorkBuddy 台账里的稿"]


def test_ledger_filters_today_and_workbuddy(tmp_path, monkeypatch):
    ledger = tmp_path / "drafts.jsonl"
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(
        timespec="seconds"
    )
    ledger.write_text(
        "\n".join(
            [
                '{"time": "%s", "title": "WorkBuddy 昨天的稿", "media_id": "a"}'
                % yesterday,
                '{"time": "%s", "title": "词表越短，推理越快？", "media_id": "b"}'
                % datetime.datetime.now().isoformat(timespec="seconds"),
                '{"time": "%s", "title": "WorkBuddy 今天的稿", "media_id": "c"}'
                % datetime.datetime.now().isoformat(timespec="seconds"),
                "不是 JSON 的一行",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(monitoring, "DRAFT_LEDGER", ledger)

    assert gw._ledger_material_titles("WorkBuddy") == ["WorkBuddy 今天的稿"]


def test_titles_today_missing_ledger_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(monitoring, "DRAFT_LEDGER", tmp_path / "nope.jsonl")
    assert gw._ledger_material_titles("WorkBuddy") == []


def test_doubao_presets_all_exist_on_disk():
    """豆包那套选题的章节路径也要真的存在（路径写错 = 当天出不了稿）。"""
    missing = [
        rel for preset in gw.DOUBAO_PRESETS for rel, _ in preset["chapters"]
        if not (gw.references_dir("doubaowork") / rel).exists()
    ]
    assert not missing, f"豆包素材里缺这些章节: {missing}"


def test_material_spec_switches_presets_and_kicker():
    """--material 切换后，选题表与封面口径必须跟着换（否则豆包稿会署成蓝皮书）。"""
    wb, db = gw.material_spec("workbuddy"), gw.material_spec("doubaowork")
    assert wb["presets"] is gw.PRESETS and db["presets"] is gw.DOUBAO_PRESETS
    assert wb["name"] == "WorkBuddy" and db["name"] == "豆包工作"
    assert "蓝皮书" in wb["footer"] and "指南" in db["footer"]
    assert "蓝皮书" in gw.extra_instruction("workbuddy")
    assert "豆包工作实战指南" in gw.extra_instruction("doubaowork")
