"""
Custom Article Generator - 自定义文章生成模块

支持生成各种类型的自定义文章，包括横评、评测等
"""

import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from src.config import load_config
from src.domestic_llm import get_domestic_llm
from src.summarizer import Summarizer

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
        
        # 模板文章
        logger.warning("所有LLM都不可用，使用模板文章")
        return self._get_note_tools_template_article()
    
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
        
        return self._get_search_tools_template_article()
    
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
        
        return self._get_code_tools_template_article()
    
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
        
        return self._get_video_tools_template_article()
    
    def _get_video_tools_template_article(self) -> str:
        return f"""# 🎬 {datetime.now().strftime("%Y年%m月%d日")} AI视频工具大横评：谁才是创作者的神器？

## 📝 引言

AI视频正在崛起！从Sora到Runway，从Pika到可灵AI，各类AI视频工具层出不穷。今天，我们来深度横评主流AI视频工具。

---

## 🎬 主流AI视频工具横评

### 1. Sora 🔵

**核心功能**：文本转视频、图生视频、视频延长

**优势**：质量最高、时长最长

**不足**：未公开、成本高

**适用场景**：专业制作

### 2. Runway 🔷

**核心功能**：视频生成、编辑、特效

**优势**：功能全面、生态好

**不足**：需付费、等待时间长

**适用场景**：创意制作

### 3. Pika 🎨

**核心功能**：文本转视频、图生视频

**优势**：免费、速度快

**不足**：质量一般、时长短

**适用场景**：社交媒体

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Sora | 文本转视频 | 质量最�� | 未公开 | 专业 | 待定 |
| Runway | 视频生成 | 功能全 | 付费 | 创意 | 付费 |
| Pika | 文本转视频 | 免费快 | 质量一般 | 社交 | 免费 |
| Luma AI | 视频生成 | 效果好 | 有限 | 创作 | 免费 |
| Pixverse | 文本转视频 | 中文 | 起步晚 | 中文 | 免费 |
| 可灵AI | 文本转视频 | 国产免费 | 排队久 | 国内 | 免费 |

---

## 💡 选购建议

1. **专业制作**：Sora、Runway
2. **社交媒体**：Pika
3. **中文用户**：可灵AI、Pixverse

---

## 🔮 未来展望

AI视频将在电影、游戏等领域大放异彩！

---

*本文由AI生成，仅供参考*"""
    
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
        
        return self._get_audio_tools_template_article()
    
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
        
        return self._get_office_tools_template_article()
    
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
        
        return self._get_design_tools_template_article()
    
    def _get_design_tools_template_article(self) -> str:
        return f"""# 🎨 {datetime.now().strftime("%Y年%m月%d日")} AI设计工具大横评：谁才是设计师的最佳拍档？

## 📝 引言

AI正在彻底改变设计行业！从Figma到Canva，从Adobe Firefly到即时设计，各类AI设计工具层出不穷。今天，我们来深度横评主流AI设计工具。

---

## 🎨 主流AI设计工具横评

### 1. Figma AI 🔵

**核心功能**：UI设计、原型制作、AI生成组件

**优势**：协作强、生态完善、插件丰富

**不足**：需联网、高级功能付费

**适用场景**：UI/UX设计、团队协作

### 2. Canva AI 🔷

**核心功能**：海报设计、社交媒体图、AI生图

**优势**：模板多、上手快、免费版够用

**不足**：专业功能少、定制性弱

**适用场景**：营销物料、社交媒体

### 3. Adobe Firefly 🎨

**核心功能**：AI图像生成、编辑、风格迁移

**优势**：Adobe生态、质量高、版权清晰

**不足**：需订阅、学习曲线陡

**适用场景**：专业设计、品牌创作

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Figma AI | UI设计 | 协作强 | 需联网 | UI/UX | 免费+付费 |
| Canva AI | 平面设计 | 模板多 | 功能少 | 营销 | 免费+增值 |
| Adobe Firefly | AI图像 | 质量高 | 需订阅 | 专业设计 | 含Creative Cloud |
| Midjourney | AI生图 | 质量顶级 | 无编辑 | 艺术创作 | 付费订阅 |
| 即时设计 AI | UI设计 | 中文免费 | 功能少 | 国内设计 | 免费 |
| 美图云修 | 人像美化 | 一键美颜 | 场景少 | 人像处理 | 免费+增值 |

---

## 💡 选购建议

1. **UI/UX设计**：Figma AI
2. **营销物料**：Canva AI
3. **专业创作**：Adobe Firefly
4. **中文用户**：即时设计 AI

---

## 🔮 未来展望

AI设计将让每个人都能成为设计师！

---

*本文由AI生成，仅供参考*"""
    
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
        
        return self._get_marketing_tools_template_article()
    
    def _get_marketing_tools_template_article(self) -> str:
        return f"""# 📣 {datetime.now().strftime("%Y年%m月%d日")} AI营销工具大横评：谁才是营销人的最佳助手？

## 📝 引言

AI正在重塑营销方式！从内容创作到客户分析，从广告投放到社媒管理，AI营销工具让营销效率翻倍。今天，我们来深度横评主流AI营销工具。

---

## 📣 主流AI营销工具横评

### 1. HubSpot AI 🔵

**核心功能**：营销自动化、客户分析、内容生成

**优势**：生态完善、集成度高

**不足**：价格高、学习曲线陡

**适用场景**：企业营销、CRM管理

### 2. Jasper AI 🔷

**核心功能**：AI写作、营销文案、品牌语调

**优势**：质量高、多语言支持

**不足**：需付费、中文能力弱

**适用场景**：英文内容、营销文案

### 3. Copy.ai 📝

**核心功能**：快速文案生成、社交媒体内容

**优势**：速度快、模板多**

**不足**：创意有限、重复率高**

**适用场景**：社媒运营、快速产出**

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| HubSpot AI | 营销自动化 | 生态完善 | 价格高 | 企业营销 | 付费 |
| Jasper AI | AI写作 | 质量高 | 需付费 | 营销文案 | 付费 |
| Copy.ai | 文案生成 | 速度快 | 创意少 | 社媒运营 | 免费+付费 |
| PepperType AI | 内容生成 | 模板多 | 功能少 | 博客写作 | 付费 |
| 秘塔写作猫 | 中文写作 | 中文免费 | 功能少 | 国内营销 | 免费 |
| 讯飞智文 | 中文生成 | 语音输入 | 起步晚 | 中文创作 | 免费 |

---

## 💡 选购建议

1. **企业营销**：HubSpot AI
2. **英文内容**：Jasper AI
3. **社媒运营**：Copy.ai
4. **中文用户**：秘塔写作猫

---

## 🔮 未来展望

AI营销将让每个人都能成为营销专家！

---

*本文由AI生成，仅供参考*"""
    
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
        
        return self._get_data_tools_template_article()
    
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
        
        return self._get_education_tools_template_article()
    
    def _get_education_tools_template_article(self) -> str:
        return f"""# 🎓 {datetime.now().strftime("%Y年%m月%d日")} AI教育工具大横评：谁才是学习的最佳助手？

## 📝 引言

AI正在改变教育方式！从个性化学习到智能辅导，从语言学习到作业批改，AI教育工具让学习更高效。今天，我们来深度横评主流AI教育工具。

---

## 🎓 主流AI教育工具横评

### 1. Khan Academy AI 🔵

**核心功能**：个性化学习路径、智能辅导、知识点推荐

**优势**：免费、内容权威、覆盖K-12

**不足**：中文资源少、需科学上网

**适用场景**：K-12学习、自学

### 2. Duolingo Max 🔷

**核心功能**：AI语言学习、对话练习、角色扮演

**优势**：趣味性强、多语言支持

**不足**：高级功能需订阅、专业度有限

**适用场景**：语言学习、日常练习

### 3. Quizlet AI 📚

**核心功能**：智能闪卡、学习路径、记忆曲线优化

**优势**：科学记忆、多平台同步

**不足**：功能相对单一、中文内容少

**适用场景**：备考、记忆学习

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Khan Academy AI | 个性化学习 | 免费权威 | 中文少 | K-12学习 | 免费 |
| Duolingo Max | 语言学习 | 趣味性强 | 需订阅 | 语言学习 | 免费+付费 |
| Quizlet AI | 智能闪卡 | 科学记忆 | 功能单一 | 备考 | 免费+付费 |
| 作业帮AI | 作业批改 | 中文免费 | 场景有限 | 中小学 | 免费+增值 |
| 猿辅导AI | 在线辅导 | 真人+AI | 价格高 | K-12辅导 | 付费 |
| 科大讯飞学习机 | AI学习机 | 硬件一体 | 价格高 | 家庭教育 | 硬件销售 |

---

## 💡 选购建议

1. **K-12学生**：Khan Academy AI + 作业帮AI
2. **语言学习**：Duolingo Max
3. **备考记忆**：Quizlet AI
4. **家庭教育**：科大讯飞学习机

---

## 🔮 未来展望

AI教育将实现真正的个性化学习，让每个人都能高效学习！

---

*本文由AI生成，仅供参考*"""
    
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
        
        return self._get_medical_tools_template_article()
    
    def _get_medical_tools_template_article(self) -> str:
        return f"""# 🏥 {datetime.now().strftime("%Y年%m月%d日")} AI医疗工具大横评：谁才是健康的最佳守护者？

## 📝 引言

AI正在革新医疗健康！从辅助诊断到药物研发，从健康管理到医疗影像，AI医疗工具正在改变整个行业。今天，我们来深度横评主流AI医疗工具。

---

## 🏥 主流AI医疗工具横评

### 1. IBM Watson Health 🔵

**核心功能**：癌症诊断、治疗建议、医疗数据分析

**优势**：历史悠久、数据丰富

**不足**：商业化困难、实际效果争议

**适用场景**：医院、研究机构

### 2. PathAI 🔬

**核心功能**：病理影像分析、癌症检测

**优势**：专业性强、准确率高

**不足**：应用场景有限、需专业设备

**适用场景**：病理诊断、医学研究

### 3. 平安好医生AI 🟢

**核心功能**：在线问诊、健康咨询、智能分诊

**优势**：中文服务、生态完善

**不足**：诊断能力有限、依赖真人医生

**适用场景**：日常健康咨询

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| IBM Watson Health | 辅助诊断 | 数据丰富 | 效果争议 | 医院 | 企业服务 |
| PathAI | 病理分析 | 准确率高 | 场景有限 | 病理诊断 | 企业服务 |
| 平安好医生AI | 在线问诊 | 中文生态 | 诊断有限 | 健康咨询 | 免费+增值 |
| 阿里健康AI | 医药电商 | 生态完善 | 功能基础 | 在线购药 | 免费+增值 |
| 推想医疗AI | 影像诊断 | 专业精准 | 价格高 | 医院影像 | 企业服务 |
| 科亚医疗AI | 心血管AI | 专科深入 | 场景单一 | 心血管诊断 | 企业服务 |

---

## 💡 选购建议

1. **医院机构**：IBM Watson 或 推想医疗AI
2. **日常咨询**：平安好医生AI
3. **医药购买**：阿里健康AI
4. **专科诊断**：科亚医疗AI

---

## 🔮 未来展望

AI医疗将让精准医疗成为现实，拯救更多生命！

---

*本文由AI生成，仅供参考*"""
    
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
        
        return self._get_finance_tools_template_article()
    
    def _get_finance_tools_template_article(self) -> str:
        return f"""# 💹 {datetime.now().strftime("%Y年%m月%d日")} AI金融工具大横评：谁才是投资的最佳参谋？

## 📝 引言

AI正在改变金融行业！从智能投顾到风险控制，从量化交易到财务分析，AI金融工具正在重塑投资方式。今天，我们来深度横评主流AI金融工具。

---

## 💹 主流AI金融工具横评

### 1. Bloomberg GPT 🔵

**核心功能**：金融数据分析、市场预测、新闻分析

**优势**：数据权威、实时性强

**不足**：价格昂贵、主要面向机构

**适用场景**：机构投资者、专业交易员

### 2. Kensho (S&P Global) 🔷

**核心功能**：金融分析、事件驱动分析、风险评估

**优势**：标普背书、分析深入

**不足**：使用门槛高、需专业背景

**适用场景**：金融机构、分析师

### 3. 同花顺AI 🟢

**核心功能**：智能选股、技术分析、行情预测

**优势**：中文服务、散户友好

**不足**：预测准确性有限、需付费

**适用场景**：个人投资者、散户

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Bloomberg GPT | 金融分析 | 数据权威 | 价格昂贵 | 机构投资者 | 企业服务 |
| Kensho | 事件分析 | 标普背书 | 门槛高 | 金融机构 | 企业服务 |
| 同花顺AI | 智能选股 | 散户友好 | 准确性有限 | 个人投资 | 免费+付费 |
| 东方财富AI | 财经资讯 | 中文全面 | 功能基础 | 信息获取 | 免费+增值 |
| 蚂蚁财富AI | 智能投顾 | 生态完善 | 收益一般 | 理财规划 | 免费+增值 |
| 京东金融AI | 消费金融 | 场景丰富 | 金融深度浅 | 消费信贷 | 免费+增值 |

---

## 💡 选购建议

1. **机构投资者**：Bloomberg GPT 或 Kensho
2. **个人投资者**：同花顺AI
3. **理财规划**：蚂蚁财富AI
4. **信息获取**：东方财富AI

---

## 🔮 未来展望

AI金融将让每个人都能享受专业级的投资建议！

---

*本文由AI生成，仅供参考*"""
    
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
        
        return self._get_legal_tools_template_article()
    
    def _get_legal_tools_template_article(self) -> str:
        return f"""# ⚖️ {datetime.now().strftime("%Y年%m月%d日")} AI法律工具大横评：谁才是法律人的最佳助手？

## 📝 引言

AI正在改变法律行业！从合同审查到案例检索，从法律研究到风险评估，AI法律工具正在提升法律工作效率。今天，我们来深度横评主流AI法律工具。

---

## ⚖️ 主流AI法律工具横评

### 1. LegalSifter 🔵

**核心功能**：合同审查、条款分析、风险识别

**优势**：专业性强、准确率高

**不足**：主要面向英文、价格昂贵

**适用场景**：企业法务、律所

### 2. Casetext (Coo) 🔷

**核心功能**：案例检索、法律研究、AI助手

**优势**：数据全面、被Coo收购整合

**不足**：中文支持弱、需订阅

**适用场景**：法律研究、案例检索

### 3. 法狗狗AI 🟢

**核心功能**：智能咨询、合同生成、法规查询

**优势**：中文服务、价格亲民

**不足**：功能深度有限、数据覆盖不全

**适用场景**：中小企业、个人咨询

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| LegalSifter | 合同审查 | 专业准确 | 价格贵 | 企业法务 | 企业服务 |
| Casetext | 案例检索 | 数据全面 | 中文弱 | 法律研究 | 付费订阅 |
| 法狗狗AI | 智能咨询 | 中文价格好 | 功能有限 | 中小企业 | 免费+增值 |
| 华宇法律AI | 司法AI | 法院合作 | 场景单一 | 司法机关 | 企业服务 |
| 北大法宝AI | 法律检索 | 权威全面 | 界面老旧 | 法律研究 | 付费订阅 |
| 无讼AI | 律师助手 | 律师生态 | 功能基础 | 律师工作 | 免费+增值 |

---

## 💡 选购建议

1. **企业法务**：LegalSifter
2. **法律研究**：Casetext 或 北大法宝AI
3. **中小企业**：法狗狗AI
4. **律师工作**：无讼AI

---

## 🔮 未来展望

AI法律将让法律服务更高效、更普惠！

---

*本文由AI生成，仅供参考*"""
    
    def _get_data_tools_template_article(self) -> str:
        return f"""# 📊 {datetime.now().strftime("%Y年%m月%d日")} AI数据分析工具大横评：谁才是数据分析师的最佳拍档？

## 📝 引言

AI正在彻底改变数据分析！从自动建模到智能洞察，从自然语言查询到预测分析，AI数据分析工具让数据价值最大化。今天，我们来深度横评主流AI数据分析工具。

---

## 📊 主流AI数据分析工具横评#

### 1. Tableau AI 🔵

**核心功能**：可视化分析、AI洞察、自然语言查询

**优势**：可视化强、生态成熟**

**不足**：价格高、学习曲线陡**

**适用场景**：企业BI、数据可视化**

### 2. Power BI AI 🔷

**核心功能**：微软生态集成、AI分析、实时仪表盘**

**优势**：与Office集成、性价比高**

**不足**：功能相对基础**

**适用场景**：中小企业、Office用户**

### 3. Thoughtspot 🧠

**核心功能**：搜索式分析、AI洞察、实时查询**

**优势**：搜索体验好、响应快**

**不足**：生态小、功能少**

**适用场景**：快速查询、业务分析**

---

## 📊 综合对比表格#

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Tableau AI | 可视化分析 | 可视化强 | 价格高 | 企业BI | 付费 |
| Power BI AI | BI分析 | Office集成 | 功能基础 | 中小企业 | 含Office 365 |
| Thoughtspot | 搜索分析 | 搜索体验 | 生态小 | 业务分析 | 付费 |
| 帆软AI | 国产BI | 中文支持 | 功能少 | 国内企业 | 付费 |
| 观远BI | 智能分析 | 国产免费 | 起步晚 | 国内分析 | 免费+付费 |
| 神策数据 | 用户分析 | 行为追踪 | 场景少 | 用户运营 | 付费 |

---

## 💡 选购建议"

1. **企业BI**：Tableau AI
2. **Office用户**：Power BI AI
3. **快速查询**：Thoughtspot
4. **国内企业**：帆软AI

---

## 🔮 未来展望"

AI数据分析将让每个人都能成为数据分析师！

---

*本文由AI生成，仅供参考*"""
    
    def _get_office_tools_template_article(self) -> str:
        return f"""# 💼 {datetime.now().strftime("%Y年%m月%d日")} AI办公工具大横评：谁才是职场人的最佳助手？

## 📝 引言

AI正在重塑办公方式！从文档写作到数据分析，从会议纪要到项目管理，AI办公工具让工作效率翻倍。今天，我们来深度横评主流AI办公工具。

---

## 💼 主流AI办公工具横评

### 1. Microsoft 365 Copilot 🔵

**核心功能**：Word写作、Excel分析、PPT生成、会议纪要

**优势**：深度集成Office、生态完善

**不足**：仅限企业版、需订阅

**适用场景**：企业办公、数据分析

### 2. Google Workspace AI 🔷

**核心功能**：Docs写作、Sheets分析、Slides生成、Meet字幕

**优势**：协作强、实时同步

**不足**：功能较基础、高级功能少

**适用场景**：团队协作、在线办公

### 3. Notion AI 🟨

**核心功能**：内容生成、摘要提取、智能分类、数据库填充

**优势**：功能全面、模板丰富

**不足**：离线能力弱、移动端体验一般

**适用场景**：知识管理、项目管理

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Microsoft 365 Copilot | Office全套AI | 集成深 | 企业版 | 企业办公 | 含Microsoft 365 |
| Google Workspace AI | Google全套AI | 协作强 | 功能基础 | 团队协作 | 含Workspace |
| Notion AI | 内容生成 | 功能全 | 离线弱 | 知识管理 | 个人免费/团队付费 |
| WPS AI | 国产办公 | 免费中文 | 功能少 | 个人办公 | 免费+增值 |
| 石墨文档 AI | 协作编辑 | 实时协作 | AI功能新 | 团队文档 | 免费+增值 |
| 飞书多维表格 | 数据管理 | 强大表格 | 生态小 | 数据管理 | 免费+增值 |

---

## 💡 选购建议

1. **企业用户**：Microsoft 365 Copilot
2. **团队协作**：Google Workspace 或 飞书
3. **个人/知识工作者**：Notion AI
4. **中文免费**：WPS AI

---

## 🔮 未来展望

AI办公将成为标配，告别重复劳动，专注创造价值！

---

*本文由AI生成，仅供参考*"""
    
    def _get_audio_tools_template_article(self) -> str:
        return f"""# 🎙️ {datetime.now().strftime("%Y年%m月%d日")} AI音频工具大横评：谁才是内容创作者的最佳选择？

## 📝 引言

AI音频正在改变内容创作！从语音合成到音乐生成，AI让每个人都能成为音频创作者。今天，我们来深度横评主流AI音频工具。

---

## 🎙️ 主流AI音频工具横评

### 1. ElevenLabs 🔵

**核心功能**：文本转语音、语音克隆、多语言

**优势**：质量最高、支持中文

**不足**：付费、需科学上网

**适用场景**：专业配音

### 2. Audiobox 🖤

**核心功能**：语音合成、声音生成、编辑

**优势**：开源免费、功能强

**不足**：上手较难

**适用场景**：开发者

### 3. 剪映AI 🎵

**核心功能**：AI配音、语音克隆

**优势**：免费、国内生态好

**不足**：功能有限

**适用场景**：视频创作

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| ElevenLabs | 文本转语音 | 质量高 | 付费 | 专业配音 | 付费 |
| Audiobox | 语音合成 | 开源免费 | 上手难 | 开发 | 免费 |
| Cope | AI音乐 | 功能全 | 付费 | 音乐 | 付费 |
| 剪映AI | AI配音 | 免费 | 功能少 | 视频 | 免费 |
| 讯飞智文 | 语音合成 | 中文 | 有限 | 国内 | 免费 |
| 米可智能 | 语音合成 | 中文免费 | 新品 | 中文 | 免费 |

---

## 💡 选购建议

1. **专业配音**：ElevenLabs
2. **视频创作**：剪映AI
3. **中文用户**：米可智能

---

## 🔮 未来展望

AI音频将让每个人都能创作播客和音乐！

---

*本文由AI生成，仅供参考*"""
    
    def _get_code_tools_template_article(self) -> str:
        return f"""# 💻 {datetime.now().strftime("%Y年%m月%d日")} AI编程工具大横评：谁才是开发者的最佳拍档？

## 📝 引言

AI正在彻底改变编程方式。从Copilot到Claude，每个开发者都在寻找最佳的AI编程助手。今天，我们来深度横评主流AI编程工具。

---

## 💻 主流AI编程工具横评

### 1. GitHub Copilot 🔵

**核心功能**：代码补全、函数生成、注释转代码

**优势**：集成VS Code、生态完善

**不足**：需要付费、个人隐私考量

**适用场景**：日常开发、学习编程

### 2. Claude AI 🖤

**核心功能**：代码理解、重构、Debug、性能优化

**优势**：理解力强、输出质量高

**不足**：需要复制粘贴

**适用场景**：复杂项目、重构

### 3. Cursor 🔷

**核心功能**：AI IDE、对话编程、零-shot

**优势**：原生AI设计、体验流畅

**不足**：功能有限、需付费

**适用场景**：AI优先开发

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| GitHub Copilot | 代码补全 | 生态好 | 付费 | 开发 | $10/月 |
| Claude AI | 代码理解 | 质量高 | 需粘贴 | 重构 | 免费/付费 |
| Cursor | AI IDE | 体验好 | 有限 | AI开发 | 免费 |
| Replit AI | 在线IDE | 云端 | 功能少 | 学习 | 免费 |
| CodeWhisperer | 代码补全 | 免费 | 功能少 | AWS | 免费 |
| 通义灵码 | 代码补全 | 中文 | 起步晚 | 中文开发 | 免费 |

---

## 💡 选购建议

1. **日常开发**：GitHub Copilot
2. **复杂重构**：Claude AI
3. **AI优先**：Cursor
4. **中文用户**：通义灵码

---

## 🔮 未来展望

AI编程将成为开发标配，让我们拭目以待！

---

*本文由AI生成，仅供参考*"""
    
    def _get_search_tools_template_article(self) -> str:
        return f"""# 🔍 {datetime.now().strftime("%Y年%m月%d日")} AI搜索工具大横评：谁才是信息检索的未来？

## 📝 引言

传统搜索引擎正在被AI颠覆。从Perplexity到ChatGPT Search，从Kimi到秘塔AI，各类AI搜索工具层出不穷。今天，我们来深度横评市面上主流的AI搜索工具。

---

## 🔍 主流AI搜索工具横评

### 1. Perplexity 🔵

**核心功能**：AI原生搜索、追问功能、来源标注

**优势**：回答准确、实时性强、体验流畅

**不足**：免费版有限制、需要科学上网

**适用场景**：学术研究、专业查询

### 2. ChatGPT Search 🔷

**核心功能**：GPT-4驱动、上下文理解、多模态

**优势**：理解能力强、生态完善

**不足**：响应较慢、部分地区不可用

**适用场景**：复杂问题、内容创作

### 3. Kimi 🇨🇳

**核心功能**：中文优化、长文本处理、免费使用

**优势**：中文体验好、完全免费

**不足**：英文能力相对弱

**适用场景**：中文用户、日常查询

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Perplexity | AI搜索 | 准确实时 | 需翻墙 | 研究 | 付费 |
| ChatGPT Search | AI搜索 | 理解强 | 响应慢 | 创作 | 付费 |
| Kimi | AI搜索 | 中文免费 | 英文弱 | 中文用户 | 免费 |
| 秘塔AI搜索 | AI搜索 | 中文优化 | 起步晚 | 国内用户 | 免费 |
| 百度AI搜索 | AI搜索 | 生态完整 | 广告多 | 日常 | 免费 |
| 360 AI搜索 | AI搜索 | 安全好 | 能力一般 | 安全需求 | 免费 |

---

## 💡 选购建议

1. **专业研究**：Perplexity
2. **中文用户**：Kimi、秘塔AI
3. **日常使用**：百度AI搜索
4. **内容创作**：ChatGPT Search

---

## 🔮 未来展望

AI搜索将取代传统搜索引擎，成为信息获取的主要方式。

---

*本文由AI生成，仅供参考*"""
    
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
        
        # 如果所有LLM都失败，返回模板文章
        logger.warning("所有LLM都不可用，使用模板文章")
        return self._get_image_tools_template_article()
    
    def _get_image_tools_template_article(self) -> str:
        """获取AI绘画工具模板文章（当所有LLM都不可用时）"""
        today = datetime.now().strftime("%Y年%m月%d日")
        
        return f"""# 🎨 {today} AI绘画工具大横评：哪款最适合你？

## 📝 引言

AI绘画工具在近两年经历了爆发式增长，从Midjourney到DALL-E，从Stable Diffusion到Adobe Firefly，各类工具层出不穷。今天，我们就来深度横评市面上主流的AI绘画工具，帮你找到最适合的那一款。

---

## 🔍 主流AI绘画工具横评

### 1. Midjourney 🟣

**核心功能：**
- 文本到图像生成
- 风格化渲染
- 图像微调与扩展
- 参数精确控制

**优势：**
- 艺术感极强
- 社区活跃
- 提示词门槛低

**不足：**
- 需要discord使用
- 付费订阅

**适用场景：** 艺术创作、广告设计

### 2. DALL-E (OpenAI) 🔵

**核心功能：**
- 文本到图像生成
- 图像编辑
- 变体生成
- GPT-4集成

**优势：**
- 生成质量稳定
- 易于使用
- API完善

**不足：**
- 价格较高
- 风格有限

**适用场景：** 产品设计、内容创作

### 3. Stable Diffusion 🔵🟢

**核心功能：**
- 本地部署
- 完全开源
- LoRA微调
- ControlNet控制

**优势：**
- 完全免费
- 可本地运行
- 高度定制

**不足：**
- 需要硬件配置
- 上手门槛高

**适用场景：** 进阶用户、研究人员

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Midjourney | AI绘画 | 艺术感强 | 需discord | 设计创作 | $10/月 |
| DALL-E | AI绘画 | 质量稳定 | 价格高 | 产品设计 | $0.04/图 |
| Stable Diffusion | 本地AI绘画 | 完全免费 | 需硬件 | 研究/进阶 | 免费 |
| Adobe Firefly | AI绘画 | 商业安全 | 功能少 | 商业设计 | 免费/付费 |
| Leonardo.ai | AI绘画 | 功能丰富 | 需排队 | 创作训练 | 免费/付费 |

---

## 💡 选购建议

1. **新手入门**：推荐DALL-E或Midjourney，上手简单
2. **进阶创作**：推荐Stable Diffusion+ControlNet
3. **商业使用**：推荐Adobe Firefly（法律风险低）
4. **爱好者**：推荐Leonardo.ai（免费额度多）

---

## 🔮 未来展望

AI绘画工具将继续进化：
- 视频生成
- 3D模型生成
- 更精准的控制
- 更低的使用门槛

敬请期待！

---

*本文由AI生成，仅供参考*"""

    def _get_note_tools_template_article(self) -> str:
        """获取AI笔记工具模板文章"""
        today = datetime.now().strftime("%Y年%m月%d日")
        
        return f"""# 📝 {today} AI笔记工具大横评：哪款才是你的最佳拍档？

## 📝 引言

在AI时代，笔记工具不再只是简单的记录文字，而是成为了我们的"第二大脑"。从Notion AI到Obsidian，从Apple Notes到Evernote，各类AI笔记工具层出不穷。今天，我们来深度横评市面上主流的AI笔记工具，帮你找到最适合的那一款。

---

## 🔍 主流AI笔记工具横评

### 1. Notion AI 📝

**核心功能：**
- AI写作助手
- 自动汇总会议纪要
- 智能整理笔记
- 内容改写与润色

**优势：**
- 功能全面，生态丰富
- 团队协作强大
- 模板库丰富

**不足：**
- 需要网络访问
- 免费版功能有限

**适用场景：** 团队协作、项目管理

### 2. Apple Notes AI 🍎

**核心功能：**
- 智能搜索
- 录音转文字
- 自动整理笔记

**优势：**
- 苹果生态深度集成
- 免费使用
- 隐私保护强

**不足：**
- AI功能相对基础
- 仅限苹果设备

**适用场景：** 苹果用户日常记录

### 3. Obsidian + AI插件 🔮

**核心功能：**
- 双向链接
- 本地优先存储
- AI写作与问答

**优势：**
- 完全免费（基础功能）
- 可自定义工作流
- 插件生态丰富

**不足：**
- 需要一定学习成本
- 移动端体验一般

**适用场景：** 知识管理、写作爱好者

---

## 📊 综合对比表格

| 工具名称 | 核心功能 | 优势 | 不足 | 适用场景 | 价格 |
|----------|----------|------|------|----------|------|
| Notion AI | AI写作、汇总 | 功能全面 | 需付费 | 团队协作 | 免费/付费 |
| Apple Notes | 搜索、录音 | 免费生态好 | AI功能弱 | 苹果用户 | 免费 |
| Obsidian AI | 本地笔记、链接 | 灵活免费 | 上手难 | 知识管理 | 免费 |
| Microsoft OneNote | 墨迹、搜索 | Office集成 | 功能陈旧 | 企业用户 | 免费 |
| Evernote | 剪藏、搜索 | 老牌稳定 | 价格高 | 进阶用户 | 付费 |
| Google Keep | 快速记录 | 简洁免费 | 功能少 | 轻量记录 | 免费 |

---

## 💡 选购建议

1. **团队协作**：Notion AI 是首选
2. **苹果生态用户**：Apple Notes 足够日常使用
3. **知识管理爱好者**：Obsidian 灵活性最高
4. **企业用户**：Microsoft OneNote 集成度高

---

## 🔮 未来展望

AI笔记工具将继续进化：
- 更智能的内容理解
- 跨平台同步增强
- 个性化推荐

敬请期待！

---

*本文由AI生成，仅供参考*"""
    
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
        
        # 如果所有LLM都失败，返回模板文章
        logger.warning("所有LLM都不可用，使用模板文章")
        return self._get_template_article()
    
    def _get_template_article(self) -> str:
        """获取模板文章（当所有LLM都不可用时）"""
        today = datetime.now().strftime("%Y年%m月%d日")
        
        return f"""# 🎯 {today} AI会议工具大横评：哪款最适合你？

## 📝 引言

在远程办公和混合办公成为常态的今天，AI会议工具已经成为提升工作效率的必备利器。这些工具不仅能自动记录会议内容，还能生成摘要、提取待办事项，甚至提供实时翻译。今天，我们就来深度横评市面上主流的AI会议工具，帮你找到最适合的那一款。

---

## 🔍 主流AI会议工具横评

### 1. Zoom AI Companion 🟢

**核心功能：**
- 实时会议摘要
- 智能待办事项提取
- 会议录制与转录
- 实时翻译支持

**优势：**
- 与Zoom深度集成，使用无缝
- 支持多种语言
- 准确率高

**不足：**
- 需要付费订阅
- 对网络要求较高

**适用场景：** 已经使用Zoom的企业用户

### 2. Microsoft Teams Copilot 🔵

**核心功能：**
- 会议智能回顾
- 实时协作增强
- 与Office 365深度集成
- 智能内容生成

**优势：**
- 与微软生态系统完美融合
- 功能全面强大
- 企业级安全

**不足：**
- 需要Microsoft 365订阅
- 学习曲线较陡

**适用场景：** 微软生态企业用户

### 3. Google Meet Gemini 🟡

**核心功能：**
- 实时字幕与翻译
- 会议笔记自动生成
- 智能噪音消除
- 画质增强

**优势：**
- 与Google Workspace集成
- 界面简洁易用
- 免费版功能实用

**不足：**
- 高级功能需要付费
- 在某些地区网络不稳定

**适用场景：** Google生态用户、小型团队

### 4. 腾讯会议AI助手 🔴

**核心功能：**
- 智能会议纪要
- 待办事项自动提取
- 实时字幕
- 会议录制管理

**优势：**
- 国内网络稳定
- 中文支持优秀
- 免费版功能丰富

**不足：**
- 国际化支持有限
- 高级功能需要企业版

**适用场景：** 国内企业、中文会议为主

### 5. 飞书妙记 🟣

**核心功能：**
- 智能语音转文字
- 会议内容智能分析
- 多语言实时翻译
- 与飞书生态深度集成

**优势：**
- 识别准确率高
- 与飞书办公套件无缝集成
- 支持多种方言

**不足：**
- 主要面向飞书用户
- 独立使用受限

**适用场景：** 飞书生态用户、字节系企业

---

## 📊 综合对比

| 工具 | 价格 | 中文支持 | 功能完整度 | 生态集成 | 推荐指数 |
|------|------|----------|------------|----------|----------|
| Zoom AI | 💰💰💰 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Teams Copilot | 💰💰💰 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Google Gemini | 💰💰 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 腾讯会议 | 💰 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 飞书妙记 | 💰💰 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 💡 选购建议

### 按企业规模选择：
- **初创公司/小型团队**：腾讯会议（免费版）或 Google Meet
- **中型企业**：根据现有办公套件选择
- **大型企业**：Microsoft Teams Copilot 或 Zoom Enterprise

### 按使用场景选择：
- **国际会议为主**：Zoom 或 Microsoft Teams
- **国内会议为主**：腾讯会议或飞书妙记
- **跨平台协作**：Google Meet

---

## 🔮 未来发展趋势

1. **多模态融合**：结合视频、音频、文本的全方位理解
2. **个性化定制**：根据用户习惯提供定制化服务
3. **安全隐私增强**：端到端加密和隐私保护
4. **跨平台互通**：不同工具间的数据互通
5. **AI深度集成**：从辅助工具变为核心生产力

---

## 📢 总结

选择AI会议工具时，需要综合考虑企业现有生态、预算、使用场景等因素。没有绝对最好的工具，只有最适合的工具。建议先试用免费版本，再根据实际需求决定是否升级付费版本。

希望这篇横评能帮助你找到最适合的AI会议工具！如果有任何问题，欢迎在评论区留言讨论。

---

📅 *本文由 AI 辅助生成，发布于{today}*
🔔 *关注我们，获取更多AI工具评测和使用技巧*"""

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
    article = generator.generate_meeting_tools_review()
    print(f"文章生成完成，长度: {len(article)} 字符")
    print("\n预览前500字符:")
    print(article[:500])