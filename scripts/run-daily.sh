#!/usr/bin/env bash
# Linux cron 入口：每天按 scheduler.max_drafts_per_day 的日产上限跑 main.py daily。
#
# AGENTS.md 红线：只建草稿（main.py daily -> create_draft），绝不群发。
# 时点由 cron 决定（crontab: 0 8,15 * * *）；这里只负责"今天够数了就不再跑"。
#
# 计数直接读 logs/drafts_created.jsonl（跟 main.py 内部的配额判断同一个来源），
# 不再自己维护状态文件——两套计数会漂移（2026-11-11 实测就漂了一次）。
#
# crontab: 0 8,15 * * * /home/xieyingfei/文档/feiyingqi-wechat-ainews/scripts/run-daily.sh
set -u

cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
exec >> logs/daily.log 2>&1

PY=".venv/bin/python"
LEDGER="logs/drafts_created.jsonl"

if [ ! -f config.yaml ] || [ ! -f .env ]; then
    echo "== $(date '+%F %T') 跳过：缺 config.yaml 或 .env（微信凭据 / LLM key）"
    exit 1
fi

# 日产上限：scheduler.max_drafts_per_day，缺省 1（AGENTS.md 的默认约束）
max="$(sed -n '/^scheduler:/,/^[^[:space:]#]/p' config.yaml | sed -n 's/^[[:space:]]*max_drafts_per_day:[[:space:]]*\([0-9]\+\).*/\1/p' | head -1)"
max="${max:-1}"

today="$(date '+%F')"
done_today=0
if [ -f "$LEDGER" ]; then
    done_today="$(grep -c "\"time\": \"$today" "$LEDGER" 2>/dev/null || true)"
    done_today="${done_today:-0}"
fi

if [ "$done_today" -ge "$max" ]; then
    echo "== $(date '+%F %T') 跳过：今天已产出 $done_today 篇（上限 $max）"
    exit 0
fi

echo "== $(date '+%F %T') 开始 main.py daily（今天第 $((done_today + 1)) / $max 篇）"
"$PY" main.py daily
rc=$?
echo "== $(date '+%F %T') 结束 rc=$rc"
exit "$rc"
