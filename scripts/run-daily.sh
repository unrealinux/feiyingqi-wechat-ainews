#!/usr/bin/env bash
# Linux cron 入口：按 config.yaml 的 scheduler.interval_days 间隔跑一次 main.py daily。
#
# AGENTS.md 红线：只建草稿（main.py daily -> create_draft），绝不群发。
# 间隔由脚本自己管（cron 只负责每天叫醒它），避免"每天一篇"把号发废。
#
# crontab: 0 8 * * * /home/xieyingfei/文档/feiyingqi-wechat-ainews/scripts/run-daily.sh
set -u

cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
exec >> logs/daily.log 2>&1

PY=".venv/bin/python"
STATE="logs/.last-daily-run"

if [ ! -f config.yaml ] || [ ! -f .env ]; then
    echo "== $(date '+%F %T') 跳过：缺 config.yaml 或 .env（微信凭据 / LLM key）"
    exit 1
fi

# 间隔：scheduler.interval_days，缺省 2 天
interval="$(sed -n '/^scheduler:/,/^[^[:space:]#]/p' config.yaml | sed -n 's/^[[:space:]]*interval_days:[[:space:]]*\([0-9]\+\).*/\1/p' | head -1)"
interval="${interval:-2}"

if [ -f "$STATE" ]; then
    last="$(cat "$STATE")"
    elapsed=$(( ( $(date +%s) - $(date -d "$last" +%s 2>/dev/null || echo 0) ) / 86400 ))
    if [ "$elapsed" -lt "$interval" ]; then
        echo "== $(date '+%F %T') 跳过：上次成功是 $last（间隔 ${interval} 天）"
        exit 0
    fi
fi

echo "== $(date '+%F %T') 开始 main.py daily"
"$PY" main.py daily
rc=$?
echo "== $(date '+%F %T') 结束 rc=$rc"
[ "$rc" -eq 0 ] && date '+%F %T' > "$STATE"
exit "$rc"
