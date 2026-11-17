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
