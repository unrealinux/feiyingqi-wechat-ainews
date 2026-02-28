"""
AI Enhancements - 高级 AI 功能

- 多模型支持
- 自定义 Prompt
- 长文章优化
"""

import os
import logging
from typing import List, Optional
from src.config import load_config, get_openai_config
from src.fetcher import NewsItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedSummarizer:
    """增强版 AI 摘要生成器"""
    
    def __init__(self, model: str = None, temperature: float = 0.7):
        config = load_config()
        openai_config = get_openai_config(config)
        
        self.api_key = openai_config.get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or openai_config.get("model", "gpt-4o-mini")
        self.temperature = temperature
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai library not installed")
                self.client = None
        else:
            self.client = None
    
    def generate_with_style(self, news_items: List[NewsItem], 
                           style: str = "professional") -> str:
        """
        按指定风格生成文章
        
        风格选项:
        - professional: 专业科技媒体风格
        - casual: 轻松易懂风格
        - academic: 学术严谨风格
        - marketing: 营销号风格
        """
        style_prompts = {
            "professional": """
你是一位资深科技编辑，文笔专业严谨。
要求：
- 使用专业术语但解释清晰
- 结构清晰，逻辑严密
- 客观中立的语气
""",
            "casual": """
你是一位亲切的科技博主，用轻松的方式讲解技术。
要求：
- 使用口语化表达
- 多用比喻和例子
- 像和朋友聊天一样
""",
            "academic": """
你是一位 AI 领域研究员，撰写学术综述。
要求：
- 严谨的学术语言
- 引用技术细节
- 分析技术影响和意义
""",
            "marketing": """
你是一位擅长吸引眼球的自媒体作者。
要求：
- 使用吸引眼球的标题
- 情绪化的表达
- 强调重要性和紧迫感
""",
        }
        
        system_prompt = style_prompts.get(style, style_prompts["professional"])
        return self._generate_with_prompt(news_items, system_prompt)
    
    def generate_deep_analysis(self, news_items: List[NewsItem]) -> str:
        """生成深度分析文章"""
        
        system_prompt = """你是一位 AI 行业分析师，擅长深度解读技术趋势。

请完成以下任务：
1. 识别今日新闻中的关键趋势
2. 分析技术背后的商业逻辑
3. 预测可能的行业影响
4. 给出专业的投资建议

要求：
- 深度洞察，不是简单总结
- 联系行业背景和历史发展
- 给出独家观点和分析
"""
        
        return self._generate_with_prompt(news_items, system_prompt, max_tokens=6000)
    
    def generate_bulletin(self, news_items: List[NewsItem]) -> str:
        """生成简报（短小精悍）"""
        
        system_prompt = """你是一位高效的新闻编辑，擅长写简报。

要求：
- 每条新闻限制在 30 字以内
- 只保留最关键信息
- 使用 bullet points 格式
- 总长度控制在 500 字以内

格式示例：
📌 今日要点
• 新闻 1（30 字）
• 新闻 2（30 字）
"""
        
        return self._generate_with_prompt(news_items, system_prompt, max_tokens=1000)
    
    def _generate_with_prompt(self, news_items: List[NewsItem], 
                              system_prompt: str, 
                              max_tokens: int = 4000) -> str:
        """使用指定 prompt 生成"""
        if not self.client or not news_items:
            return self._fallback_generate(news_items)
        
        news_content = self._prepare_news(news_items)
        
        user_prompt = f"""今日 AI 资讯素材：

{news_content}

请根据上述素材生成文章。"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=max_tokens,
                timeout=120
            )
            
            article = response.choices[0].message.content
            if article:
                logger.info(f"Generated with {self.model}, {len(article)} chars")
                return article
            
        except Exception as e:
            logger.error(f"API error: {e}")
        
        return self._fallback_generate(news_items)
    
    def _prepare_news(self, news_items: List[NewsItem]) -> str:
        parts = []
        for i, item in enumerate(news_items, 1):
            parts.append(f"{i}. [{item.source}] {item.title}\n   {item.description or '暂无摘要'}\n")
        return "\n".join(parts)
    
    def _fallback_generate(self, news_items: List[NewsItem]) -> str:
        """降级方案"""
        logger.warning("Using fallback generation")
        
        if not news_items:
            return "今日暂无 AI 资讯"
        
        lines = ["# 📰 AI 资讯简报\n"]
        for item in news_items:
            lines.append(f"## {item.title}")
            if item.description:
                lines.append(f">{item.description}\n")
        
        return "\n".join(lines)


class PromptTemplates:
    """Prompt 模板库"""
    
    @staticmethod
    def comparison_analysis() -> str:
        return """分析这几条新闻之间的关联：
1. 技术方案对比
2. 公司战略差异
3. 市场竞争格局
给出你的专业见解。"""
    
    @staticmethod
    def technical_deep_dive() -> str:
        return """从技术角度深入分析：
1. 核心技术突破点
2. 与之前技术的区别
3. 技术实现的难点
4. 可能的应用场景"""
    
    @staticmethod
    def market_impact() -> str:
        return """分析市场影响：
1. 对相关公司股票的影响
2. 行业格局变化
3. 投资机会和风险
4. 对未来发展的预测"""


def quick_test():
    """快速测试"""
    from src.fetcher import get_mock_news
    
    print("Testing Enhanced Summarizer...")
    summarizer = EnhancedSummarizer()
    
    news = get_mock_news(3)
    
    print("\n--- Professional Style ---")
    result = summarizer.generate_with_style(news, "professional")
    print(result[:500])
    
    print("\n--- Bulletin Style ---")
    result = summarizer.generate_bulletin(news)
    print(result)


if __name__ == "__main__":
    quick_test()
