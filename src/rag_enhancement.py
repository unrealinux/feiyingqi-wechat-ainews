"""
RAG Enhancement - 检索增强生成

使用历史文章和知识库增强 AI 摘要质量
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_DIR = Path("cache")
KNOWLEDGE_FILE = CACHE_DIR / "knowledge.json"


class KnowledgeBase:
    """简易知识库 - 使用 TF-IDF 相似度"""
    
    def __init__(self):
        self.articles = []
        self.keywords_index = {}
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载知识库"""
        if KNOWLEDGE_FILE.exists():
            try:
                self.articles = json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
                self._build_index()
                logger.info(f"Loaded {len(self.articles)} articles into knowledge base")
            except Exception as e:
                logger.warning(f"Failed to load knowledge base: {e}")
                self.articles = []
    
    def _build_index(self):
        """构建关键词索引"""
        self.keywords_index = {}
        
        for i, article in enumerate(self.articles):
            keywords = self._extract_keywords(article.get("content", ""))
            for kw in keywords:
                if kw not in self.keywords_index:
                    self.keywords_index[kw] = []
                self.keywords_index[kw].append(i)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re
        text = text.lower()
        words = re.findall(r'\b\w{4,}\b', text)
        
        stopwords = {"this", "that", "with", "from", "have", "been", "will", 
                    "their", "what", "about", "which", "when", "make", "like",
                    "time", "just", "know", "take", "people", "year", "good", "some"}
        
        keywords = [w for w in words if w not in stopwords]
        return list(set(keywords))[:20]
    
    def add_article(self, title: str, content: str, metadata: dict = None):
        """添加文章到知识库"""
        article = {
            "title": title,
            "content": content,
            "date": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.articles.append(article)
        
        if len(self.articles) > 100:
            self.articles = self.articles[-100:]
        
        self._build_index()
        self._save_knowledge()
        
        logger.info(f"Added article to knowledge base: {title[:30]}")
    
    def _save_knowledge(self):
        """保存知识库"""
        CACHE_DIR.mkdir(exist_ok=True)
        KNOWLEDGE_FILE.write_text(
            json.dumps(self.articles, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def find_related(self, query: str, top_k: int = 3) -> List[Dict]:
        """查找相关文章"""
        query_keywords = self._extract_keywords(query)
        
        if not query_keywords:
            return []
        
        scores = {}
        
        for kw in query_keywords:
            if kw in self.keywords_index:
                for idx in self.keywords_index[kw]:
                    scores[idx] = scores.get(idx, 0) + 1
        
        if not scores:
            return []
        
        sorted_indices = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in sorted_indices[:top_k]:
            article = self.articles[idx]
            results.append({
                "title": article["title"],
                "content": article["content"][:500],
                "date": article["date"],
                "relevance": score
            })
        
        return results
    
    def get_context(self, current_news: str, max_chars: int = 2000) -> str:
        """获取相关上下文用于增强生成"""
        related = self.find_related(current_news, top_k=3)
        
        if not related:
            return ""
        
        context_parts = ["## 相关历史背景\n"]
        
        for i, article in enumerate(related, 1):
            context_parts.append(f"\n### {i}. {article['title']}")
            context_parts.append(f"({article['date'][:10]}, 相关度: {article['relevance']})")
            context_parts.append(f"\n{article['content'][:300]}...")
        
        context = "\n".join(context_parts)
        
        if len(context) > max_chars:
            context = context[:max_chars] + "..."
        
        return context


class RAGEnhancer:
    """RAG 增强器"""
    
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置"""
        from src.config import load_config
        config = load_config()
        return config.get("rag", {})
    
    def enhance_prompt(self, news_content: str, base_prompt: str) -> str:
        """增强 Prompt"""
        if not self.config.get("enabled", False):
            return base_prompt
        
        try:
            context = self.knowledge_base.get_context(news_content)
            
            if context:
                enhanced = base_prompt + f"\n\n{context}"
                logger.info("RAG context added to prompt")
                return enhanced
            
        except Exception as e:
            logger.warning(f"RAG enhancement failed: {e}")
        
        return base_prompt
    
    def save_to_knowledge(self, title: str, content: str, metadata: dict = None):
        """保存到知识库"""
        if self.config.get("enabled", False):
            self.knowledge_base.add_article(title, content, metadata)
    
    def search_history(self, keyword: str) -> List[Dict]:
        """搜索历史文章"""
        return self.knowledge_base.find_related(keyword)


class PromptTemplates:
    """Prompt 模板库"""
    
    @staticmethod
    def get_summary_prompt(news_items: str, context: str = "") -> str:
        template = f"""你是一位专业的科技编辑，擅长撰写 AI 领域的资讯日报。

要求：
1. 标题要有吸引力，使用 emoji
2. 按主题分类组织内容
3. 每条资讯要有专业摘要
4. 结尾要有行业点评

今日 AI 资讯素材：
{news_items}
"""
        if context:
            template += f"\n{context}\n"
        
        template += "\n请直接输出公众号文章内容（Markdown 格式）。"
        
        return template
    
    @staticmethod
    def get_analysis_prompt(news_items: str, historical_context: str = "") -> str:
        template = f"""你是一位 AI 行业分析师。请分析以下新闻：

{news_items}
"""
        if historical_context:
            template += f"\n参考历史背景：\n{historical_context}\n"
        
        template += """
请提供：
1. 技术趋势分析
2. 市场竞争格局
3. 投资建议
4. 未来预测

分析格式："""
        
        return template


def quick_test():
    """快速测试"""
    print("Testing RAG Enhancement...")
    
    kb = KnowledgeBase()
    
    kb.add_article(
        "GPT-5 发布",
        "OpenAI 发布了 GPT-5 模型，在推理能力和多模态理解方面有重大突破。",
        {"source": "test"}
    )
    
    kb.add_article(
        "Claude 4 发布",
        "Anthropic 发布了 Claude 4，强调安全性和可控性。",
        {"source": "test"}
    )
    
    results = kb.find_related("OpenAI GPT model")
    print(f"\nSearch results for 'OpenAI GPT model':")
    for r in results:
        print(f"  - {r['title']} (relevance: {r['relevance']})")
    
    enhancer = RAGEnhancer()
    print("\nRAG Enhancer initialized")


if __name__ == "__main__":
    quick_test()
