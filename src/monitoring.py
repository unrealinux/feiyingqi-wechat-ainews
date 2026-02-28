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
                "attachments": [{
                    "color": color,
                    "title": title,
                    "text": message,
                    "footer": "AI News Publisher",
                    "ts": int(time.time())
                }]
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
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": color
                    },
                    "elements": [{
                        "tag": "markdown",
                        "content": message[:500]
                    }]
                }
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
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, 
                 password: str, from_addr: str, to_addrs: List[str]):
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
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = title
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            
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
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
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
