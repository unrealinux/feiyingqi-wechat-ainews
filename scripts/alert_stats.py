#!/usr/bin/env python3
"""统计"为什么没稿"：按 kind 分桶，看闸门拦掉的频率。

用法：
    python scripts/alert_stats.py            # 全量
    python scripts/alert_stats.py --days 7   # 只看最近 7 天
"""

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

KIND_LABEL = {
    "gate_no_tool_change": "闸门：素材无工具级变化",
    "gate_title": "闸门：标题不合格（重写后仍不合格）",
    "gate_no_copyable": "闸门：缺可复制块",
    "ai_tone": "AI 味门禁拦截",
    "llm_bad_output": "LLM 输出坏了（JSON 语法错 / 被截断）",
    "wechat_ip": "微信 IP 白名单",
    "llm_unavailable": "LLM 不可用 / 未配置",
    "run_failed": "其它失败",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="只看最近 N 天（0=全部）")
    a = ap.parse_args()

    from src.monitoring import ALERT_LOG

    path = Path(ALERT_LOG)
    if not path.exists():
        print("还没有告警记录")
        return 0

    cutoff = datetime.now() - timedelta(days=a.days) if a.days else None
    per_kind, per_day = Counter(), Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = str(r.get("time", ""))
        if cutoff and ts[:19] and datetime.fromisoformat(ts[:19]) < cutoff:
            continue
        kind = r.get("kind") or "run_failed"  # 老记录没有 kind 字段
        per_kind[kind] += 1
        per_day[ts[:10]] += 1

    if not per_kind:
        print("窗口内没有告警")
        return 0

    print(f"{'原因':34} 次数")
    print("-" * 44)
    for kind, n in per_kind.most_common():
        print(f"{KIND_LABEL.get(kind, kind):34} {n}")
    print(f"{'合计':34} {sum(per_kind.values())}")
    print("\n按天：")
    for day in sorted(per_day):
        print(f"  {day}  {per_day[day]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
