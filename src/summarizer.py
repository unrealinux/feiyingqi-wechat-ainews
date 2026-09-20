"""
AI News Summarizer - AI 摘要生成模块

使用 OpenAI GPT 生成专业的公众号文章
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from src.config import load_config, get_llm_config
from src.fetcher import NewsItem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """LLM 不可用（未配置 / 调用失败）时抛出。

    AGENTS.md 红线：禁止用模板拼贴的 mock 文本充当原创内容。
    因此定时流水线必须 fail-closed：宁可本次不产出，也不往草稿箱塞低质稿。
    """


# 文本 LLM 提供商表：name -> (config 段, 默认 base_url, 默认模型, 环境变量, 段内模型键)
# 只要目标服务兼容 OpenAI /chat/completions，就能直接接入。
# 注意 agnes 段的 model 是封面图模型，所以文本模型另用 text_model 键，避免拿图片模型去写文章。
_LLM_PROVIDERS = {
    "agnes":       ("agnes",       "https://apihub.agnes-ai.com/v1",       "agnes-3.0-flash",
                    "AGNES_API_KEY",        "text_model"),
    "deepseek":    ("deepseek",    "https://api.deepseek.com/v1",          "deepseek-chat",
                    "DEEPSEEK_API_KEY",     "model"),
    "zhipu":       ("zhipu",       "https://open.bigmodel.cn/api/paas/v4",  "glm-4-flash",
                    "ZHIPU_API_KEY",        "model"),
    "siliconflow": ("siliconflow", "https://api.siliconflow.cn/v1",        "Qwen/Qwen2.5-7B-Instruct",
                    "SILICONFLOW_API_KEY",  "model"),
    "openrouter":  ("openrouter",  "https://openrouter.ai/api/v1",         "google/gemini-2.0-flash-001",
                    "OPENROUTER_API_KEY",   "model"),
    "openai":      ("openai",      None,                                   "gpt-4o-mini",
                    "OPENAI_API_KEY",       "model"),
}

# llm.provider = auto 时的探测顺序（先挑当前最可用的）
_AUTO_ORDER = ["agnes", "deepseek", "zhipu", "siliconflow", "openrouter", "openai"]


def _resolve_provider(config: dict, name: str) -> Optional[dict]:
    """按提供商名解析出 api_key / base_url / model（密钥优先取环境变量/.env）。"""
    spec = _LLM_PROVIDERS.get(name)
    if not spec:
        return None
    section, default_base, default_model, env_name, model_key = spec
    cfg = config.get(section, {}) or {}
    api_key = cfg.get("api_key") or os.environ.get(env_name, "")
    if api_key == "your_openai_api_key_here":
        api_key = ""
    return {
        "provider": name,
        "api_key": api_key,
        "base_url": cfg.get("base_url") or default_base,
        "model": cfg.get(model_key) or default_model,
    }


class Summarizer:
    """AI 摘要生成器"""
    
    def __init__(self):
        config = load_config()
        llm_config = get_llm_config(config)
        requested = (llm_config.get("provider") or "auto").strip().lower()

        if requested in _LLM_PROVIDERS:
            candidates = [requested]
        else:
            if requested != "auto":
                logger.warning(f"未知的 llm.provider='{requested}'，回退到 auto 探测")
            candidates = _AUTO_ORDER

        # 选定第一个真正带 api_key 的提供商
        chosen = None
        for name in candidates:
            resolved = _resolve_provider(config, name)
            if resolved and resolved["api_key"]:
                chosen = resolved
                break

        if not chosen:
            logger.warning(
                "未找到可用的 LLM API Key（检查 .env 与 llm.provider）。将拒绝生成 mock 稿件。"
            )
            self.provider = None
            self.api_key = ""
            self.model = ""
            self.base_url = None
            self.client = None
        else:
            self.provider = chosen["provider"]
            self.api_key = chosen["api_key"]
            # llm.model 仅在显式指定 provider 时生效；auto 模式一律用该提供商默认模型
            override = llm_config.get("model") if requested in _LLM_PROVIDERS else ""
            self.model = override or chosen["model"]
            self.base_url = chosen["base_url"]
            logger.info(f"LLM provider: {self.provider} | model: {self.model} | base_url: {self.base_url}")

        if not self.api_key:
            self.client = None
        else:
            try:
                from openai import OpenAI
                # 设置超时和重试参数
                kwargs = {
                    "api_key": self.api_key,
                    "timeout": 30.0,  # 30秒超时
                    "max_retries": 1  # 最多重试1次
                }
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                
                self.client = OpenAI(**kwargs)
                logger.info(f"OpenAI client initialized ({self.model}, base_url={self.base_url})")
            except ImportError:
                logger.warning("openai library not installed")
                self.client = None
    
    def summarize_news(self, news_items: List[NewsItem], allow_mock: bool = True) -> str:
        """生成公众号文章

        Args:
            news_items: 新闻素材
            allow_mock: 是否允许在 LLM 不可用时降级为模板拼贴。
                默认 True 仅为兼容测试/本地预览；定时发布链传 False，
                这样 LLM 失败会抛错而不是生成低质稿（详见 AGENTS.md）。
        """
        if not self.client or not news_items:
            if not allow_mock:
                raise LLMUnavailableError(
                    "LLM 客户端不可用（未配置 API Key 或 openai 库缺失），拒绝生成 mock 稿件"
                )
            return self._mock_summarize(news_items)
        
        news_content = self._prepare_news_content(news_items)
        
        system_prompt = """你是一位资深 AI 领域深度观察者，擅长从新闻素材中提炼独特视角，写出有观点、有深度的原创评论。
写作要求：每篇独立构思，杜绝模板化套路；标题不落俗套，有钩子但不过度夸张；避免反复使用固定句式和结构。
对每条素材做事实性转述，不编造数据、不虚构人物，所有论断都必须来自给定素材。"""

        user_prompt = f"""请基于以下 AI 新闻素材，为微信公众号撰写一篇深度原创文章。

写作要求：
1. 从多条素材中提炼一个有价值的核心观点或主题，围绕它展开（而非逐条罗列成日报）
2. 标题要有辨识度，能引发思考，不使用"XX日报""今日速递"类模板词，不用 emoji 堆砌
3. 结构自然流畅，可以有小标题分区，但不要固定分类；允许"引申/反问/对比"等评论性段落
4. 每条重要事实后标注来源（Markdown 格式 [来源](链接)），确保可溯源
5. 结尾有一段作者视角的总结，发出值得读者思考的问题，输出观点而非情绪
6. 语言专业但有温度，去 AI 味

今日 AI 新闻素材：

{news_content}

请直接输出公众号文章内容（Markdown 格式），不要添加额外说明。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.9,
                max_tokens=4000,
                timeout=60
            )
            
            article = response.choices[0].message.content
            if article:
                logger.info(f"Article generated by {self.model}")
                return article
            if not allow_mock:
                raise LLMUnavailableError("LLM 返回空内容，拒绝生成 mock 稿件")
            return self._mock_summarize(news_items)
            
        except LLMUnavailableError:
            raise
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            if not allow_mock:
                raise LLMUnavailableError(f"LLM 调用失败: {e}") from e
            return self._mock_summarize(news_items)
    
    def generate_editorial_spec(self, news_items: List[NewsItem],
                                allow_mock: bool = False) -> dict:
        """生成「深读」结构化内容（供 src/editorial_template 渲染固定排版）。

        与 summarize_news 的区别：这里让模型只输出 **内容字段的 JSON**，
        排版由本地模版确定性拼装，避免模型手写 CSS 造成各篇观感漂移。
        """
        from src.editorial_template import (EDITORIAL_SCHEMA_DOC, EditorialSpecError, extract_json,
                                            validate_spec, ground_numeric_blocks,
                                            find_blacklisted_terms, normalize_meta_date,
                                            find_ungrounded_numbers)

        if not self.client or not news_items:
            raise LLMUnavailableError(
                "LLM 客户端不可用（未配置 API Key 或 openai 库缺失），拒绝生成内容"
            )

        news_content = self._prepare_news_content(news_items)
        today = datetime.now().strftime("%Y年%m月%d日")

        system_prompt = (
            "你是资深 AI 领域深度观察者，写有观点、有出处的原创分析。"
            "你只能使用给定的新闻素材和公开可查的信息，禁止编造数据、人物、机构或引语。"
            "绝对禁止模板句式与空话（如“不是替代……而是让……更……”“总而言之机遇与挑战并存”）。"
        )

        user_prompt = f"""基于下面的 AI 新闻素材，写一篇公众号「深读」文章，并**只输出一个 JSON 对象**（不要 Markdown 围栏、不要多余说明）。

JSON 结构如下：
{EDITORIAL_SCHEMA_DOC}

写作要求：
0. meta_line 必须以今天的日期开头，格式：{today} ｜ 一句话说明本篇看什么（不要用新闻发生日）。
1. 从多条素材中找一条**能立得住的主线**，围绕它展开观点，绝不逐条罗列新闻。
2. title 要有辨识度和钩子，可用 \\n 手工断行，不超过 30 字；禁止“日报/速递/盘点”类模板词，不用 emoji。
3. sections 写 4～6 节，每节 2～4 个内容块；accent 在 red / green 之间交替。
4. 至少用 1 个 datacard 或 bars 承载具体数字；**数字必须直接来自上面的素材文本**（原文里没出现的百分比、年份、金额一律不写）。
5. **素材中没有的具体数字、材料名、公司名、人物名一律不得写入**；宁少勿编。
6. sources 至少 3 条，写清“机构/文章名 + 链接或可查标识”；**正文里引用过哪条新闻，sources 里就必须列出哪条**（含中文媒体来源）。
7. closing 用两段收束，给出作者视角的判断，不发散情绪；全文观点必须一致，不得出现与主线相矛盾的表述（例如一边论证算力受限，一边又说“算力过剩”）。
8. 英文专有名词按本义翻译：mouse=小鼠（**不是鼠标**）、model=模型、agent=智能体；不确定的译名宁可用英文原名。
9. 全文中文，总长约 2500～3500 字；段落可用 **加粗** 强调关键词。

今日 AI 新闻素材：

{news_content}
"""

        last_error = None
        for attempt in (1, 2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.85 if attempt == 1 else 0.5,
                    max_tokens=6000,
                    timeout=180,
                )
                raw = response.choices[0].message.content or ""
                spec = extract_json(raw)
                validate_spec(spec)

                # 译名雷区（如 mouse→鼠标）命中则整体重生成，不放过
                bad_terms = find_blacklisted_terms(spec)
                if bad_terms:
                    raise EditorialSpecError(f"译名错误: {'、'.join(bad_terms)}")

                # 数字溯源：素材里没有的数字不允许上图（AGENTS.md 禁编造数据）
                dropped = ground_numeric_blocks(spec, news_content)
                if dropped:
                    logger.warning("剔除无出处的图表数据: " + "; ".join(dropped))

                normalize_meta_date(spec)
                validate_spec(spec)

                ungrounded = find_ungrounded_numbers(spec, news_content)
                if ungrounded:
                    logger.warning(
                        "正文中存在素材未出现的数字（请人工复核是否真实）: " + "、".join(ungrounded)
                    )
                logger.info(
                    f"Editorial spec generated by {self.model} "
                    f"({len(spec.get('sections', []))} 节, {len(raw)} 字符)"
                )
                return spec
            except LLMUnavailableError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"结构化内容第 {attempt} 次生成失败: {e}")

        raise LLMUnavailableError(f"结构化内容生成失败: {last_error}")

    def _prepare_news_content(self, news_items: List[NewsItem]) -> str:
        """准备新闻素材文本"""
        """准备新闻素材文本"""
        content_parts = []
        
        for i, item in enumerate(news_items, 1):
            source_info = f"[{item.source}]" if item.source else ""
            content_parts.append(f"""
{i}. {source_info}{item.title}
   摘要：{item.description or "暂无摘要"}
   链接：{item.url}
""")
        
        return "\n".join(content_parts)
    
    def _mock_summarize(self, news_items: List[NewsItem]) -> str:
        """模拟摘要（无 API 时使用）"""
        today = datetime.now().strftime("%Y年%m月%d日")
        
        categories = self._categorize_news(news_items)
        
        article_parts = [
            f"# 🎯 {today} AI 资讯日报",
            "",
            f"各位读者朋友们，大家好！今天是{today}，让我们一起来看看 AI 领域又有哪些最新动态。",
            "",
            "---",
            ""
        ]
        
        for category, items in categories.items():
            emoji = self._get_category_emoji(category)
            article_parts.append(f"## {emoji} {category}")
            article_parts.append("")
            
            for item in items:
                article_parts.append(f"**{item.title}**")
                if item.description:
                    article_parts.append(f">{item.description}")
                if item.url:
                    article_parts.append(f"[原文链接]({item.url})")
                article_parts.append("")
        
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
        
        logger.info("Mock summary generated")
        return "\n".join(article_parts)
    
    def _categorize_news(self, news_items: List[NewsItem]) -> dict:
        """简单分类"""
        categories = {}
        
        for item in news_items:
            source = item.source.lower() if item.source else ""
            
            if any(kw in source for kw in ["openai"]):
                cat = "OpenAI 动态"
            elif any(kw in source for kw in ["google", "deepmind"]):
                cat = "Google DeepMind 动态"
            elif any(kw in source for kw in ["microsoft"]):
                cat = "Microsoft 动态"
            elif any(kw in source for kw in ["anthropic"]):
                cat = "Anthropic 动态"
            elif any(kw in source for kw in ["meta"]):
                cat = "Meta 动态"
            else:
                cat = "行业资讯"
            
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        return categories
    
    def _get_category_emoji(self, category: str) -> str:
        """获取分类 emoji"""
        emojis = {
            "OpenAI 动态": "🟢",
            "Google DeepMind 动态": "🔵",
            "Microsoft 动态": "💻",
            "Anthropic 动态": "🤖",
            "Meta 动态": "📘",
            "行业资讯": "📰",
        }
        return emojis.get(category, "📌")


def generate_article(news_items: List[NewsItem], save_to_file: bool = True,
                     allow_mock: bool = True) -> str:
    """生成文章的便捷函数

    allow_mock=False 时，LLM 不可用会抛 LLMUnavailableError（定时发布链路用）。
    """
    summarizer = Summarizer()
    article = summarizer.summarize_news(news_items, allow_mock=allow_mock)
    
    if save_to_file:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        md_filename = output_dir / f"article_{today}.md"
        
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(article)
        
        logger.info(f"Article saved: {md_filename}")
    
    return article


if __name__ == "__main__":
    from src.fetcher import fetch_news, get_mock_news
    
    print("Testing summarizer with mock data...")
    mock_news = get_mock_news(5)
    
    article = generate_article(mock_news)
    print("\n" + "="*50)
    print(article[:2000])
