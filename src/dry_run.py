"""
Dry Run - 本地预览（不碰微信）

用于发布前审阅：跑完整的内容流水线（抓新闻 → LLM 结构化产出 → 固定排版渲染
→ 封面出图），但**不创建草稿**，只把结果落到 output/preview_*.html。

AGENTS.md 的作业方式：先在本地出预览，人工确认后再决定要不要建草稿。
（同时也避免同一天反复建/删线上草稿。）
"""

import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

_PREVIEW_SHELL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ margin: 0; padding: 24px 0; background: #EDEAE3; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def run_local_preview() -> bool:
    """生成一份本地预览（HTML + 封面），返回是否成功。不产生任何微信侧写操作。"""
    from src.fetcher import fetch_news
    from src.summarizer import Summarizer
    from src import editorial_template
    from src.ai_photo_cover import generate_ai_photo_cover
    from src.cover_generator import generate_gradient_cover

    start = time.time()
    try:
        logger.info("[1/4] 抓取新闻…")
        news_items = fetch_news()
        if not news_items:
            logger.error("没抓到任何新闻，终止")
            return False
        logger.info(f"      抓到 {len(news_items)} 条")

        logger.info("[2/4] LLM 结构化产出…")
        spec = Summarizer().generate_editorial_spec(news_items, allow_mock=False)
        title = editorial_template.draft_title(spec)
        logger.info(f"      标题: {title}")

        logger.info("[3/4] 渲染排版…")
        article_html = editorial_template.render(spec)
        today = datetime.now().strftime("%Y%m%d")
        preview_html = f"output/preview_{today}.html"
        with open(preview_html, "w", encoding="utf-8") as f:
            f.write(_PREVIEW_SHELL.format(title=title, body=article_html))
        logger.info(f"      预览: {preview_html}")

        logger.info("[4/4] 生成封面（写实优先，失败降级渐变，均无文字）…")
        cover_path = f"output/preview_cv_{today}.jpg"
        cover, theme = generate_ai_photo_cover(title, cover_path)
        if not cover:
            cover = generate_gradient_cover(title, cover_path, with_text=False)
        logger.info(f"      封面: {cover or '失败'}（主题 {theme or '-'}）")

        logger.info(f"✅ 预览完成，耗时 {time.time() - start:.1f}s（未创建草稿）")
        return True
    except Exception as e:
        logger.error(f"预览失败: {e}", exc_info=True)
        return False
