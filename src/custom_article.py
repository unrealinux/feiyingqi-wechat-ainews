"""
Custom Article Generator - 自定义文章生成模块

支持生成各种类型的自定义文章，包括横评、评测等。

内容全部由 LLM 实时生成。早期版本在每个 generate_* 末尾挂了一个
"所有 LLM 都不可用时返回预写模板文章"的兜底，那批模板结构高度同质
（同一套小标题 + 同一套句式换名词），属于 AGENTS.md 明令禁止的
模板化洗稿，已整体移除。现在 LLM 不可用一律抛 LLMUnavailableError，
由调用方 fail-closed 处理——宁可不产出，不塞低质稿。
"""

import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from src.config import load_config
from src.domestic_llm import get_domestic_llm
from src.summarizer import Summarizer, LLMUnavailableError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# 表格格式强制要求（所有横评文章通用）
TABLE_FORMAT_INSTRUCTION = """
⚠️ **表格格式强制要求**（不遵守将导致表格显示错误）：
1. 第一行必须是表头：| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
2. 第二行必须是分隔线：| --- | --- | --- | --- | --- | --- |
3. 第三行开始是数据：| 工具1 | 功能1 | 优势1 | ... |
4. 禁止跳过表头直接写数据行！
5. 禁止在表格中使用加粗、换行等复杂格式！

※ 如需生成**表格图片**（推荐），在表格前添加 @table_image@ 标记：
```markdown
@table_image@
| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
| --- | --- | --- | --- | --- | --- |
| Notion AI | 功能1 | 优势1 | 不足1 | 场景1 | 价格1 |
...
```

示例：
```
@table_image@
| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
| --- | --- | --- | --- | --- | --- |
| Notion AI | 内容生成 | 功能全面 | 付费较高 | 知识管理 | $10/月 |
| Obsidian AI | 本地笔记 | 隐私安全 | 功能较少 | 个人使用 | 免费 |
```
"""

class CustomArticleGenerator:
    """自定义文章生成器"""
    
    def __init__(self):
        self.config = load_config()
        self.domestic_llm = get_domestic_llm()
        self.summarizer = Summarizer()
        self._init_image_generator()
    
    def _init_image_generator(self):
        """初始化图片生成器"""
        try:
            from src.dashscope_image_gen import DashScopeImageGenerator
            self.image_generator = DashScopeImageGenerator()
            logger.info("DashScope image generator initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize image generator: {e}")
            self.image_generator = None
    
    def generate_cover_image(self, title: str, output_dir: str = "output") -> Optional[str]:
        """
        生成文章封面图
        
        Args:
            title: 文章标题
            output_dir: 输出目录
            
        Returns:
            str: 图片路径，失败返回 None
        """
        if not self.image_generator:
            logger.warning("Image generator not available")
            return None
        
        logger.info(f"Generating cover image for: {title}")
        return self.image_generator.generate_ai_meeting_cover(title, output_dir)
    
    def generate_note_tools_review(self) -> str:
        """
        生成AI笔记工具横评文章
        
        Returns:
            str: 生成的文章内容（Markdown格式）
        """
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI笔记工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI笔记成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Notion AI
     * Obsidian AI（插件）
     * Apple Notes AI
     * Microsoft OneNote AI
     * Google Keep AI
     * Evernote AI
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

""" + TABLE_FORMAT_INSTRUCTION

        # 尝试使用国内LLM
        if self.domestic_llm.is_available():
            logger.info(f"使用 {self.domestic_llm.get_provider_name()} 生成文章")
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        # 回退到OpenAI
        if self.summarizer.client:
            logger.info("使用OpenAI生成文章")
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_search_tools_review(self) -> str:
        """生成AI搜索工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI搜索工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI搜索成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Perplexity
     * ChatGPT Search
     * Kimi（国产）
     * 秘塔AI搜索
     * 百度AI搜索
     * 360 AI搜索
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与未来展望
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

""" + TABLE_FORMAT_INSTRUCTION

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_code_tools_review(self) -> str:
        """生成AI编程工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI编程工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI编程成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * GitHub Copilot
     * Claude AI（Anthropic）
     * Cursor
     * Replit AI
     * CodeWhisperer
     * 通义灵码（国产）
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

""" + TABLE_FORMAT_INSTRUCTION

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_video_tools_review(self) -> str:
        """生成AI视频工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI视频工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI视频成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Sora (OpenAI)
     * Runway
     * Pika
     * Luma AI
     * Pixverse（国产）
     * 可灵AI（国产）
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

""" + TABLE_FORMAT_INSTRUCTION

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_audio_tools_review(self) -> str:
        """生成AI音频工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI音频工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI音频成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * ElevenLabs
     * Audiobox (Meta)
     * Cope
     * 剪映AI
     * 讯飞智文
     * 米可智能（国产）
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

""" + TABLE_FORMAT_INSTRUCTION

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_office_tools_review(self) -> str:
        """生成AI办公工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI办公工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI办公成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Microsoft 365 Copilot
     * Google Workspace AI
     * Notion AI
     * WPS AI
     * 石墨文档 AI
     * 飞书多维表格 AI
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

""" + TABLE_FORMAT_INSTRUCTION

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_design_tools_review(self) -> str:
        """生成AI设计工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI设计工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI设计成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Figma AI
     * Canva AI
     * Adobe Firefly
     * Midjourney（设计应用）
     * 即时设计 AI（国产）
     * 美图云修（国产）
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_marketing_tools_review(self) -> str:
        """生成AI营销工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI营销工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI营销成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * HubSpot AI
     * Jasper AI
     * Copy.ai
     * PepperType AI
     * 秘塔写作猫（国产）
     * 讯飞智文（国产）
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_data_tools_review(self) -> str:
        """生成AI数据分析工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI数据分析工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI数据分析成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Tableau AI
     * Power BI AI
     * Thoughtspot
     * 帆软AI（国产）
     * 观远BI（国产）
     * 神策数据（国产）
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_education_tools_review(self) -> str:
        """生成AI教育工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI教育工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI教育成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Khan Academy AI
     * Duolingo Max
     * Quizlet AI
     * 作业帮AI
     * 猿辅导AI
     * 科大讯飞学习机
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_medical_tools_review(self) -> str:
        """生成AI医疗工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI医疗工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI医疗成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * IBM Watson Health
     * PathAI
     * 平安好医生AI
     * 阿里健康AI
     * 推想医疗AI
     * 科亚医疗AI
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_finance_tools_review(self) -> str:
        """生成AI金融工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI金融工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI金融成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Bloomberg GPT
     * Kensho (S&P Global)
     * 同花顺AI
     * 东方财富AI
     * 蚂蚁财富AI
     * 京东金融AI
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_legal_tools_review(self) -> str:
        """生成AI法律工具横评文章"""
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI法律工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI法律成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * LegalSifter
     * Casetext (Coo)
     * 法狗狗AI
     * 华宇法律AI
     * 北大法宝AI
     * 无讼AI
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        if self.domestic_llm.is_available():
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        if self.summarizer.client:
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30
                )
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_image_tools_review(self) -> str:
        """
        生成AI绘画工具横评文章
        
        Returns:
            str: 生成的文章内容（Markdown格式）
        """
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI绘画工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI绘画成为新趋势
   - 主流工具横评（至少包含6个工具）：
     * Midjourney
     * DALL-E 3
     * Stable Diffusion
     * 文心一格（国产）
     * 通义万相（国产）
     * 6pen Art（国产）
   - 每个工具的：核心功能、优势、不足、适用场景
   - **综合对比表格**（Markdown格式）：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
   - 选购建议与使用技巧
3. 字数：3000-4000字
4. 包含emoji和格式化

注意：表格使用正确的Markdown语法（| --- |格式）

""" + TABLE_FORMAT_INSTRUCTION

        # 尝试使用国内LLM（快速失败）
        if self.domestic_llm.is_available():
            logger.info(f"使用 {self.domestic_llm.get_provider_name()} 生成文章")
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        # 回退到OpenAI（快速失败）
        if self.summarizer.client:
            logger.info("使用OpenAI生成文章")
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30  # 减少超时时间
                )
                
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def generate_meeting_tools_review(self) -> str:
        """
        生成AI会议工具横评文章
        
        Returns:
            str: 生成的文章内容（Markdown格式）
        """
        system_prompt = """你是一位专业的科技编辑，擅长撰写深度横评文章。
文笔专业严谨，分析全面深入，适合公众号读者阅读。
文章结构清晰，对比分析透彻，观点客观公正。"""
        
        user_prompt = """请为微信公众号撰写一篇关于AI会议工具的深度横评文章。

要求：
1. 标题要有吸引力，使用emoji增加视觉效果
2. 文章结构包括：
   - 引言：为什么AI会议工具很重要
   - 主流工具横评（至少包含5个工具）：
     * Zoom AI Companion
     * Microsoft Teams Copilot
     * Google Meet Gemini
     * 腾讯会议AI助手
     * 飞书妙记
     * 其他值得关注的工具
   - 每个工具的：
     * 核心功能介绍
     * 优势与特色
     * 不足与限制
     * 适用场景
   - **综合对比表格**（Markdown格式）：
     必须使用Markdown表格语法，表格包含以下列：
     | 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
     每行一个工具，至少5个工具
   - 选购建议与使用技巧
   - 未来发展趋势展望
3. 语言风格：专业但生动，适合科技爱好者阅读
4. 字数：3000-4000字
5. 包含适当的emoji和格式化元素

注意：
- 对比表格必须使用正确的Markdown表格语法（| --- | --- |格式）
- 表格要简洁清晰，方便转换为HTML表格

请直接输出公众号文章内容（Markdown格式），不要添加额外说明。"""

        # 尝试使用国内LLM（快速失败）
        if self.domestic_llm.is_available():
            logger.info(f"使用 {self.domestic_llm.get_provider_name()} 生成文章")
            try:
                result = self.domestic_llm.chat(user_prompt, system_prompt)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"国内LLM生成失败: {e}")
        
        # 回退到OpenAI（快速失败）
        if self.summarizer.client:
            logger.info("使用OpenAI生成文章")
            try:
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    timeout=30  # 减少超时时间
                )
                
                article = response.choices[0].message.content
                if article:
                    return article
            except Exception as e:
                logger.warning(f"OpenAI生成失败: {e}")

        # LLM 全部不可用：fail-closed，绝不回退到模板拼贴稿（AGENTS.md 红线）
        raise LLMUnavailableError(
            "所有 LLM 均不可用，本次不产出文章（模板兜底已移除，见 AGENTS.md）"
        )
    
    def save_article(self, article: str, title: str = None) -> tuple:
        """
        保存文章到本地
        
        Args:
            article: 文章内容
            title: 文章标题（可选）
            
        Returns:
            tuple: (md_path, html_path)
        """
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        md_path = output_dir / f"ai_meeting_tools_review_{today}.md"
        html_path = output_dir / f"ai_meeting_tools_review_{today}.html"
        
        # 保存Markdown
        with open(md_path, "w", encoding="utf-8") as f:
            if title:
                f.write(f"# {title}\n\n{article}")
            else:
                f.write(article)
        
        logger.info(f"文章已保存: {md_path}")
        return md_path, html_path


def generate_custom_article(article_type: str = "meeting_tools_review") -> str:
    """
    生成自定义文章的便捷函数
    
    Args:
        article_type: 文章类型
        
    Returns:
        str: 生成的文章内容
    """
    generator = CustomArticleGenerator()
    
    if article_type == "meeting_tools_review":
        return generator.generate_meeting_tools_review()
    elif article_type == "image_tools_review":
        return generator.generate_image_tools_review()
    elif article_type == "note_tools_review":
        return generator.generate_note_tools_review()
    elif article_type == "search_tools_review":
        return generator.generate_search_tools_review()
    elif article_type == "code_tools_review":
        return generator.generate_code_tools_review()
    elif article_type == "video_tools_review":
        return generator.generate_video_tools_review()
    elif article_type == "audio_tools_review":
        return generator.generate_audio_tools_review()
    elif article_type == "office_tools_review":
        return generator.generate_office_tools_review()
    elif article_type == "design_tools_review":
        return generator.generate_design_tools_review()
    elif article_type == "marketing_tools_review":
        return generator.generate_marketing_tools_review()
    elif article_type == "data_tools_review":
        return generator.generate_data_tools_review()
    elif article_type == "education_tools_review":
        return generator.generate_education_tools_review()
    elif article_type == "medical_tools_review":
        return generator.generate_medical_tools_review()
    elif article_type == "finance_tools_review":
        return generator.generate_finance_tools_review()
    elif article_type == "legal_tools_review":
        return generator.generate_legal_tools_review()
    else:
        raise ValueError(f"不支持的文章类型: {article_type}")


if __name__ == "__main__":
    # 测试
    print("测试自定义文章生成...")
    generator = CustomArticleGenerator()
    try:
        article = generator.generate_meeting_tools_review()
    except LLMUnavailableError as e:
        print(f"[SKIP] {e}")
    else:
        print(f"文章生成完成，长度: {len(article)} 字符")
        print("\n预览前500字符:")
        print(article[:500])