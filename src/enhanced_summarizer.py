"""
Enhanced AI Summarizer - 增强版AI摘要生成器
改进的提示词工程、多风格支持、更好的内容理解
"""
import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.logger import get_logger


logger = get_logger(__name__)


class ArticleStyle(Enum):
    """文章风格"""
    NEWS = "news"           # 新闻报道风格
    TECH = "tech"           # 技术解读风格  
    CASUAL = "casual"       # 轻松聊天风格
    PROFESSIONAL = "professional"  # 专业分析风格
    BRIEF = "brief"         # 简洁摘要风格


@dataclass
class SummarizerConfig:
    """摘要生成器配置"""
    style: ArticleStyle = ArticleStyle.NEWS
    max_length: int = 8000       # 最大字符数
    min_length: int = 3000       # 最小字符数
    temperature: float = 0.7      # 创造性
    include_toc: bool = True     # 包含目录
    include_highlights: bool = True  # 包含要点
    language: str = "zh"         # 语言


class EnhancedSummarizer:
    """增强版摘要生成器"""
    
    # 提示词模板
    PROMPT_TEMPLATES = {
        ArticleStyle.NEWS: """你是一个专业的科技新闻记者。请根据以下AI领域的新闻素材，撰写一篇专业的新闻报道。

要求：
1. 结构清晰，包含导语、主体、结语
2. 使用客观、中性的语言
3. 突出新闻价值和时间性
4. 适当引用关键信息和数据
5. 长度适中，内容充实

素材：
{content}

请生成一篇新闻报道：""",
        
        ArticleStyle.TECH: """你是一个资深科技评论员。请分析以下AI领域的最新动态，撰写一篇技术分析文章。

要求：
1. 深入分析技术原理和影响
2. 提供专业的技术见解
3. 适当包含背景信息和对比分析
4. 预测未来发展趋势
5. 专业但不失可读性

素材：
{content}

请生成技术分析文章：""",
        
        ArticleStyle.CASUAL: """你是一个科技爱好者。请用轻松友好的语气，聊聊以下AI新闻。

要求：
1. 口语化，像和朋友聊天
2. 保持简洁明了
3. 可以适当加入个人见解
4. 让复杂的内容变得易懂
5. 轻松有趣

素材：
{content}

请用轻松的语气写：""",
        
        ArticleStyle.PROFESSIONAL: """你是一个科技行业分析师。请基于以下AI新闻素材，撰写一份专业分析报告。

要求：
1. 专业严谨的分析框架
2. 深入的行业洞察
3. 数据驱动的分析
4. 竞争格局分析
5. 投资/战略建议
6. 完整的报告结构

素材：
{content}

请生成专业分析报告：""",
        
        ArticleStyle.BRIEF: """请用最简洁的方式总结以下AI新闻。

要求：
1. 一句话概括核心内容
2. 关键要点用列表呈现
3. 保持信息完整
4. 简洁明了

素材：
{content}

请简洁总结：""",
    }
    
    # 输出格式模板
    OUTPUT_TEMPLATES = {
        ArticleStyle.NEWS: """# {title}

> {digest}

## 今日要闻

{highlights}

## 详细内容

{body}

## 结语

{conclusion}

---
📰 来源：{sources}
⏰ 发布时间：{date}""",
        
        ArticleStyle.BRIEF: """# AI快讯

{summary}

## 今日要点

{highlights}

---
📰 来源：{sources} | ⏰ {date}""",
    }
    
    def __init__(self, config: Optional[SummarizerConfig] = None):
        self.config = config or SummarizerConfig()
    
    def get_prompt(self, news_items: List[Dict], custom_instruction: str = "") -> str:
        """获取生成提示词
        
        Args:
            news_items: 新闻列表
            custom_instruction: 自定义指令
        
        Returns:
            完整的提示词
        """
        # 格式化新闻内容
        content = self._format_news_content(news_items)
        
        # 获取风格模板
        style = self.config.style
        template = self.PROMPT_TEMPLATES.get(style, self.PROMPT_TEMPLATES[ArticleStyle.NEWS])
        
        # 构建提示词
        prompt = template.format(content=content)
        
        # 添加自定义指令
        if custom_instruction:
            prompt += f"\n\n额外要求：{custom_instruction}"
        
        # 添加格式要求
        prompt += self._get_format_instruction()
        
        return prompt
    
    def _format_news_content(self, news_items: List[Dict]) -> str:
        """格式化新闻内容"""
        lines = []
        
        for i, item in enumerate(news_items, 1):
            title = item.get("title", "")
            source = item.get("source", "")
            desc = item.get("description", "")
            url = item.get("url", "")
            
            lines.append(f"### 新闻 {i}")
            lines.append(f"标题：{title}")
            if source:
                lines.append(f"来源：{source}")
            if desc:
                lines.append(f"摘要：{desc}")
            if url:
                lines.append(f"链接：{url}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_format_instruction(self) -> str:
        """获取格式指令"""
        instructions = [
            "",
            "=== 格式要求 ===",
            f"- 输出语言：{self.config.language}",
            f"- 最大长度：{self.config.max_length}字符",
            f"- 最小长度：{self.config.min_length}字符",
        ]
        
        if self.config.include_toc:
            instructions.append("- 添加目录结构")
        
        if self.config.include_highlights:
            instructions.append("- 包含今日要点")
        
        # 添加Markdown格式要求
        instructions.extend([
            "- 使用Markdown格式",
            "- 合理使用标题层级",
            "- 适当使用列表和引用",
        ])
        
        return "\n".join(instructions)
    
    def parse_ai_response(self, response: str, news_items: List[Dict]) -> Dict[str, Any]:
        """解析AI响应
        
        Args:
            response: AI生成的文本
            news_items: 原始新闻列表
        
        Returns:
            解析后的结构化数据
        """
        # 提取标题
        title = self._extract_title(response)
        
        # 提取摘要
        digest = self._extract_digest(response)
        
        # 提取要点
        highlights = self._extract_highlights(response)
        
        # 提取正文
        body = self._extract_body(response, highlights)
        
        # 提取结论
        conclusion = self._extract_conclusion(response)
        
        # 提取来源
        sources = self._extract_sources(news_items)
        
        return {
            "title": title,
            "digest": digest,
            "highlights": highlights,
            "body": body,
            "conclusion": conclusion,
            "sources": sources,
            "full_content": response,
            "style": self.config.style.value,
            "word_count": len(response),
        }
    
    def _extract_title(self, text: str) -> str:
        """提取标题"""
        # 尝试从Markdown标题中提取
        match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # 使用第一行作为标题
        lines = text.strip().split('\n')
        if lines:
            return lines[0][:100]
        
        return "AI每日资讯"
    
    def _extract_digest(self, text: str) -> str:
        """提取摘要"""
        # 尝试从引用中提取
        match = re.search(r'^>?\s*(.+)', text)
        if match:
            return match.group(1).strip()[:200]
        
        # 使用第一段
        paragraphs = text.split('\n\n')
        for p in paragraphs:
            if len(p.strip()) > 20:
                return p.strip()[:200]
        
        return ""
    
    def _extract_highlights(self, text: str) -> List[str]:
        """提取要点"""
        highlights = []
        
        # 查找"今日要点"、"关键信息"等章节
        patterns = [
            r'##\s*(?:今日要点|关键信息|要点|Highlights)(?:\s*[-:])?\s*\n(.*?)(?=\n##|\Z)',
            r'^\d+[.、]\s*(.+)$',
            r'^[-•]\s*(.+)$',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            if matches:
                for match in matches[:5]:
                    if len(match.strip()) > 10:
                        highlights.append(match.strip())
                break
        
        return highlights[:5]
    
    def _extract_body(self, text: str, highlights: List[str]) -> str:
        """提取正文"""
        # 移除标题和要点部分
        body = text
        
        # 移除标题
        body = re.sub(r'^#\s+.+\n', '', body, flags=re.MULTILINE)
        
        # 移除要点章节
        body = re.sub(r'##\s*(?:今日要点|关键信息|要点|Highlights).+?(?=\n##|\Z)', '', body, flags=re.DOTALL)
        
        # 移除引用
        body = re.sub(r'^>.*\n?', '', body, flags=re.MULTILINE)
        
        return body.strip()
    
    def _extract_conclusion(self, text: str) -> str:
        """提取结论"""
        # 查找结语部分
        match = re.search(r'##\s*(?:结语|总结|Conclusion)(?:\s*[-:])?\s*\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _extract_sources(self, news_items: List[Dict]) -> str:
        """提取来源"""
        sources = set()
        for item in news_items:
            if item.get("source"):
                sources.add(item["source"])
        
        return " / ".join(sorted(sources)) if sources else "综合来源"
    
    def generate_article(
        self, 
        news_items: List[Dict], 
        ai_client,
        custom_instruction: str = ""
    ) -> Dict[str, Any]:
        """生成文章
        
        Args:
            news_items: 新闻列表
            ai_client: AI客户端
            custom_instruction: 自定义指令
        
        Returns:
            生成的完整文章数据
        """
        # 构建提示词
        prompt = self.get_prompt(news_items, custom_instruction)
        
        logger.info(f"Generating article with style: {self.config.style.value}")
        
        # 调用AI生成
        response = ai_client.generate(
            prompt=prompt,
            max_tokens=self.config.max_length,
            temperature=self.config.temperature,
        )
        
        # 解析响应
        article_data = self.parse_ai_response(response, news_items)
        
        logger.info(f"Article generated: {article_data.get('word_count', 0)} chars")
        
        return article_data


# 便捷函数
def create_summarizer(
    style: str = "news",
    language: str = "zh",
    **kwargs
) -> EnhancedSummarizer:
    """创建摘要生成器"""
    style_enum = ArticleStyle(style) if isinstance(style, str) else style
    
    config = SummarizerConfig(
        style=style_enum,
        language=language,
        **kwargs
    )
    
    return EnhancedSummarizer(config)
