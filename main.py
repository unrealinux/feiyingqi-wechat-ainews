#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="AI News Publisher v3.0 - 全网 AI 资讯聚合自动发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py run           手动运行一次
  python main.py schedule      启动定时任务
  python main.py test          测试模式
  python main.py dashboard     启动增强版 Web 界面
  python main.py api           启动 REST API
  python main.py analytics     查看数据统计
  python main.py config       配置状态检查
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("run", help="手动运行一次")
    subparsers.add_parser("schedule", help="启动定时任务")
    subparsers.add_parser("test", help="测试模式")
    subparsers.add_parser("dashboard", help="启动增强版 Web 界面")
    subparsers.add_parser("dashboard-simple", help="启动简洁版 Web 界面")
    subparsers.add_parser("api", help="启动 REST API")
    subparsers.add_parser("analytics", help="查看数据统计")
    subparsers.add_parser("config", help="配置状态检查")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "config":
        show_config()
        return
    
    if args.command == "test":
        run_test_mode()
        return
    
    if args.command == "run":
        run_once()
        return
    
    if args.command == "schedule":
        run_scheduler()
        return
    
    if args.command == "dashboard":
        run_enhanced_dashboard()
        return
    
    if args.command == "dashboard-simple":
        run_simple_dashboard()
        return
    
    if args.command == "api":
        run_api_server()
        return
    
    if args.command == "analytics":
        show_analytics()
        return


def show_config():
    try:
        from src.config_secure import print_config_status
        print_config_status()
    except ImportError:
        from src.config import load_config
        config = load_config()
        
        print("\n=== Configuration ===")
        wechat = config.get("wechat", {})
        openai = config.get("openai", {})
        
        print(f"WeChat: {'✅ Configured' if wechat.get('app_id') else '❌ Not set'}")
        print(f"OpenAI: {'✅ Configured' if openai.get('api_key') else '❌ Not set'}")
        print()


def run_test_mode():
    from src.fetcher import fetch_news
    from src.summarizer import generate_article
    
    print("🧪 Test Mode - Fetching and generating article")
    print("="*50)
    
    print("\n[1/2] Fetching latest AI news...")
    news_items = fetch_news()
    print(f"Fetched {len(news_items)} news items")
    
    if not news_items:
        print("No news fetched.")
        return
    
    print("\n[2/2] Generating article with AI...")
    article_content = generate_article(news_items)
    print(f"Article generated ({len(article_content)} characters)")
    print("\n" + "="*50)
    print("Article Preview:")
    print("="*50)
    print(article_content[:2000])


def run_once():
    from src.scheduler import run_once as scheduler_run_once
    scheduler_run_once()


def run_scheduler():
    from src.scheduler import start_scheduler
    from src.scheduler import run_once
    
    print("📅 Starting scheduler mode...")
    start_scheduler(run_once)


def run_enhanced_dashboard():
    from src.dashboard_enhanced import start_dashboard
    print("🎨 Starting Enhanced Dashboard...")
    print("   Dashboard: http://localhost:5000")
    print("   API:       http://localhost:5000/api")
    print("="*50)
    start_dashboard(port=5000)


def run_simple_dashboard():
    from src.dashboard import start_dashboard
    print("📊 Starting Simple Dashboard...")
    print("   URL: http://localhost:5000")
    print("="*50)
    start_dashboard(port=5000)


def run_api_server():
    from src.api import start_api_server
    print("🔌 Starting REST API Server...")
    print("   API: http://localhost:5001")
    print("   Docs: http://localhost:5001/")
    print("="*50)
    start_api_server(port=5001)


def show_analytics():
    from src.analytics import show_analytics
    show_analytics()


if __name__ == "__main__":
    main()
