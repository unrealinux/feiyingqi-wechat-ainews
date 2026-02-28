"""
Multi-Channel Publisher - 多渠道发布模块

支持：微信公众号、企业微信、钉钉、邮件等
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from typing import Optional, List
from pathlib import Path

from src.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PublisherBase(ABC):
    """发布渠道基类"""
    
    @abstractmethod
    def publish(self, title: str, content: str, **kwargs) -> bool:
        """发布内容"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """渠道名称"""
        pass


class WeChatPublisher(PublisherBase):
    """微信公众号发布"""
    
    def __init__(self):
        from src.publisher import WeChatPublisher as WeChatPub
        self.wechat = WeChatPub()
    
    def publish(self, title: str, content: str, **kwargs) -> bool:
        html_content = self.wechat.markdown_to_html(content)
        
        media_id = self.wechat.create_draft(
            title=title,
            content=html_content,
            author=kwargs.get("author", ""),
            digest=kwargs.get("digest", ""),
            cover_path=kwargs.get("cover_path", "")
        )
        
        if media_id and kwargs.get("auto_publish", False):
            return bool(self.wechat.publish_draft(media_id))
        
        return bool(media_id)
    
    def get_name(self) -> str:
        return "微信公众号"


class WeComPublisher(PublisherBase):
    """企业微信发布"""
    
    def __init__(self):
        config = load_config()
        wecom_config = config.get("wecom", {})
        
        self.corp_id = wecom_config.get("corp_id", "")
        self.corp_secret = wecom_config.get("corp_secret", "")
        self.agent_id = wecom_config.get("agent_id", "")
        self.enabled = bool(self.corp_id and self.corp_secret and self.agent_id)
    
    def publish(self, title: str, content: str, **kwargs) -> bool:
        if not self.enabled:
            logger.warning("WeCom not configured")
            return False
        
        try:
            import requests
            
            token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {"corpid": self.corp_id, "corpsecret": self.corp_secret}
            resp = requests.get(token_url, params=params, timeout=10)
            data = resp.json()
            
            if "access_token" not in data:
                logger.error(f"Failed to get WeCom token: {data}")
                return False
            
            access_token = data["access_token"]
            
            send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send"
            params = {"access_token": access_token}
            
            msg_content = f"{title}\n\n{content[:500]}..."
            
            data = {
                "touser": "@all",
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": msg_content}
            }
            
            resp = requests.post(send_url, params=params, json=data, timeout=10)
            result = resp.json()
            
            if result.get("errcode") == 0:
                logger.info("WeCom message sent")
                return True
            else:
                logger.error(f"WeCom send failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"WeCom error: {e}")
            return False
    
    def get_name(self) -> str:
        return "企业微信"


class DingTalkPublisher(PublisherBase):
    """钉钉发布"""
    
    def __init__(self):
        config = load_config()
        dingtalk_config = config.get("dingtalk", {})
        
        self.webhook = dingtalk_config.get("webhook", "")
        self.secret = dingtalk_config.get("secret", "")
        self.enabled = bool(self.webhook)
    
    def publish(self, title: str, content: str, **kwargs) -> bool:
        if not self.enabled:
            logger.warning("DingTalk not configured")
            return False
        
        try:
            import requests
            import hmac
            import hashlib
            import base64
            import urllib.parse
            import time
            
            timestamp = str(round(time.time() * 1000))
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, self.secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            
            url = f"{self.webhook}&timestamp={timestamp}&sign={sign}"
            
            markdown_content = f"## {title}\n\n{content[:1000]}"
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": markdown_content
                }
            }
            
            resp = requests.post(url, json=data, timeout=10)
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("DingTalk message sent")
                    return True
            
            logger.error(f"DingTalk send failed: {resp.text}")
            return False
            
        except Exception as e:
            logger.error(f"DingTalk error: {e}")
            return False
    
    def get_name(self) -> str:
        return "钉钉"


class EmailPublisher(PublisherBase):
    """邮件发布"""
    
    def __init__(self):
        config = load_config()
        email_config = config.get("email", {})
        
        self.smtp_host = email_config.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = email_config.get("smtp_port", 587)
        self.username = email_config.get("username", "")
        self.password = email_config.get("password", "")
        self.from_addr = email_config.get("from_addr", "")
        self.to_addrs = email_config.get("to_addrs", [])
        self.enabled = bool(self.username and self.password and self.to_addrs)
    
    def publish(self, title: str, content: str, **kwargs) -> bool:
        if not self.enabled:
            logger.warning("Email not configured")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = title
            msg['From'] = self.from_addr or self.username
            msg['To'] = ', '.join(self.to_addrs)
            
            text_content = content.replace('\n', '\n\n')
            html_content = self._convert_to_html(content)
            
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {len(self.to_addrs)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Email error: {e}")
            return False
    
    def _convert_to_html(self, content: str) -> str:
        html = content
        import re
        html = re.sub(r'^### (.*)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        html = re.sub(r'\n\n', '</p><p>', html)
        
        return f"""<html><body><p>{html}</p></body></html>"""
    
    def get_name(self) -> str:
        return "邮件"


class FilePublisher(PublisherBase):
    """文件导出"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def publish(self, title: str, content: str, **kwargs) -> bool:
        try:
            from datetime import datetime
            
            today = datetime.now().strftime("%Y%m%d")
            
            md_file = self.output_dir / f"article_{today}.md"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            html_file = self.output_dir / f"article_{today}.html"
            from src.publisher import WeChatPublisher
            wechat = WeChatPublisher()
            html_content = wechat.markdown_to_html(content)
            
            full_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px;}}</style>
</head><body>{html_content}</body></html>"""
            
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(full_html)
            
            logger.info(f"Files saved: {md_file.name}, {html_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"File save error: {e}")
            return False
    
    def get_name(self) -> str:
        return "本地文件"


class MultiPublisher:
    """多渠道发布管理器"""
    
    def __init__(self, channels: List[str] = None):
        self.channels = channels or ["file"]
        
        self.publishers = {
            "wechat": WeChatPublisher(),
            "wecom": WeComPublisher(),
            "dingtalk": DingTalkPublisher(),
            "email": EmailPublisher(),
            "file": FilePublisher(),
        }
    
    def publish(self, title: str, content: str, **kwargs) -> dict:
        """发布到所有启用的渠道"""
        results = {}
        
        for channel in self.channels:
            if channel in self.publishers:
                publisher = self.publishers[channel]
                try:
                    success = publisher.publish(title, content, **kwargs)
                    results[channel] = {
                        "success": success,
                        "name": publisher.get_name()
                    }
                    status = "✅" if success else "❌"
                    logger.info(f"{status} {publisher.get_name()}: {'成功' if success else '失败'}")
                except Exception as e:
                    results[channel] = {
                        "success": False,
                        "name": publisher.get_name(),
                        "error": str(e)
                    }
                    logger.error(f"❌ {publisher.get_name()}: {e}")
        
        return results
    
    def get_enabled_channels(self) -> List[str]:
        """获取已启用的渠道"""
        enabled = []
        for name, publisher in self.publishers.items():
            if hasattr(publisher, 'enabled'):
                if publisher.enabled:
                    enabled.append(name)
            else:
                enabled.append(name)
        return enabled


def publish_multi_channel(title: str, content: str, 
                         channels: List[str] = None,
                         **kwargs) -> dict:
    """便捷的多渠道发布函数"""
    publisher = MultiPublisher(channels)
    return publisher.publish(title, content, **kwargs)


if __name__ == "__main__":
    print("Testing Multi-Publisher...")
    
    publisher = MultiPublisher(["file"])
    
    result = publisher.publish(
        title="Test Article",
        content="# Hello World\n\nThis is a test."
    )
    
    print(f"\nResults: {result}")
