#!/usr/bin/env bash
# Linux cron 入口：08:00 出新闻稿，15:00 出工具指南（两套社区素材隔天轮换）。
#
# AGENTS.md 红线：两条路径都只建草稿（create_draft），绝不群发。
# 日产上限读 scheduler.max_drafts_per_day，计数直接看 logs/drafts_created.jsonl
# （跟 main.py 内部的配额判断同一个来源，不再自己维护状态文件）。
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

hour="$(date '+%H')"
if [ "$hour" -lt 12 ]; then
    echo "== $(date '+%F %T') 08:00 档：新闻稿（今天第 $((done_today + 1)) / $max 篇）"
    "$PY" main.py daily
else
    # 15:00 档：工具指南。两套社区素材按当年第几天奇偶轮换，
    # 同一套至少隔一天，避免连着两天一个模样。
    if [ $(( 10#$(date '+%j') % 2 )) -eq 0 ]; then
        material="doubaowork"
    else
        material="workbuddy"
    fi
    echo "== $(date '+%F %T') 15:00 档：工具指南（$material，今天第 $((done_today + 1)) / $max 篇）"
    "$PY" scripts/gen_workbuddy_article.py --daily --material "$material"
fi

rc=$?
echo "== $(date '+%F %T') 结束 rc=$rc"
exit "$rc"
