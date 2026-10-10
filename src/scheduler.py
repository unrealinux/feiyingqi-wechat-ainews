"""
AI News Scheduler - 调度器模块

支持定时任务、手动运行、进度显示
"""

import time
import signal
import sys
import logging
from datetime import datetime, timedelta
from typing import Callable

from src.config import load_config, get_scheduler_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _refetch_more(current: list, limit: int = 30) -> list:
    """再抓一轮素材并与原素材合并（只增不减，按 URL/标题去重）。

    用于"素材太薄"：模型写不出人味往往是因为素材里没数字可写，多给一份素材
    比把同一份重写第三次有用。补抓失败就维持原样，不因此中断流水线。
    """
    from src.fetcher import fetch_news

    try:
        fresh = fetch_news()
    except Exception as e:
        logger.warning(f"补抓素材失败，沿用原有素材: {e}")
        return current

    seen = {item.url or item.title for item in current}
    merged = list(current)
    for item in fresh:
        key = item.url or item.title
        if key and key not in seen:
            seen.add(key)
            merged.append(item)
    return merged[:limit]


def _notify_failure(reason: str) -> None:
    """失败要有声音。定时任务跑在后台，日志没人看；

    AI 味门禁/LLM 失败都会让当天"没稿"，不说一声就和网络挂掉分不出来。
    复用已有的监控通道（未配置 webhook 时是 no-op），且通知本身出错不得影响主流程。
    """
    try:
        from src.monitoring import record_alert, send_run_notification

        send_run_notification("error", {"error": reason})
        record_alert(reason)
    except Exception as e:
        logger.warning(f"失败通知发送失败（不影响主流程）: {e}")


class Scheduler:
    """定时任务调度器"""

    def __init__(self, task_func: Callable):
        self.task_func = task_func
        self.running = False
        config = load_config()
        scheduler_config = get_scheduler_config(config)

        self.target_time = scheduler_config.get("time", "08:00")
        self.timezone = scheduler_config.get("timezone", "Asia/Shanghai")
        self.interval_days = int(scheduler_config.get("interval_days", 1))
        self.enabled = scheduler_config.get("enabled", False)

        # 真正按配置时区计算（此前 timezone 只打日志、不生效）
        try:
            from zoneinfo import ZoneInfo

            self.tz = ZoneInfo(self.timezone)
        except Exception as e:
            logger.warning(f"时区 {self.timezone!r} 不可用（{e}），回退本机时区")
            self.tz = None

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _now(self) -> datetime:
        """当前时间（配置时区；不可用时回退本机时区）。"""
        if self.tz is not None:
            return datetime.now(self.tz)
        return datetime.now()

    def _signal_handler(self, signum, frame):
        logger.info("\nReceived shutdown signal. Stopping...")
        self.running = False
        sys.exit(0)

    def run(self):
        if not self.enabled:
            logger.info("Scheduler is disabled in config.yaml")
            logger.info("Set scheduler.enabled: true to enable daily scheduling")
            return

        logger.info("=" * 50)
        tz_note = str(self.tz) if self.tz is not None else "本机时区"
        logger.info(
            f"Scheduler started - Every {self.interval_days} day(s) at {self.target_time} ({tz_note})"
        )
        logger.info("=" * 50)

        self.running = True

        while self.running:
            now = self._now()
            target_hour, target_minute = map(int, self.target_time.split(":"))

            target = now.replace(
                hour=target_hour, minute=target_minute, second=0, microsecond=0
            )

            if now >= target:
                target = target + timedelta(days=self.interval_days)

            wait_seconds = (target - now).total_seconds()
            next_run = target.strftime("%Y-%m-%d %H:%M:%S")

            logger.info(f"Next run: {next_run} (in {int(wait_seconds / 60)} minutes)")
            logger.info("Press Ctrl+C to stop")

            time.sleep(wait_seconds)

            if self.running:
                self._run_task()

    def _run_task(self):
        logger.info("\n" + "=" * 50)
        logger.info(f"Running task at {self._now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 50)

        try:
            self.task_func()
            logger.info("Task completed successfully!")
        except Exception as e:
            logger.error(f"Task failed: {e}", exc_info=True)

        logger.info("=" * 50 + "\n")


def start_scheduler(task_func: Callable):
    """启动调度器"""
    scheduler = Scheduler(task_func)
    scheduler.run()


def run_once() -> bool:
    """运行一次完整流程：抓新闻 → LLM 产出结构化内容 → 固定排版渲染 → 写草稿。"""
    from src.fetcher import fetch_news, get_mock_news
    from src.summarizer import Summarizer, ThinMaterialError
    from src.publisher import publish_article
    from src import editorial_template

    start_time = time.time()

    logger.info("\n" + "=" * 50)
    logger.info("AI News Publisher - Starting")
    logger.info("=" * 50)

    try:
        logger.info("\n[1/4] Fetching latest AI news...")
        news_items = fetch_news()

        if not news_items:
            logger.warning("No news fetched, using mock data")
            news_items = get_mock_news(5)

        logger.info(f"Fetched {len(news_items)} news items")

        logger.info("\n[2/4] Generating structured content with AI...")
        # allow_mock=False：LLM 欠费/掉线时宁可本次失败，也不生成 mock 拼贴稿
        summarizer = Summarizer()
        for material_attempt in (1, 2):
            try:
                spec = summarizer.generate_editorial_spec(news_items, allow_mock=False)
                break
            except ThinMaterialError as e:
                if material_attempt == 2:
                    raise
                logger.warning(f"素材太薄（{e}），补抓一批素材后重试")
                news_items = _refetch_more(news_items)
        title = editorial_template.draft_title(spec)
        logger.info(f"Title: {title}")

        logger.info("\n[3/4] Rendering fixed editorial layout...")
        article_html = editorial_template.render(spec)
        logger.info(f"Article rendered ({len(article_html)} characters)")

        # 生成封面：优先写实风（Agnes 出图），失败则降级到本地渐变封面
        from src.cover_generator import generate_gradient_cover
        import datetime as _dt

        cover_path = f"output/cv_auto_{_dt.datetime.now().strftime('%Y%m%d')}.jpg"
        cover_result = None
        try:
            from src.ai_photo_cover import generate_ai_photo_cover

            cover_result, _theme = generate_ai_photo_cover(title, cover_path)
        except Exception as e:
            logger.warning(f"写实封面生成异常，改用渐变封面: {e}")
        if not cover_result:
            logger.info("改用本地渐变封面（无文字版）")
            cover_result = generate_gradient_cover(title, cover_path, with_text=False)
        if not cover_result:
            logger.warning("渐变封面生成失败，将使用默认封面")
            cover_path = ""

        logger.info("\n[4/4] Publishing to WeChat...")
        success = publish_article(
            title=title,
            content=article_html,
            cover_path=cover_path,
            auto_publish=False,
            export_html=True,
            content_is_html=True,
        )

        elapsed = time.time() - start_time

        logger.info("\n" + "=" * 50)
        if success:
            logger.info("✅ All done! Article saved to:")
            logger.info(f"   - output/article_{datetime.now().strftime('%Y%m%d')}.html")
            logger.info("\nLogin to mp.weixin.qq.com to publish")
        else:
            logger.error("Failed to publish article")
            # 不猜原因：实测最常见的就是 IP 白名单（invalid ip），其次是门禁/网络
            _notify_failure(
                "发布步骤返回失败（详细原因见上文日志；常见：出口 IP 不在白名单 / "
                "AI 味门禁拦截 / 网络或凭证问题）"
            )
        logger.info(f"Total time: {elapsed:.1f}s")
        logger.info("=" * 50)

        return success

    except Exception as e:
        logger.error(f"Error in run_once: {e}", exc_info=True)
        logger.error("本次不创建草稿。修复后重跑：python main.py daily")
        _notify_failure(str(e))
        return False


if __name__ == "__main__":
    print("Running once...")
    run_once()
