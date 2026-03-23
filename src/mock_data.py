"""
Mock Data Module - 模拟数据模块

参考 feiqingqiWechatMP 的 crawler.js 模拟数据功能
提供网络受限时的自动切换到模拟数据的能力
"""
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.logger import get_logger


logger = get_logger(__name__)


@dataclass
class MockNewsItem:
    """模拟新闻项"""
    title: str
    url: str
    source: str
    description: str = ""
    published_at: str = ""
    category: str = "general"
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "description": self.description,
            "published_at": self.published_at,
            "category": self.category
        }


class MockDataGenerator:
    """模拟数据生成器"""
    
    # 模拟新闻模板
    NEWS_TEMPLATES = [
        {
            "title": "OpenAI 发布最新 GPT-5 模型，性能大幅提升",
            "source": "OpenAI",
            "category": "大模型进展",
            "description": "OpenAI 宣布推出 GPT-5，新模型在推理能力和多模态理解方面有显著突破"
        },
        {
            "title": "Google DeepMind 发布 AlphaFold 3，预测精度再创新高",
            "source": "Google DeepMind",
            "category": "AI 研究",
            "description": "DeepMind 最新蛋白质结构预测模型，能够预测蛋白质与其他分子的相互作用"
        },
        {
            "title": "微软推出 Copilot+ PC，AI 功能全面集成 Windows",
            "source": "Microsoft",
            "category": "AI 应用",
            "description": "微软发布新一代 PC 架构，AI 能力深度集成到操作系统层面"
        },
        {
            "title": "Anthropic 发布 Claude 4，主打安全性和可控性",
            "source": "Anthropic",
            "category": "大模型进展",
            "description": "Claude 4 在安全对齐方面取得重大进展，同时保持强大的推理能力"
        },
        {
            "title": "Meta 开源 Llama 4，性能超越闭源模型",
            "source": "Meta",
            "category": "开源动态",
            "description": "Meta 发布 Llama 4 系列模型，参数规模和创新架构引发业界关注"
        },
        {
            "title": "特斯拉 Optimus 机器人开始量产，成本大幅降低",
            "source": "Tesla",
            "category": "机器人",
            "description": "特斯拉人形机器人 Optimus 开始小规模量产，成本降低至 2 万美元以下"
        },
        {
            "title": "英伟达发布新一代 AI 芯片，算力提升 5 倍",
            "source": "NVIDIA",
            "category": "硬件",
            "description": "英伟达发布最新一代 AI 加速芯片，算力大幅提升，能效比显著改善"
        },
        {
            "title": "百度文心一言 5.0 发布，中文能力超越 GPT-4",
            "source": "百度",
            "category": "国产大模型",
            "description": "百度发布文心一言 5.0 版本，在中文理解和生成能力上超越 GPT-4"
        },
        {
            "title": "阿里通义千问 3.0 发布，支持多模态理解",
            "source": "阿里巴巴",
            "category": "国产大模型",
            "description": "阿里发布通义千问 3.0，支持文本、图像、音频、视频的多模态理解"
        },
        {
            "title": "字节跳动发布豆包大模型，主打轻量高效",
            "source": "字节跳动",
            "category": "国产大模型",
            "description": "字节跳动发布豆包大模型，在保持高性能的同时大幅降低计算资源需求"
        },
        {
            "title": "Stability AI 发布 Stable Diffusion 4，生成质量媲美专业摄影",
            "source": "Stability AI",
            "category": "AI 生成",
            "description": "Stability AI 发布最新图像生成模型，生成质量达到专业摄影水平"
        },
        {
            "title": "Midjourney V7 发布，支持视频生成",
            "source": "Midjourney",
            "category": "AI 生成",
            "description": "Midjourney 发布 V7 版本，首次支持文本到视频的生成能力"
        },
        {
            "title": "GitHub Copilot 用户突破 1000 万，开发者生产力大幅提升",
            "source": "GitHub",
            "category": "开发者工具",
            "description": "GitHub Copilot 用户数量突破 1000 万，平均提升开发者生产力 55%"
        },
        {
            "title": "AWS 发布 Amazon Q，企业级 AI 助手正式商用",
            "source": "AWS",
            "category": "企业服务",
            "description": "AWS 发布企业级 AI 助手 Amazon Q，支持代码生成、数据分析等场景"
        },
        {
            "title": "DeepMind 发表论文，AI 在数学推理上取得突破",
            "source": "Google DeepMind",
            "category": "AI 研究",
            "description": "DeepMind 最新研究表明，AI 在复杂数学推理任务上首次超越人类专家"
        },
        {
            "title": "欧盟通过 AI 法案，全球首个全面监管框架",
            "source": "欧盟",
            "category": "政策法规",
            "description": "欧盟正式通过 AI 法案，成为全球首个全面监管人工智能的法律框架"
        },
        {
            "title": "OpenAI 推出 Sora 2，视频生成质量达到电影级别",
            "source": "OpenAI",
            "category": "AI 生成",
            "description": "OpenAI 发布 Sora 2，视频生成质量达到电影级别，引发影视行业震动"
        },
        {
            "title": "华为发布盘古大模型 5.0，专注行业应用",
            "source": "华为",
            "category": "国产大模型",
            "description": "华为发布盘古大模型 5.0，专注金融、医疗、制造等行业应用场景"
        },
        {
            "title": "特斯拉 FSD V13 发布，自动驾驶安全性提升 10 倍",
            "source": "Tesla",
            "category": "自动驾驶",
            "description": "特斯拉发布 FSD V13 版本，自动驾驶安全性相比上一代提升 10 倍"
        },
        {
            "title": "Anthropic 获得 50 亿美元融资，估值超过 300 亿",
            "source": "Anthropic",
            "category": "融资动态",
            "description": "Anthropic 完成 50 亿美元融资，估值超过 300 亿美元，成为 AI 领域独角兽"
        }
    ]
    
    # 国内新闻源
    DOMESTIC_SOURCES = [
        "36kr",
        "量子位",
        "机器之心",
        "虎嗅",
        "极客公园",
        "爱范儿",
        "少数派",
        "知乎",
        "微博",
        "百度"
    ]
    
    # 国际新闻源
    INTERNATIONAL_SOURCES = [
        "OpenAI",
        "Google DeepMind",
        "Microsoft",
        "Anthropic",
        "Meta",
        "Tesla",
        "NVIDIA",
        "Stability AI",
        "Midjourney",
        "GitHub"
    ]
    
    def __init__(self, seed: Optional[int] = None):
        """初始化模拟数据生成器
        
        Args:
            seed: 随机种子，用于生成可重复的模拟数据
        """
        if seed is not None:
            random.seed(seed)
    
    def generate_news(
        self,
        count: int = 10,
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        days_back: int = 7
    ) -> List[MockNewsItem]:
        """生成模拟新闻数据
        
        Args:
            count: 生成的新闻数量
            categories: 筛选的类别列表
            sources: 筛选的来源列表
            days_back: 生成过去多少天的新闻
            
        Returns:
            模拟新闻列表
        """
        # 筛选新闻模板
        templates = self.NEWS_TEMPLATES.copy()
        
        if categories:
            templates = [t for t in templates if t["category"] in categories]
        
        if sources:
            templates = [t for t in templates if t["source"] in sources]
        
        # 如果筛选后没有模板，使用所有模板
        if not templates:
            templates = self.NEWS_TEMPLATES
        
        # 生成新闻
        news_items = []
        today = datetime.now()
        
        for i in range(min(count, len(templates))):
            template = random.choice(templates)
            
            # 生成随机日期
            days_ago = random.randint(0, days_back)
            pub_date = today - timedelta(days=days_ago)
            
            # 生成模拟 URL
            url = f"https://example.com/news/{random.randint(1000, 9999)}"
            
            news_item = MockNewsItem(
                title=template["title"],
                url=url,
                source=template["source"],
                description=template["description"],
                published_at=pub_date.strftime("%Y-%m-%d"),
                category=template["category"]
            )
            
            news_items.append(news_item)
        
        logger.info(f"生成 {len(news_items)} 条模拟新闻")
        return news_items
    
    def generate_domestic_news(self, count: int = 10) -> List[MockNewsItem]:
        """生成国内新闻模拟数据"""
        return self.generate_news(
            count=count,
            sources=self.DOMESTIC_SOURCES
        )
    
    def generate_international_news(self, count: int = 10) -> List[MockNewsItem]:
        """生成国际新闻模拟数据"""
        return self.generate_news(
            count=count,
            sources=self.INTERNATIONAL_SOURCES
        )
    
    def generate_by_category(self, category: str, count: int = 5) -> List[MockNewsItem]:
        """按类别生成模拟数据"""
        return self.generate_news(
            count=count,
            categories=[category]
        )
    
    def generate_article(self, news_items: List[MockNewsItem]) -> str:
        """生成模拟文章"""
        today = datetime.now().strftime("%Y年%m月%d日")
        
        # 按类别分类
        categories = {}
        for item in news_items:
            cat = item.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        # 生成文章
        article_parts = [
            f"# 🎯 {today} AI 资讯日报",
            "",
            f"各位读者朋友们，大家好！今天是{today}，让我们一起来看看 AI 领域又有哪些最新动态。",
            "",
            "---",
            ""
        ]
        
        # 添加分类内容
        for category, items in categories.items():
            emoji = self._get_category_emoji(category)
            article_parts.append(f"## {emoji} {category}")
            article_parts.append("")
            
            for item in items:
                article_parts.append(f"**{item.title}**")
                if item.description:
                    article_parts.append(f">{item.description}")
                article_parts.append(f"[原文链接]({item.url})")
                article_parts.append("")
        
        # 添加结尾
        article_parts.extend([
            "---",
            "",
            "## 💡 今日点评",
            "",
            "AI 领域正在经历快速发展期，各大科技公司纷纷加码布局。" +
            "从今天的资讯来看，大模型能力和应用场景都在持续扩展。" +
            "建议读者朋友们持续关注这一领域的最新发展。",
            "",
            "---",
            "",
            f"📢 *本文由 AI 自动整理汇总，发布于{today}*"
        ])
        
        return "\n".join(article_parts)
    
    def _get_category_emoji(self, category: str) -> str:
        """获取分类 emoji"""
        emojis = {
            "大模型进展": "🧠",
            "AI 研究": "🔬",
            "AI 应用": "🚀",
            "开源动态": "🌐",
            "机器人": "🤖",
            "硬件": "💻",
            "国产大模型": "🇨🇳",
            "AI 生成": "🎨",
            "开发者工具": "👨‍💻",
            "企业服务": "🏢",
            "政策法规": "📜",
            "自动驾驶": "🚗",
            "融资动态": "💰"
        }
        return emojis.get(category, "📌")


# 全局模拟数据生成器
_mock_generator: Optional[MockDataGenerator] = None


def get_mock_generator() -> MockDataGenerator:
    """获取全局模拟数据生成器"""
    global _mock_generator
    if _mock_generator is None:
        _mock_generator = MockDataGenerator()
    return _mock_generator


def generate_mock_news(count: int = 10, **kwargs) -> List[MockNewsItem]:
    """生成模拟新闻的便捷函数"""
    return get_mock_generator().generate_news(count, **kwargs)


def generate_mock_article(news_items: List[MockNewsItem]) -> str:
    """生成模拟文章的便捷函数"""
    return get_mock_generator().generate_article(news_items)


def is_mock_mode_enabled() -> bool:
    """检查是否启用了模拟模式"""
    return os.environ.get("USE_MOCK_DATA", "false").lower() == "true"


def get_mock_mode_reason() -> Optional[str]:
    """获取启用模拟模式的原因"""
    if is_mock_mode_enabled():
        return "环境变量 USE_MOCK_DATA=true"
    return None


if __name__ == "__main__":
    # 测试代码
    generator = MockDataGenerator(seed=42)
    
    # 生成模拟新闻
    news = generator.generate_news(count=5)
    print("生成的模拟新闻:")
    for item in news:
        print(f"  - [{item.source}] {item.title}")
    
    # 生成模拟文章
    article = generator.generate_article(news)
    print("\n生成的模拟文章:")
    print(article[:500] + "...")
