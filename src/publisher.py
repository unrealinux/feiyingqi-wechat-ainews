"""
WeChat Publisher - 微信公众号发布模块

支持 Markdown 转 HTML、草稿创建、自动发布
参考 feiqingqiWechatMP 优化，集成代理支持和配置验证
"""

import os
import re
import json
import time
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.config import load_config, get_wechat_config, get_publish_config
from src.proxy import get_requests_proxy, is_proxy_enabled
from src.validate_config import validate_config, ValidationErrorType
from src.errors import with_retry, AppError, ErrorType
from src.health import inc_published, inc_publish_failure

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class WeChatPublisher:
    """微信公众号发布器"""
    
    def __init__(self):
        config = load_config()
        wechat_config = get_wechat_config(config)
        publish_config = get_publish_config(config)
        
        self.app_id = wechat_config.get("app_id", "")
        self.app_secret = wechat_config.get("app_secret", "")
        self.author = publish_config.get("author", "AI 前沿观察")
        self.default_cover = publish_config.get("default_cover", "")
        self.default_digest = publish_config.get("default_digest", "")
        
        self.access_token = None
        self.token_expires_at = 0
        
        # 代理配置
        self.proxies = get_requests_proxy()
        self.use_proxy = is_proxy_enabled()
        
        # 配置验证
        self._validate_config()
        
        # 健康监控
        self._health_checker = None
        try:
            import src.health as health_module
            self._health_checker = health_module.get_health_checker()
        except (ImportError, AttributeError):
            pass
    
    def _validate_config(self):
        """验证配置"""
        validation_result = validate_config(load_config())
        
        if not validation_result["valid"]:
            logger.warning(f"配置验证失败: {validation_result['error_count']} 个错误")
            for error in validation_result["errors"]:
                if error.field.startswith("wechat"):
                    logger.error(f"微信配置错误: {error.message}")
        
        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                logger.info(f"配置警告: {warning.message}")
    
    def get_access_token(self) -> Optional[str]:
        """获取访问令牌（带缓存和重试）"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }
        
        @with_retry(max_retries=2, delay=1.0)
        def _fetch_token():
            # 使用代理
            proxies = self.proxies if self.use_proxy else {}
            
            response = requests.get(url, params=params, timeout=10, proxies=proxies)
            data = response.json()
            
            if "access_token" in data:
                return data
            else:
                error_msg = data.get("errmsg", "Unknown error")
                error_code = data.get("errcode", -1)
                raise AppError(
                    f"获取 access_token 失败: {error_msg}",
                    error_type=ErrorType.AUTH,
                    context={"error_code": error_code}
                )
        
        try:
            data = _fetch_token()
            self.access_token = data["access_token"]
            expires_in = data.get("expires_in", 7200)
            self.token_expires_at = time.time() + expires_in - 300
            logger.info("Access token refreshed")
            return self.access_token
        except AppError as e:
            logger.error(f"获取 access_token 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取 access_token 异常: {e}")
            return None
    
    def create_draft(self, title: str, content: str, author: str = "", 
                    digest: str = "", cover_path: str = "") -> Optional[str]:
        """创建草稿（带代理支持和重试）"""
        token = self.get_access_token()
        if not token:
            logger.error("Failed to get access token")
            return None
        
        # 记录标题和作者长度，用于调试
        final_author = author or self.author
        logger.info(f"Creating draft with title: '{title}' (length: {len(title)})")
        logger.info(f"Creating draft with author: '{final_author}' (length: {len(final_author)})")
        
        article = {
            "title": title,
            "author": final_author,
            "content": content,
            "digest": digest or self.default_digest,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }
        
        # 处理封面图
        if cover_path and os.path.exists(cover_path):
            media_id = self._upload_media(cover_path, "image")
            if media_id:
                article["thumb_media_id"] = media_id
        
        # 如果没有有效的thumb_media_id，使用默认封面
        if "thumb_media_id" not in article:
            default_cover_path = self.default_cover
            if default_cover_path and os.path.exists(default_cover_path):
                media_id = self._upload_media(default_cover_path, "image")
                if media_id:
                    article["thumb_media_id"] = media_id
        
        # 如果仍然没有thumb_media_id，尝试使用cover.png
        if "thumb_media_id" not in article:
            if os.path.exists("cover.png"):
                media_id = self._upload_media("cover.png", "image")
                if media_id:
                    article["thumb_media_id"] = media_id
        
        url = "https://api.weixin.qq.com/cgi-bin/draft/add"
        params = {"access_token": token}
        data = {"articles": [article]}
        
        @with_retry(max_retries=2, delay=1.0)
        def _create_draft():
            # 使用代理
            proxies = self.proxies if self.use_proxy else {}
            
            response = requests.post(url, params=params, json=data, timeout=30, proxies=proxies)
            result = response.json()
            
            # 添加调试日志
            logger.info(f"WeChat API response: {result}")
            
            # 检查是否有错误码
            if "errcode" in result:
                errcode = result.get("errcode")
                if errcode == 0:
                    return result.get("media_id")
                else:
                    error_msg = result.get("errmsg", "Unknown error")
                    raise AppError(
                        f"创建草稿失败: {error_msg}",
                        error_type=ErrorType.SYSTEM,
                        context={"error_code": errcode, "title": title}
                    )
            # 如果没有错误码，但有media_id，说明创建成功
            elif "media_id" in result:
                return result.get("media_id")
            else:
                raise AppError(
                    f"创建草稿失败: Unknown error",
                    error_type=ErrorType.SYSTEM,
                    context={"title": title}
                )
        
        try:
            media_id = _create_draft()
            logger.info(f"Draft created: {media_id}")
            
            # 更新健康监控
            if self._health_checker:
                self._health_checker.inc_published(1)
            
            return media_id
        except AppError as e:
            logger.error(f"创建草稿失败: {e}")
            
            # 更新健康监控
            if self._health_checker:
                self._health_checker.inc_publish_failure(1)
            
            return None
        except Exception as e:
            logger.error(f"创建草稿异常: {e}")
            
            # 更新健康监控
            if self._health_checker:
                self._health_checker.inc_publish_failure(1)
            
            return None
    
    def publish_draft(self, media_id: str) -> Optional[str]:
        """发布草稿（带代理支持和重试）"""
        token = self.get_access_token()
        if not token:
            return None
        
        url = "https://api.weixin.qq.com/cgi-bin/freepublish"
        params = {"access_token": token}
        data = {"media_id": media_id, "publish_id": 0}
        
        @with_retry(max_retries=2, delay=1.0)
        def _publish_draft():
            # 使用代理
            proxies = self.proxies if self.use_proxy else {}
            
            response = requests.post(url, params=params, json=data, timeout=30, proxies=proxies)
            result = response.json()
            
            if result.get("errcode") == 0:
                return result.get("publish_id")
            else:
                error_msg = result.get("errmsg", "Unknown error")
                error_code = result.get("errcode", -1)
                raise AppError(
                    f"发布草稿失败: {error_msg}",
                    error_type=ErrorType.SYSTEM,
                    context={"error_code": error_code, "media_id": media_id}
                )
        
        try:
            publish_id = _publish_draft()
            logger.info(f"Published: {publish_id}")
            
            # 更新健康监控
            if self._health_checker:
                self._health_checker.inc_published(1)
            
            return str(publish_id)
        except AppError as e:
            logger.error(f"发布草稿失败: {e}")
            
            # 更新健康监控
            if self._health_checker:
                self._health_checker.inc_publish_failure(1)
            
            return None
        except Exception as e:
            logger.error(f"发布草稿异常: {e}")
            
            # 更新健康监控
            if self._health_checker:
                self._health_checker.inc_publish_failure(1)
            
            return None
    
    def _upload_media(self, file_path: str, media_type: str = "image") -> Optional[str]:
        """上传素材（带代理支持）"""
        token = self.get_access_token()
        if not token:
            return None
        
        url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
        params = {"access_token": token, "type": media_type}
        
        try:
            # 使用代理
            proxies = self.proxies if self.use_proxy else {}
            
            with open(file_path, "rb") as f:
                files = {"media": f}
                response = requests.post(url, params=params, files=files, timeout=60, proxies=proxies)
                result = response.json()
                
                # 检查是否有错误码
                if "errcode" in result:
                    errcode = result.get("errcode")
                    if errcode == 0:
                        return result.get("media_id")
                    else:
                        logger.error(f"Failed to upload media: {result}")
                        return None
                # 如果没有错误码，但有media_id，说明上传成功
                elif "media_id" in result:
                    return result.get("media_id")
                else:
                    logger.error(f"Failed to upload media: {result}")
                    return None
        except Exception as e:
            logger.error(f"Error uploading media: {e}")
            return None
    
    def markdown_to_html(self, markdown_text: str) -> str:
        """Markdown 转 HTML（微信公众号兼容）"""
        html = markdown_text
        
        html = re.sub(r'^### (.*?)$', r'<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2 style="font-size: 20px; color: #1a73e8; margin: 25px 0 15px; border-left: 4px solid #1a73e8; padding-left: 12px;">\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1 style="font-size: 24px; color: #333; margin: 30px 0 20px; text-align: center;">\1</h1>', html, flags=re.MULTILINE)
        
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="font-weight: bold;">\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" style="color: #1a73e8; text-decoration: underline;">\1</a>', html)
        
        html = re.sub(r'^> (.*?)$', r'<blockquote style="border-left: 3px solid #ddd; padding-left: 15px; margin: 15px 0; color: #666; font-style: italic;">\1</blockquote>', html, flags=re.MULTILINE)
        
        html = re.sub(r'^---$', r'<hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">', html, flags=re.MULTILINE)
        
        html = re.sub(r'\n\n', r'</p><p style="margin: 15px 0; line-height: 1.8;">', html)
        html = '<p style="margin: 15px 0; line-height: 1.8;">' + html + '</p>'
        
        html = re.sub(r'<p style="margin: 15px 0; line-height: 1.8;"></p>', r'', html)
        html = re.sub(r'<p style="margin: 15px 0; line-height: 1.8;">(<h[123])', r'\1', html)
        html = re.sub(r'(</h[123]>)</p>', r'\1', html)
        html = re.sub(r'<p style="margin: 15px 0; line-height: 1.8;">(<hr)', r'\1', html)
        html = re.sub(r'(</hr>)</p>', r'\1', html)
        
        return html
    
    def export_html(self, content: str, title: str, output_dir: str = "output") -> str:
        """导出为完整的 HTML 文件"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        filename = f"{output_dir}/article_{today}.html"
        
        html_content = self.markdown_to_html(content)
        
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 677px; margin: 0 auto; padding: 20px; color: #333; }}
        h1, h2, h3 {{ margin: 20px 0; }}
        p {{ line-height: 1.8; margin: 15px 0; }}
        a {{ color: #1a73e8; }}
        blockquote {{ border-left: 3px solid #ddd; padding-left: 15px; color: #666; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 30px 0; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_html)
        
        logger.info(f"HTML exported: {filename}")
        return filename


def publish_article(title: str, content: str, author: str = "", 
                    digest: str = "", cover_path: str = "",
                    auto_publish: bool = False, 
                    export_html: bool = True) -> bool:
    """发布文章"""
    publisher = WeChatPublisher()
    html_content = publisher.markdown_to_html(content)
    
    if export_html:
        publisher.export_html(content, title)
    
    if not publisher.app_id or publisher.app_id == "your_app_id_here":
        logger.warning("WeChat not configured, skipping publish")
        today = datetime.now().strftime("%Y%m%d")
        with open(f"output/article_{today}.md", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Article saved to output/article_{today}.md")
        return True
    
    media_id = publisher.create_draft(
        title=title,
        content=html_content,
        author=author,
        digest=digest,
        cover_path=cover_path
    )
    
    if not media_id:
        logger.error("Failed to create draft")
        return False
    
    if auto_publish:
        publish_id = publisher.publish_draft(media_id)
        if publish_id:
            logger.info(f"Article published! ID: {publish_id}")
            return True
        return False
    
    logger.info(f"Draft created: {media_id}")
    logger.info("Login to mp.weixin.qq.com to publish")
    return True


if __name__ == "__main__":
    test_content = """# 🎯 2024 年 1 月 24 日 AI 资讯日报

## 大模型进展

**OpenAI 发布最新 GPT-5 模型**
> OpenAI 宣布推出 GPT-5，新模型在推理能力和多模态理解方面有显著突破

[原文链接](https://openai.com)

---

## 今日点评

AI 领域正在经历快速发展期。
"""
    
    result = publish_article(
        title="2024 年 1 月 24 日 AI 资讯日报",
        content=test_content,
        auto_publish=False
    )
    print(f"Result: {result}")
