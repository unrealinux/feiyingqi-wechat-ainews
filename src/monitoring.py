"""
Monitoring & Alerts - 监控告警模块

支持：飞书、Slack、邮件通知
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional, List
from abc import ABC, abstractmethod
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 本地观测文件：不依赖任何外部 webhook（当前 FEISHU/SLACK/DINGTALK 都没配，
# 告警默认发不出去）。写文件是零配置、事后可查的那一层。
AI_GATE_LOG = Path("logs/ai_gate.jsonl")
ALERT_LOG = Path("logs/alerts.jsonl")


def _append_jsonl(path: Path, record: Dict) -> None:
    """追加一行 JSON。观测不能反过来搞挂主流程，所以任何异常都只记 warning。"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"写入 {path} 失败（不影响主流程）: {e}")


def record_ai_score(
    source: str, title: str, report: Dict, threshold: float, passed: bool
) -> None:
    """记录每次 AI 味打分。

    threshold=45 是 Easel 拍的默认值，本仓库没有依据。攒够真实分布后用
    scripts/ai_gate_report.py 看拦截率和分位数，再决定该不该调。
    """
    _append_jsonl(
        AI_GATE_LOG,
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "source": source,
            "title": title[:80],
            "score": report.get("total_score"),
            "threshold": threshold,
            "passed": passed,
            "hit_phrases": report.get("hit_phrases", []),
            "hit_vocab": report.get("hit_vocab", []),
        },
    )


def read_ai_scores(path: Optional[Path] = None) -> List[Dict]:
    """读回历史打分记录（文件不存在/单行损坏都不报错）。"""
    path = path or AI_GATE_LOG
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def summarize_ai_scores(records: List[Dict]) -> Dict:
    """给阈值决策用的汇总：拦截率 / 分位数 / 最常命中的词。"""
    scores = sorted(
        r["score"] for r in records if isinstance(r.get("score"), (int, float))
    )
    blocked = [r for r in records if not r.get("passed", True)]
    hits: Dict[str, int] = {}
    for r in blocked:
        for word in list(r.get("hit_phrases", [])) + list(r.get("hit_vocab", [])):
            hits[word] = hits.get(word, 0) + 1
    return {
        "total": len(records),
        "blocked": len(blocked),
        "block_rate": round(len(blocked) / len(records), 3) if records else 0.0,
        "p50": _percentile(scores, 50),
        "p90": _percentile(scores, 90),
        "p99": _percentile(scores, 99),
        "top_hits": sorted(hits.items(), key=lambda kv: -kv[1])[:10],
    }


def _percentile(sorted_values: List[float], pct: float) -> Optional[float]:
    if not sorted_values:
        return None
    idx = min(
        len(sorted_values) - 1, int(round((pct / 100) * (len(sorted_values) - 1)))
    )
    return round(float(sorted_values[idx]), 1)


def record_alert(reason: str) -> None:
    """本地告警底账：webhook 没配时，这是唯一能事后查到"今天为什么没稿"的地方。"""
    _append_jsonl(
        ALERT_LOG,
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "reason": reason[:500],
        },
    )
    logger.error(f"[ALERT] 今日未产出：{reason}")


class NotificationChannel(ABC):
    """通知渠道基类"""

    @abstractmethod
    def send(self, title: str, message: str, **kwargs) -> bool:
        pass


class SlackNotifier(NotificationChannel):
    """Slack 通知"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, title: str, message: str, **kwargs) -> bool:
        try:
            import requests

            color = kwargs.get("color", "good" if "成功" in message else "warning")

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "AI News Publisher",
                        "ts": int(time.time()),
                    }
                ]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Slack notification sent: {title}")
                return True
            else:
                logger.error(f"Slack error: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False


class FeishuNotifier(NotificationChannel):
    """飞书通知"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, title: str, message: str, **kwargs) -> bool:
        try:
            import requests

            color = "green" if "成功" in message or "✅" in message else "red"

            payload = {
                "msg_type": "interactive_card",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": title},
                        "template": color,
                    },
                    "elements": [{"tag": "markdown", "content": message[:500]}],
                },
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    logger.info(f"Feishu notification sent: {title}")
                    return True

            logger.error(f"Feishu error: {response.text}")
            return False

        except Exception as e:
            logger.error(f"Feishu notification failed: {e}")
            return False


class EmailNotifier(NotificationChannel):
    """邮件通知"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_addr: str,
        to_addrs: List[str],
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr or username
        self.to_addrs = to_addrs

    def send(self, title: str, message: str, **kwargs) -> bool:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = title
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            html_content = f"""
            <html>
            <body>
                <h2>{title}</h2>
                <pre style="font-family: monospace; background: #f5f5f5; padding: 10px;">{message}</pre>
                <p style="color: #666; font-size: 12px;">
                    Sent by AI News Publisher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
            </html>
            """

            msg.attach(MIMEText(message, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email notification sent: {title}")
            return True

        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False


class Monitor:
    """监控管理器"""

    def __init__(self):
        from src.config_secure import get_monitoring_config, load_env

        load_env()

        self.config = get_monitoring_config()
        self.channels = []
        self._init_channels()

    def _init_channels(self):
        """初始化通知渠道"""
        if not self.config.get("enabled"):
            logger.info("Monitoring is disabled")
            return

        if self.config.get("slack_webhook"):
            self.channels.append(SlackNotifier(self.config["slack_webhook"]))
            logger.info("Slack notifier initialized")

        if self.config.get("feishu_webhook"):
            self.channels.append(FeishuNotifier(self.config["feishu_webhook"]))
            logger.info("Feishu notifier initialized")

    def notify_success(self, title: str, message: str, **kwargs):
        """发送成功通知"""
        if not self.config.get("enabled") or not self.config.get("notify_on_success"):
            return

        full_title = f"✅ {title}"

        for channel in self.channels:
            try:
                channel.send(full_title, message, **kwargs)
            except Exception as e:
                logger.error(f"Notification failed: {e}")

    def notify_error(self, title: str, message: str, **kwargs):
        """发送错误通知"""
        if not self.config.get("enabled") or not self.config.get("notify_on_error"):
            return

        full_title = f"❌ {title}"

        for channel in self.channels:
            try:
                channel.send(full_title, message, color="danger", **kwargs)
            except Exception as e:
                logger.error(f"Notification failed: {e}")

    def notify_info(self, title: str, message: str, **kwargs):
        """发送普通通知"""
        if not self.config.get("enabled"):
            return

        for channel in self.channels:
            try:
                channel.send(title, message, **kwargs)
            except Exception as e:
                logger.error(f"Notification failed: {e}")


def send_run_notification(status: str, details: Dict):
    """发送运行通知"""
    monitor = Monitor()

    if status == "success":
        message = f"""
📊 运行详情：
- 获取新闻: {details.get('news_count', 0)} 条
- 文章字数: {details.get('word_count', 0)} 字
- 发布渠道: {details.get('channels', 'file')}
- 耗时: {details.get('elapsed', 0):.1f}s
- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        monitor.notify_success("AI News Publisher 运行成功", message)

    elif status == "error":
        message = f"""
❌ 错误信息: {details.get('error', 'Unknown error')}
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        monitor.notify_error("AI News Publisher 运行失败", message)


def quick_test():
    """快速测试通知"""
    print("Testing notifications...")

    monitor = Monitor()

    monitor.notify_info("Test", "This is a test notification")
    print("Test notification sent (if configured)")


if __name__ == "__main__":
    quick_test()
