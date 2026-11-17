"""告警分桶：闸门拦稿、IP 白名单、LLM 挂掉必须能分开统计。

2026-11-16 加的三条生成闸门会主动"拒绝出稿"，如果不分类，日志里就会和
网络失败混在一起，看不出到底是被规则拦掉还是真出了问题。
"""

import json

from src import monitoring
from src.scheduler import failure_kind


class TestFailureKind:
    def test_gate_reasons_have_their_own_buckets(self):
        cases = [
            ("素材里没有工具级变化（版本/定价/额度/权限/用法），本次不写趋势稿",
             "gate_no_tool_change"),
            ("结构化内容生成失败: 标题不合格：长度 31 字，要求 14–30", "gate_title"),
            ("结构化内容生成失败: 缺少可复制块：至少要一个 steps 块", "gate_no_copyable"),
        ]
        for reason, want in cases:
            assert failure_kind(reason) == want, reason

    def test_infra_failures_are_not_mixed_with_gates(self):
        assert failure_kind("获取 access_token 失败: invalid ip 1.2.3.4") == "wechat_ip"
        assert failure_kind("LLM 客户端不可用（未配置 API Key）") == "llm_unavailable"
        assert failure_kind("AI 味过重（56.0 >= 45.0）") == "ai_tone"
        assert failure_kind(
            "结构化内容生成失败: JSON 解析失败: Expecting ':' delimiter"
        ) == "llm_bad_output"
        assert failure_kind("结构化内容生成失败: 上一稿被截断（5900 字符就到底了）") == "llm_bad_output"
        assert failure_kind("发布步骤返回失败") == "run_failed"


class TestRecordAlert:
    def test_kind_is_persisted(self, isolate_monitoring_logs):
        monitoring.record_alert("素材里没有工具级变化", kind="gate_no_tool_change")

        line = monitoring.ALERT_LOG.read_text(encoding="utf-8").strip().splitlines()[-1]
        record = json.loads(line)
        assert record["kind"] == "gate_no_tool_change"
        assert "工具级变化" in record["reason"]

    def test_kind_defaults_when_omitted(self, isolate_monitoring_logs):
        monitoring.record_alert("随便什么失败")

        record = json.loads(
            monitoring.ALERT_LOG.read_text(encoding="utf-8").strip().splitlines()[-1]
        )
        assert record["kind"] == "run_failed"


class TestEgressIpRecording:
    """IP 漂移要能从告警底账里看出来：白名单拒绝时把当前出口 IP 记进去。"""

    def test_extract_ip_from_wechat_error(self):
        from src.netinfo import extract_ip

        msg = (
            "获取 access_token 失败: invalid ip 183.202.137.105 "
            "ipv6 ::ffff:183.202.137.105, not in whitelist rid: 6af653ac"
        )
        assert extract_ip(msg) == "183.202.137.105"
        assert extract_ip("没有 IP 的消息") == ""

    def test_preflight_blocks_run_and_records_ip(self):
        """token 探不通时：不出稿、不花 LLM 的钱，告警里带 IP。"""
        from unittest.mock import patch

        from src.scheduler import run_once

        err = "invalid ip 1.2.3.4 ipv6 ::ffff:1.2.3.4, not in whitelist"
        with patch("src.publisher.count_drafts_created_today", return_value=0), \
             patch("src.config.load_config", return_value={"scheduler": {}}), \
             patch("src.netinfo.probe_token", return_value=(None, err)), \
             patch("src.fetcher.fetch_news") as m_fetch, \
             patch("src.publisher.publish_article") as m_publish, \
             patch("src.monitoring.send_run_notification") as m_notify:
            result = run_once()

        assert result is False
        self_fetch_called = m_fetch.called
        assert not self_fetch_called, "token 都拿不到，不该再抓素材"
        assert not m_publish.called
        status, details = m_notify.call_args.args
        assert status == "error"
        assert "1.2.3.4" in details["error"]
        assert failure_kind(details["error"]) == "wechat_ip"
