#!/usr/bin/env python3
"""回采公众号后台数据（粉丝/阅读/分享/单篇表现），按天追加到 logs/wechat_stats.jsonl。

前提：先跑一次 `py scripts/weixin_mp_stats.py login`（管理员扫码），会话会持久化在
浏览器 profile 里；之后本脚本可无人值守运行。

用法：
    python scripts/fetch_mp_stats.py            # 回采并追加一条历史
    python scripts/fetch_mp_stats.py --dry-run  # 只看不写
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

HISTORY = ROOT / "logs" / "wechat_stats.jsonl"
MP_STATS = ROOT / "scripts" / "weixin_mp_stats.py"


def fetch() -> dict:
    """调 weixin_mp_stats stats，返回它吐的 JSON（失败抛 RuntimeError）。"""
    proc = subprocess.run(
        [sys.executable, str(MP_STATS), "stats"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        cwd=str(ROOT),
    )
    out = (proc.stdout or "").strip()
    start = out.find("{")
    if start == -1:
        raise RuntimeError(f"stats 没有返回 JSON: {out[:200]} {proc.stderr[:200]}")
    data = json.loads(out[start:])
    if not data.get("loggedIn"):
        raise RuntimeError(f"未登录或会话失效: {data.get('error') or data}")
    return data


def summarize(data: dict) -> dict:
    period = data.get("period_metrics") or {}
    week = {m["label"]: m["value"] for m in period.get("week") or []}
    month = {m["label"]: m["value"] for m in period.get("month") or []}
    notes = [
        {"title": n.get("title", "")[:40], "stat": n.get("stat", "")}
        for n in (data.get("notes") or [])[:10]
    ]
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().isoformat(timespec="seconds"),
        "nickname": data.get("nickname"),
        "followers": data.get("followers"),
        "reads_week": week.get("阅读人数"),
        "reads_month": month.get("阅读人数"),
        "shares_month": month.get("分享次数"),
        "notes": notes,
        "error": data.get("error"),
    }


def main():
    parser = argparse.ArgumentParser(description="回采公众号后台数据")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写历史")
    args = parser.parse_args()

    try:
        data = fetch()
    except Exception as e:
        print(f"回采失败: {e}")
        return 1

    snap = summarize(data)
    print(f"账号: {snap['nickname']} | 粉丝: {snap['followers']}")
    print(f"近 7 天阅读 {snap['reads_week']} | 近 30 天阅读 {snap['reads_month']} | 30 天分享 {snap['shares_month']}")
    print("近期单篇：")
    for n in snap["notes"]:
        print(f"  {n['stat']:14s} {n['title']}")
    if snap.get("error"):
        print(f"提示: {snap['error']}")

    if args.dry_run:
        return 0
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")
    print(f"已追加历史: {HISTORY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
