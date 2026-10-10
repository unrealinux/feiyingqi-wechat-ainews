"""
Unified Publisher - 统一发布入口

整合所有发布功能：
- 基础发布（无封面）
- 带封面图发布
- 带AI封面发布
- 带代理发布
- 完整发布流程
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.ai_score import check_ai_score, DEFAULT_THRESHOLD
from src.config import load_config, get_wechat_config

logger = logging.getLogger(__name__)


class UnifiedPublisher:
    """统一发布器 - 整合所有发布功能"""

    def __init__(self):
        self.config = load_config()
        self.wechat_config = get_wechat_config(self.config)
        self.app_id = self.wechat_config.get("app_id", "")
        self.app_secret = self.wechat_config.get("app_secret", "")

    def publish(
        self,
        title: str,
        content: str,
        mode: str = "auto",
        cover_image: Optional[str] = None,
        use_ai_cover: bool = False,
        use_proxy: bool = False,
        auto_publish: bool = False,
        ai_threshold: float = DEFAULT_THRESHOLD,
    ) -> dict:
        """
        统一发布接口

        Args:
            title: 文章标题
            content: 文章内容（Markdown格式）
            mode: 发布模式
                - simple: 简单发布（无封面）
                - with_cover: 带封面发布
                - ai_cover: 带AI生成封面
                - complete: 完整流程
                - auto: 自动选择最佳方式
            cover_image: 封面图路径（可选）
            use_ai_cover: 是否使用AI生成封面
            use_proxy: 是否使用代理
            auto_publish: 是否自动发布（vs保存为草稿）
            ai_threshold: AI 味分数上限，超过即拒绝发布（AGENTS.md：低质模板化
                内容会触发平台降权）。检测逻辑来自 Easel 的 src/ai_score.py

        Returns:
            dict: 发布结果
        """
        # AGENTS.md 红线：低质/AI 味内容 = 平台降权。发布前过一遍启发式门禁。
        passed, report = check_ai_score(content, threshold=ai_threshold)
        if not passed:
            logger.warning(
                f"AI 味门禁拒绝发布：{report['total_score']}/{ai_threshold} "
                f"套话={report['hit_phrases']} 高频词={report['hit_vocab']}"
            )
            return {
                "success": False,
                "mode": mode,
                "title": title,
                "timestamp": datetime.now().isoformat(),
                "files": [],
                "ai_score": report,
                "error": (
                    f"AI 味过重（{report['total_score']} >= {ai_threshold}），已拒绝发布。"
                    "请按 docs/anti-ai-checklist.md 改写后重试。"
                ),
            }
        logger.info(f"AI 味门禁通过：{report['total_score']}/{ai_threshold}")

        result = {
            "success": False,
            "mode": mode,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "files": [],
            "error": None,
        }

        try:
            # 1. 保存文章到本地
            md_path, html_path = self._save_article(title, content)
            result["files"].extend([str(md_path), str(html_path)])

            # 2. 处理封面图
            final_cover = cover_image
            if use_ai_cover or mode == "ai_cover":
                final_cover = self._generate_ai_cover(title)
                if final_cover:
                    result["files"].append(final_cover)
            elif not final_cover and mode in ["with_cover", "complete", "auto"]:
                final_cover = self._get_default_cover()

            # 3. 发布到微信
            if self.app_id and self.app_secret:
                publish_result = self._publish_to_wechat(
                    title=title,
                    content=content,
                    cover_path=final_cover,
                    auto_publish=auto_publish,
                )
                result.update(publish_result)
            else:
                result["success"] = True
                result["message"] = "文章已保存到本地（微信未配置）"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"发布失败: {e}", exc_info=True)

        return result

    def _save_article(self, title: str, content: str):
        """保存文章到本地"""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        today = datetime.now().strftime("%Y%m%d")
        md_path = output_dir / f"article_{today}.md"
        html_path = output_dir / f"article_{today}.html"

        # 保存Markdown
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{content}")

        # 生成HTML
        html_content = self._markdown_to_html(title, content)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"文章已保存: {md_path}")
        return md_path, html_path

    def _markdown_to_html(self, title: str, content: str) -> str:
        """转换Markdown为HTML"""
        # 简单的Markdown转HTML
        html_body = content
        # 基本转换
        html_body = html_body.replace("\n\n", "</p><p>")
        html_body = html_body.replace("\n", "<br>")
        # 处理标题
        for i in range(6, 0, -1):
            prefix = "#" * i
            html_body = html_body.replace(f"{prefix} ", f"<h{i}>").replace(
                "\n", f"</h{i}>\n", 1
            )

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        h2 {{ color: #444; margin-top: 30px; }}
        p {{ margin: 15px 0; }}
        a {{ color: #0366d6; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>{html_body}</p>
    <div class="footer">
        <p>由 AI News Publisher 自动生成</p>
    </div>
</body>
</html>"""

    def _generate_ai_cover(self, title: str) -> Optional[str]:
        """生成AI封面图"""
        try:
            from src.ai_cover_generator import generate_ai_cover

            output_path = f"output/cover_{datetime.now().strftime('%Y%m%d')}.png"
            return generate_ai_cover(title, output_path)
        except Exception as e:
            logger.warning(f"AI封面生成失败: {e}")
            return None

    def _get_default_cover(self) -> Optional[str]:
        """获取默认封面图"""
        # 查找现有封面图
        cover_files = ["cover.png", "output/cover.png", "assets/cover.png"]
        for path in cover_files:
            if os.path.exists(path):
                return path
        return None

    def _publish_to_wechat(
        self, title: str, content: str, cover_path: Optional[str], auto_publish: bool
    ) -> dict:
        """发布到微信公众号"""
        try:
            from src.publisher import publish_article

            success = publish_article(
                title=title,
                content=content,
                cover_path=cover_path,
                auto_publish=auto_publish,
            )
            return {
                "success": success,
                "channel": "wechat",
                "message": "已发布到微信草稿箱" if success else "微信发布失败",
            }
        except Exception as e:
            return {"success": False, "channel": "wechat", "error": str(e)}


# 便捷函数
def publish_article_unified(
    title: str,
    content: str,
    mode: str = "auto",
    cover_image: Optional[str] = None,
    use_ai_cover: bool = False,
    **kwargs,
) -> dict:
    """
    统一发布文章

    Args:
        title: 文章标题
        content: 文章内容
        mode: 发布模式
        cover_image: 封面图路径
        use_ai_cover: 是否使用AI封面
        **kwargs: 其他参数

    Returns:
        发布结果
    """
    publisher = UnifiedPublisher()
    return publisher.publish(
        title=title,
        content=content,
        mode=mode,
        cover_image=cover_image,
        use_ai_cover=use_ai_cover,
        **kwargs,
    )


if __name__ == "__main__":
    # 测试
    result = publish_article_unified(
        title="测试文章", content="这是一篇测试文章的内容。", mode="simple"
    )
    print(f"发布结果: {result}")
