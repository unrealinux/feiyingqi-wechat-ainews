"""
Enhanced Publisher - 增强版发布器
微信公众号模板、SEO优化、分享图生成
"""
import re
import os
import json
import hashlib
import base64
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from src.logger import get_logger


logger = get_logger(__name__)


@dataclass
class WeChatArticle:
    """微信公众号文章"""
    title: str
    content: str
    digest: str = ""
    author: str = "AI前沿观察"
    content_source_url: str = ""
    thumb_media_id: str = ""
    show_cover_pic: bool = True
    need_open_comment: int = 0
    only_fans_can_comment: int = 0


@dataclass
class SEOConfig:
    """SEO配置"""
    title_template: str = "{title} - {site_name}"
    meta_description: str = ""
    meta_keywords: List[str] = None
    og_image: str = ""
    canonical_url: str = ""
    
    def __post_init__(self):
        if self.meta_keywords is None:
            self.meta_keywords = ["AI", "人工智能", "科技资讯"]


class WeChatHTMLConverter:
    """微信公众号HTML转换器 - 优化版"""
    
    # 微信公众号支持的HTML标签和属性
    ALLOWED_TAGS = {
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'a', 'img',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
        'section', 'div', 'span'
    }
    
    # 允许的标签属性
    ALLOWED_ATTRS = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height', 'data-src'],
        '*': ['style', 'class']
    }
    
    # 微信图片域名白名单
    WECHAT_IMAGE_DOMAINS = [
        'mmbiz.qpic.cn',
        'mmbiz.qlogo.cn',
        'cdn.xiaohongshu.com',
        'p.xiaohongshu.com',
    ]
    
    def __init__(self):
        self._css_cache = {}
    
    def convert(
        self, 
        markdown: str, 
        title: str = "",
        author: str = "AI前沿观察",
        date: str = ""
    ) -> str:
        """将Markdown转换为微信公众号兼容的HTML
        
        Args:
            markdown: Markdown内容
            title: 文章标题
            author: 作者
            date: 日期
        
        Returns:
            微信公众号兼容的HTML
        """
        # 解析Markdown
        html = self._markdown_to_html(markdown)
        
        # 添加标题栏
        header = self._create_header(title, author, date)
        
        # 处理图片
        html = self._process_images(html)
        
        # 优化样式
        html = self._optimize_styles(html)
        
        return header + html
    
    def _create_header(self, title: str, author: str, date: str) -> str:
        """创建文章头部"""
        date_str = date or datetime.now().strftime("%Y-%m-%d")
        
        return f'''
<section style="margin-bottom: 20px;">
    <h1 style="font-size: 24px; font-weight: bold; margin-bottom: 10px; line-height: 1.4;">{title}</h1>
    <p style="color: #888; font-size: 14px;">
        <span style="margin-right: 15px;">👤 {author}</span>
        <span>📅 {date_str}</span>
    </p>
</section>
'''
    
    def _markdown_to_html(self, markdown: str) -> str:
        """Markdown转HTML"""
        # 转义HTML特殊字符
        markdown = self._escape_html(markdown)
        
        # 转换标题
        markdown = re.sub(r'^######\s+(.+)$', r'<h6>\1</h6>', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^#####\s+(.+)$', r'<h5>\1</h5>', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', markdown, flags=re.MULTILINE)
        
        # 转换加粗
        markdown = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', markdown)
        markdown = re.sub(r'__(.+?)__', r'<strong>\1</strong>', markdown)
        
        # 转换斜体
        markdown = re.sub(r'\*(.+?)\*', r'<em>\1</em>', markdown)
        markdown = re.sub(r'_(.+?)_', r'<em>\1</em>', markdown)
        
        # 转换链接
        markdown = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', markdown)
        
        # 转换图片
        markdown = re.sub(r'!\[(.*?)\]\((.+?)\)', r'<img src="\2" alt="\1">', markdown)
        
        # 转换代码块
        markdown = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', markdown, flags=re.DOTALL)
        markdown = re.sub(r'`(.+?)`', r'<code>\1</code>', markdown)
        
        # 转换引用
        markdown = re.sub(r'^>\s+(.+)$', r'<blockquote>\1</blockquote>', markdown, flags=re.MULTILINE)
        
        # 转换无序列表
        markdown = re.sub(r'^[-*]\s+(.+)$', r'<li>\1</li>', markdown, flags=re.MULTILINE)
        
        # 转换有序列表
        markdown = re.sub(r'^\d+\.\s+(.+)$', r'<li>\1</li>', markdown, flags=re.MULTILINE)
        
        # 包裹连续的li
        markdown = re.sub(r'(<li>.*?</li>\n?)+', r'<ul>\g<0></ul>', markdown)
        
        # 转换段落
        paragraphs = []
        for para in markdown.split('\n\n'):
            para = para.strip()
            if para and not para.startswith('<'):
                paragraphs.append(f'<p>{para}</p>')
            else:
                paragraphs.append(para)
        
        return '\n'.join(paragraphs)
    
    def _escape_html(self, text: str) -> str:
        """转义HTML"""
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
        }
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        return text
    
    def _process_images(self, html: str) -> str:
        """处理图片"""
        def process_img(match):
            src = match.group(1)
            alt = match.group(2) if match.group(2) else ""
            
            # 检查是否为微信支持的图片
            if not any(domain in src for domain in self.WECHAT_IMAGE_DOMAINS):
                # 添加水印提示
                alt += " (图片可能无法显示，建议在浏览器中查看)"
            
            return f'<img src="{src}" alt="{alt}" style="max-width:100%; height:auto;">'
        
        return re.sub(r'<img src="([^"]+)"[^>]*alt="([^"]*)"', process_img, html)
    
    def _optimize_styles(self, html: str) -> str:
        """优化样式"""
        # 添加默认样式
        styles = '''
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 16px;
                line-height: 1.8;
                color: #333;
                padding: 0 15px;
            }
            h1, h2, h3, h4, h5, h6 {
                font-weight: 600;
                margin: 20px 0 10px;
                line-height: 1.4;
            }
            h1 { font-size: 24px; }
            h2 { font-size: 20px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
            h3 { font-size: 18px; }
            p { margin: 10px 0; }
            img { max-width: 100%; height: auto; display: block; margin: 15px auto; }
            pre {
                background: #f6f8fa;
                padding: 15px;
                border-radius: 6px;
                overflow-x: auto;
                font-size: 14px;
            }
            code {
                background: #f6f8fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
            }
            blockquote {
                border-left: 4px solid #ddd;
                margin: 10px 0;
                padding: 10px 15px;
                color: #666;
                background: #f9f9f9;
            }
            ul, ol {
                padding-left: 20px;
            }
            li {
                margin: 5px 0;
            }
            a {
                color: #007bff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
        '''
        
        return styles + html


class SEOGenerator:
    """SEO优化生成器"""
    
    def __init__(self, config: Optional[SEOConfig] = None):
        self.config = config or SEOConfig()
    
    def generate_meta_tags(self, title: str, description: str, url: str = "") -> str:
        """生成Meta标签
        
        Args:
            title: 页面标题
            description: 页面描述
            url: 页面URL
        
        Returns:
            Meta标签HTML
        """
        # 生成最终标题
        final_title = self.config.title_template.format(
            title=title,
            site_name="AI前沿观察"
        )
        
        # 生成描述
        final_desc = description[:200] if description else self.config.meta_description
        
        # 生成标签
        meta_tags = f'''
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{final_title}</title>
<meta name="description" content="{final_desc}">
<meta name="keywords" content="{','.join(self.config.meta_keywords)}">
<meta name="author" content="AI前沿观察">

<!-- Open Graph -->
<meta property="og:title" content="{final_title}">
<meta property="og:description" content="{final_desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url or self.config.canonical_url}">
<meta property="og:image" content="{self.config.og_image}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{final_title}">
<meta name="twitter:description" content="{final_desc}">
<meta name="twitter:image" content="{self.config.og_image}">

<!-- Canonical -->
<link rel="canonical" href="{url or self.config.canonical_url}">
'''
        return meta_tags
    
    def generate_sitemap_entry(self, url: str, lastmod: str = "", changefreq: str = "daily", priority: float = 0.8) -> str:
        """生成站点地图条目
        
        Args:
            url: 页面URL
            lastmod: 最后修改时间
            changefreq: 更新频率
            priority: 优先级
        
        Returns:
            sitemap XML条目
        """
        lastmod_str = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        
        return f'''
<url>
    <loc>{url}</loc>
    {lastmod_str}
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
</url>
'''
    
    def generate_robots_txt(self, sitemap_url: str = "") -> str:
        """生成robots.txt
        
        Args:
            sitemap_url: 站点地图URL
        
        Returns:
            robots.txt内容
        """
        content = "User-agent: *\nAllow: /\n\n"
        
        if sitemap_url:
            content += f"Sitemap: {sitemap_url}\n"
        
        return content


class ArticleMetadata:
    """文章元数据"""
    
    def __init__(self, article_id: str = ""):
        self.article_id = article_id or self._generate_id()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.word_count = 0
        self.read_time = 0
        self.views = 0
        self.likes = 0
        self.shares = 0
    
    def _generate_id(self) -> str:
        """生成文章ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"article_{timestamp}"
    
    def calculate_read_time(self, content: str) -> int:
        """计算阅读时间(分钟)"""
        words = len(content)
        self.word_count = words
        # 假设平均阅读速度: 200字/分钟
        self.read_time = max(1, words // 200)
        return self.read_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "article_id": self.article_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "word_count": self.word_count,
            "read_time": self.read_time,
            "views": self.views,
            "likes": self.likes,
            "shares": self.shares,
        }


# 便捷函数
def create_wechat_article(
    title: str,
    content: str,
    author: str = "AI前沿观察",
    **kwargs
) -> WeChatArticle:
    """创建微信公众号文章"""
    # 生成摘要
    digest = kwargs.get('digest', content[:120].replace('\n', ' '))
    
    return WeChatArticle(
        title=title,
        content=content,
        digest=digest,
        author=author,
        **kwargs
    )


def convert_to_wechat_html(
    markdown: str,
    title: str = "",
    author: str = "AI前沿观察"
) -> str:
    """转换为微信公众号HTML"""
    converter = WeChatHTMLConverter()
    return converter.convert(markdown, title, author)
