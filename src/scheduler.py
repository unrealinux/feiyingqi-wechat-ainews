"""
AI News Scheduler - 调度器模块

支持定时任务、手动运行、进度显示
"""

import time
import signal
import sys
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional
from pathlib import Path

from src.config import load_config, get_scheduler_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self, task_func: Callable):
        self.task_func = task_func
        self.running = False
        config = load_config()
        scheduler_config = get_scheduler_config(config)
        
        self.target_time = scheduler_config.get("time", "08:00")
        self.timezone = scheduler_config.get("timezone", "Asia/Shanghai")
        self.enabled = scheduler_config.get("enabled", False)
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info("\nReceived shutdown signal. Stopping...")
        self.running = False
        sys.exit(0)
    
    def run(self):
        if not self.enabled:
            logger.info("Scheduler is disabled in config.yaml")
            logger.info("Set scheduler.enabled: true to enable daily scheduling")
            return
        
        logger.info("="*50)
        logger.info(f"Scheduler started - Daily at {self.target_time} ({self.timezone})")
        logger.info("="*50)
        
        self.running = True
        
        while self.running:
            now = datetime.now()
            target_hour, target_minute = map(int, self.target_time.split(":"))
            
            target = now.replace(
                hour=target_hour,
                minute=target_minute,
                second=0,
                microsecond=0
            )
            
            if now >= target:
                target = target + timedelta(days=1)
            
            wait_seconds = (target - now).total_seconds()
            next_run = target.strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"Next run: {next_run} (in {int(wait_seconds/60)} minutes)")
            logger.info("Press Ctrl+C to stop")
            
            time.sleep(wait_seconds)
            
            if self.running:
                self._run_task()
    
    def _run_task(self):
        logger.info("\n" + "="*50)
        logger.info(f"Running task at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*50)
        
        try:
            self.task_func()
            logger.info("Task completed successfully!")
        except Exception as e:
            logger.error(f"Task failed: {e}", exc_info=True)
        
        logger.info("="*50 + "\n")


def start_scheduler(task_func: Callable):
    """启动调度器"""
    scheduler = Scheduler(task_func)
    scheduler.run()


def run_once() -> bool:
    """运行一次完整流程"""
    from src.fetcher import fetch_news, get_mock_news
    from src.summarizer import generate_article
    from src.publisher import publish_article
    
    start_time = time.time()
    
    logger.info("\n" + "="*50)
    logger.info("AI News Publisher - Starting")
    logger.info("="*50)
    
    try:
        logger.info("\n[1/3] Fetching latest AI news...")
        news_items = fetch_news()
        
        if not news_items:
            logger.warning("No news fetched, using mock data")
            news_items = get_mock_news(5)
        
        logger.info(f"Fetched {len(news_items)} news items")
        
        logger.info("\n[2/3] Generating article with AI...")
        article_content = generate_article(news_items)
        logger.info(f"Article generated ({len(article_content)} characters)")
        
        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"🎯 {today} AI 资讯日报"
        
        logger.info("\n[3/3] Publishing to WeChat...")
        success = publish_article(
            title=title,
            content=article_content,
            auto_publish=False,
            export_html=True
        )
        
        elapsed = time.time() - start_time
        
        logger.info("\n" + "="*50)
        if success:
            logger.info("✅ All done! Article saved to:")
            logger.info(f"   - output/article_{datetime.now().strftime('%Y%m%d')}.md")
            logger.info(f"   - output/article_{datetime.now().strftime('%Y%m%d')}.html")
            logger.info("\nLogin to mp.weixin.qq.com to publish")
        else:
            logger.error("Failed to publish article")
        logger.info(f"Total time: {elapsed:.1f}s")
        logger.info("="*50)
        
        return success
        
    except Exception as e:
        logger.error(f"Error in run_once: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("Running once...")
    run_once()
