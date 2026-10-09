#!/usr/bin/env python3
"""AI 味门禁观测报告：用真实分布决定阈值该不该调。

阈值 45 来自 Easel 的默认值，本仓库没有依据。跑几周后看这里：
拦截率过高（比如 >30%）= 阈值太严，天天没稿；接近 0 = 阈值没用上。

用法：
    python scripts/ai_gate_report.py
    python scripts/ai_gate_report.py --path logs/ai_gate.jsonl
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.monitoring import AI_GATE_LOG, read_ai_scores, summarize_ai_scores

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description="AI 味门禁观测报告")
    parser.add_argument("--path", default=str(AI_GATE_LOG), help="打分记录文件（JSONL）")
    args = parser.parse_args()

    records = read_ai_scores(Path(args.path))
    if not records:
        print(f"还没有记录（{args.path} 为空或不存在）。跑一次 python main.py daily 之后再来看。")
        return

    stats = summarize_ai_scores(records)
    print("=" * 56)
    print(f" AI 味门禁观测  —— {stats['total']} 次打分")
    print("=" * 56)
    print(f"拦截率 : {stats['block_rate']:.1%}  （{stats['blocked']}/{stats['total']}）")
    print(f"分数   : p50={stats['p50']}  p90={stats['p90']}  p99={stats['p99']}")

    by_source = {}
    for r in records:
        src = r.get("source", "?")
        b = by_source.setdefault(src, {"n": 0, "blocked": 0})
        b["n"] += 1
        b["blocked"] += 0 if r.get("passed", True) else 1
    for src, b in sorted(by_source.items()):
        print(f"  {src:12s} {b['n']:4d} 次，拦 {b['blocked']} 次")

    if stats["top_hits"]:
        print("-" * 56)
        print("最常被拦的命中项（改 prompt 就改这些）：")
        for word, count in stats["top_hits"]:
            print(f"  {count:3d}x  {word}")
    print("=" * 56)


if __name__ == "__main__":
    main()
