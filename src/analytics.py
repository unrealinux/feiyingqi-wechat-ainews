"""
Analytics Module - 数据分析模块

提供文章统计、趋势分析等功能
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output")
STATS_FILE = Path("cache/stats.json")


class Analytics:
    """数据分析器"""
    
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.stats_file = STATS_FILE
        self.stats_file.parent.mkdir(exist_ok=True)
    
    def get_article_stats(self) -> Dict:
        """获取文章统计"""
        articles = self._scan_articles()
        
        stats = {
            "total": len(articles),
            "total_words": sum(a["word_count"] for a in articles),
            "avg_words": sum(a["word_count"] for a in articles) // max(len(articles), 1),
            "by_month": self._group_by_month(articles),
            "recent_trend": self._calculate_trend(articles),
        }
        
        self._save_stats(stats)
        return stats
    
    def _scan_articles(self) -> List[Dict]:
        """扫描所有文章"""
        articles = []
        
        for md_file in sorted(self.output_dir.glob("article_*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                stat = md_file.stat()
                
                articles.append({
                    "file": md_file.name,
                    "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
                    "word_count": len(content),
                    "char_count": len(content),
                })
            except Exception as e:
                logger.debug(f"Error reading {md_file}: {e}")
        
        return articles
    
    def _group_by_month(self, articles: List[Dict]) -> Dict[str, int]:
        """按月分组统计"""
        by_month = Counter()
        
        for article in articles:
            try:
                month = article["date"][:7]  # YYYY-MM
                by_month[month] += 1
            except:
                pass
        
        return dict(sorted(by_month.items())[-6:])  # 最近 6 个月
    
    def _calculate_trend(self, articles: List[Dict]) -> str:
        """计算趋势"""
        if len(articles) < 2:
            return "stable"
        
        recent = articles[:7]
        older = articles[7:14]
        
        if len(recent) > len(older):
            return "up ⬆️"
        elif len(recent) < len(older):
            return "down ⬇️"
        return "stable ➡️"
    
    def _save_stats(self, stats: Dict):
        """保存统计"""
        stats["updated_at"] = datetime.now().isoformat()
        
        with self.stats_file.open("w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def load_stats(self) -> Optional[Dict]:
        """加载统计"""
        if self.stats_file.exists():
            return json.loads(self.stats_file.read_text(encoding="utf-8"))
        return None
    
    def get_news_source_stats(self, news_items: List) -> Dict:
        """获取新闻源统计"""
        sources = Counter(item.source for item in news_items if hasattr(item, "source"))
        
        return {
            "top_sources": sources.most_common(10),
            "total_sources": len(sources),
        }
    
    def generate_report(self) -> str:
        """生成分析报告"""
        stats = self.get_article_stats()
        
        report = f"""
## 📊 AI News Publisher 统计报告

**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

### 总体统计

| 指标 | 数值 |
|------|------|
| 总文章数 | {stats['total']} 篇 |
| 总字数 | {stats['total_words']:,} 字 |
| 平均字数 | {stats['avg_words']:,} 字/篇 |
| 趋势 | {stats['recent_trend']} |

### 月度分布

"""
        for month, count in stats.get("by_month", {}).items():
            report += f"- **{month}**: {count} 篇\n"
        
        return report


def show_analytics():
    """显示分析结果"""
    analytics = Analytics()
    
    print("\n" + "="*50)
    print("📊 AI News Publisher - 数据分析")
    print("="*50)
    
    stats = analytics.get_article_stats()
    
    print(f"\n📄 总文章数：{stats['total']}")
    print(f"📝 总字数：{stats['total_words']:,}")
    print(f"📏 平均字数：{stats['avg_words']:,}")
    print(f"📈 趋势：{stats['recent_trend']}")
    
    print("\n📅 月度分布:")
    for month, count in stats.get("by_month", {}).items():
        bar = "█" * count
        print(f"  {month}: {bar} {count}")
    
    print("\n" + "="*50)


if __name__ == "__main__":
    show_analytics()
