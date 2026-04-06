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


class CustomArticleGenerator:
    """自定义文章生成器"""
    
    def __init__(self):
        self.config = load_config()
        self.domestic_llm = get_domestic_llm()
        self.summarizer = Summarizer()
    
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
   - 综合对比表格
   - 选购建议与使用技巧
   - 未来发展趋势展望
3. 语言风格：专业但生动，适合科技爱好者阅读
4. 字数：3000-4000字
5. 包含适当的emoji和格式化元素

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