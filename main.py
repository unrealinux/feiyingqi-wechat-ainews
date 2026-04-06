#!/usr/bin/env python3
"""
AI News Publisher v3.0 - 全网 AI 资讯聚合自动发布工具

统一入口：整合所有功能到一个命令行界面
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="AI News Publisher v3.0 - 全网 AI 资讯聚合自动发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 文章生成与发布
  python main.py run                  手动运行一次（默认模式）
  python main.py run --cover          带封面图运行
  python main.py run --ai-cover       带AI生成封面运行
  python main.py run --publish        自动发布到微信
  python main.py run --no-llm         跳过LLM生成（仅获取新闻）

  # 单独功能
  python main.py fetch                仅获取新闻
  python main.py generate             仅生成文章
  python main.py publish              发布最新文章
  python main.py cover                生成封面图

  # 自定义文章
  python main.py custom-article                      生成AI会议工具横评文章
  python main.py custom-article --publish            生成并发布到微信草稿箱
  python main.py custom-article --type meeting_tools_review  指定文章类型
  python main.py custom-article --ai-cover           使用AI生成封面图

  # 服务与管理
  python main.py schedule             启动定时任务
  python main.py dashboard            启动增强版 Web 界面
  python main.py dashboard-simple     启动简洁版 Web 界面
  python main.py api                  启动 REST API
  python main.py analytics            查看数据统计
  python main.py config               配置状态检查
  python main.py test                 测试模式
  python main.py health               健康检查

开发与测试:
  python main.py test                 运行测试模式
  python main.py validate             验证配置
  python main.py mock                 使用模拟数据运行
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 主要命令
    run_parser = subparsers.add_parser("run", help="手动运行一次")
    run_parser.add_argument("--cover", action="store_true", help="生成封面图")
    run_parser.add_argument("--ai-cover", action="store_true", help="使用AI生成封面图")
    run_parser.add_argument("--publish", action="store_true", help="自动发布到微信")
    run_parser.add_argument("--no-llm", action="store_true", help="跳过LLM生成")
    run_parser.add_argument("--mock", action="store_true", help="使用模拟数据")
    
    subparsers.add_parser("fetch", help="仅获取新闻")
    subparsers.add_parser("generate", help="仅生成文章")
    publish_parser = subparsers.add_parser("publish", help="发布最新文章")
    publish_parser.add_argument("--mode", choices=["simple", "cover", "ai-cover", "complete"],
                                default="complete", help="发布模式")
    cover_parser = subparsers.add_parser("cover", help="生成封面图")
    cover_parser.add_argument("--title", help="文章标题")
    cover_parser.add_argument("--ai", action="store_true", help="使用AI生成")
    
    # 服务命令
    subparsers.add_parser("schedule", help="启动定时任务")
    subparsers.add_parser("dashboard", help="启动增强版 Web 界面")
    subparsers.add_parser("dashboard-simple", help="启动简洁版 Web 界面")
    subparsers.add_parser("api", help="启动 REST API")
    subparsers.add_parser("analytics", help="查看数据统计")
    subparsers.add_parser("config", help="配置状态检查")
    subparsers.add_parser("test", help="测试模式")
    subparsers.add_parser("health", help="健康检查")
    subparsers.add_parser("validate", help="验证配置")
    subparsers.add_parser("mock", help="使用模拟数据运行")
    
    # 自定义文章命令
    custom_parser = subparsers.add_parser("custom-article", help="生成自定义文章")
    custom_parser.add_argument("--type", choices=["meeting_tools_review"], 
                              default="meeting_tools_review", help="文章类型")
    custom_parser.add_argument("--publish", action="store_true", help="自动发布到微信草稿箱")
    custom_parser.add_argument("--cover", action="store_true", help="生成封面图")
    custom_parser.add_argument("--ai-cover", action="store_true", help="使用AI生成封面图")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 命令路由
    if args.command == "config":
        show_config()
    elif args.command == "run":
        run_once(args)
    elif args.command == "fetch":
        fetch_only()
    elif args.command == "generate":
        generate_only()
    elif args.command == "publish":
        publish_article(args.mode)
    elif args.command == "cover":
        generate_cover(args.title, args.ai)
    elif args.command == "schedule":
        run_scheduler()
    elif args.command == "dashboard":
        run_enhanced_dashboard()
    elif args.command == "dashboard-simple":
        run_simple_dashboard()
    elif args.command == "api":
        run_api_server()
    elif args.command == "analytics":
        show_analytics()
    elif args.command == "test":
        run_test_mode()
    elif args.command == "health":
        run_health_check()
    elif args.command == "validate":
        run_config_validation()
    elif args.command == "mock":
        run_mock_mode()
    elif args.command == "custom-article":
        run_custom_article(args)


def show_config():
    """显示配置状态"""
    try:
        from src.config import load_config
        
        config = load_config()
        
        print("\n" + "="*50)
        print("📊 AI News Publisher 配置状态")
        print("="*50)
        
        # 微信配置
        wechat = config.get("wechat", {})
        print(f"\n📱 微信公众号:")
        print(f"   AppID: {'✅ 已配置' if wechat.get('app_id') and wechat['app_id'] != 'your_app_id_here' else '❌ 未配置'}")
        print(f"   AppSecret: {'✅ 已配置' if wechat.get('app_secret') and wechat['app_secret'] != 'your_app_secret_here' else '❌ 未配置'}")
        
        # LLM配置
        llm = config.get("llm", {})
        provider = llm.get("provider", "auto")
        print(f"\n🤖 LLM 配置:")
        print(f"   提供商: {provider}")
        
        # OpenAI
        openai = config.get("openai", {})
        print(f"   OpenAI: {'✅ 已配置' if openai.get('api_key') and openai['api_key'] != 'your_openai_api_key_here' else '❌ 未配置'}")
        
        # DeepSeek
        deepseek = config.get("deepseek", {})
        print(f"   DeepSeek: {'✅ 已配置' if deepseek.get('api_key') else '❌ 未配置'}")
        
        # 智谱AI
        zhipu = config.get("zhipu", {})
        print(f"   智谱AI: {'✅ 已配置' if zhipu.get('api_key') else '❌ 未配置'}")
        
        # 新闻源
        news = config.get("news", {})
        print(f"\n📰 新闻源:")
        sources = news.get("sources", {})
        for source, enabled in sources.items():
            status = "✅" if enabled else "❌"
            print(f"   {source}: {status}")
        
        # 定时任务
        scheduler = config.get("scheduler", {})
        print(f"\n⏰ 定时任务:")
        print(f"   启用: {'✅ 是' if scheduler.get('enabled') else '❌ 否'}")
        print(f"   时间: {scheduler.get('time', '08:00')}")
        
        print("\n" + "="*50)
        
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")


def run_once(args=None):
    """运行一次完整流程"""
    from src.scheduler import run_once as scheduler_run_once
    from src.unified_publisher import publish_article_unified
    from src.fetcher import fetch_news
    from src.summarizer import generate_article
    from src.mock_data import get_mock_news
    
    print("\n" + "="*50)
    print("🚀 AI News Publisher - 开始运行")
    print("="*50)
    
    start_time = datetime.now()
    
    try:
        # 1. 获取新闻
        print("\n📰 [1/3] 获取最新AI新闻...")
        if args and args.mock:
            news_items = get_mock_news(5)
            print(f"   使用模拟数据: {len(news_items)} 条")
        else:
            news_items = fetch_news()
            if not news_items:
                print("   ⚠️ 未获取到新闻，使用模拟数据")
                news_items = get_mock_news(5)
            print(f"   获取到 {len(news_items)} 条新闻")
        
        # 2. 生成文章
        print("\n📝 [2/3] 生成文章...")
        if args and args.no_llm:
            article_content = "\n\n".join([
                f"### {item.title}\n{item.description}\n[原文链接]({item.url})"
                for item in news_items
            ])
            print("   跳过LLM，直接拼接")
        else:
            article_content = generate_article(news_items)
            print(f"   生成完成 ({len(article_content)} 字符)")
        
        # 3. 发布/保存
        print("\n💾 [3/3] 保存文章...")
        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"🎯 {today} AI 资讯日报"
        
        mode = "simple"
        if args:
            if args.ai_cover:
                mode = "ai_cover"
            elif args.cover:
                mode = "with_cover"
        
        result = publish_article_unified(
            title=title,
            content=article_content,
            mode=mode,
            use_ai_cover=args.ai_cover if args else False
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*50)
        if result["success"]:
            print("✅ 运行完成！")
            print(f"   保存的文件:")
            for f in result["files"]:
                print(f"   - {f}")
        else:
            print("❌ 运行失败")
            if result.get("error"):
                print(f"   错误: {result['error']}")
        print(f"   耗时: {elapsed:.1f}秒")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        logger.error(f"run_once 失败: {e}", exc_info=True)


def fetch_only():
    """仅获取新闻"""
    from src.fetcher import fetch_news
    
    print("\n📰 获取最新AI新闻...")
    news_items = fetch_news()
    
    if news_items:
        print(f"\n✅ 获取到 {len(news_items)} 条新闻:")
        for i, item in enumerate(news_items[:10], 1):
            print(f"\n{i}. {item.title}")
            if item.source:
                print(f"   来源: {item.source}")
            if item.url:
                print(f"   链接: {item.url}")
    else:
        print("❌ 未获取到新闻")


def generate_only():
    """仅生成文章"""
    from src.fetcher import fetch_news
    from src.summarizer import generate_article
    from src.mock_data import get_mock_news
    
    print("\n📰 获取新闻...")
    news_items = fetch_news()
    
    if not news_items:
        print("使用模拟数据")
        news_items = get_mock_news(5)
    
    print(f"   获取到 {len(news_items)} 条")
    
    print("\n📝 生成文章...")
    article = generate_article(news_items)
    
    today = datetime.now().strftime("%Y%m%d")
    output_path = f"output/article_{today}.md"
    Path("output").mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(article)
    
    print(f"\n✅ 文章已生成: {output_path}")
    print(f"   字数: {len(article)} 字符")


def publish_article(mode="complete"):
    """发布最新文章"""
    from src.unified_publisher import UnifiedPublisher
    
    print(f"\n📤 发布文章 (模式: {mode})...")
    
    # 查找最新的文章
    output_dir = Path("output")
    articles = list(output_dir.glob("article_*.md"))
    
    if not articles:
        print("❌ 未找到待发布的文章")
        print("   请先运行 python main.py run 生成文章")
        return
    
    latest = max(articles, key=lambda x: x.stat().st_mtime)
    print(f"   发布: {latest.name}")
    
    with open(latest, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取标题
    lines = content.split("\n")
    title = lines[0].replace("#", "").strip() if lines else "AI资讯日报"
    
    publisher = UnifiedPublisher()
    result = publisher.publish(
        title=title,
        content=content,
        mode=mode
    )
    
    if result["success"]:
        print(f"\n✅ 发布成功!")
        if result.get("message"):
            print(f"   {result['message']}")
    else:
        print(f"\n❌ 发布失败: {result.get('error', '未知错误')}")


def generate_cover(title=None, use_ai=False):
    """生成封面图"""
    from src.cover_generator import generate_cover_image
    
    if not title:
        today = datetime.now().strftime("%Y年%m月%d日")
        title = f"{today} AI 资讯日报"
    
    print(f"\n🎨 生成封面图...")
    print(f"   标题: {title}")
    print(f"   AI模式: {'✅ 启用' if use_ai else '❌ 禁用'}")
    
    output_path = f"output/cover_{datetime.now().strftime('%Y%m%d')}.png"
    
    try:
        result = generate_cover_image(
            title=title,
            output_path=output_path,
            style="auto"
        )
        
        if result:
            print(f"\n✅ 封面图已生成: {result}")
        else:
            print("\n❌ 封面图生成失败")
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")


def run_scheduler():
    """启动定时任务"""
    from src.scheduler import start_scheduler, run_once
    
    print("\n📅 启动定时任务模式...")
    print("   按 Ctrl+C 停止")
    start_scheduler(run_once)


def run_enhanced_dashboard():
    """启动增强版 Web 界面"""
    from src.dashboard_enhanced import start_dashboard
    print("\n🎨 启动增强版 Dashboard...")
    print("   Dashboard: http://localhost:5000")
    print("   API: http://localhost:5000/api")
    print("   按 Ctrl+C 停止")
    start_dashboard(port=5000)


def run_simple_dashboard():
    """启动简洁版 Web 界面"""
    from src.dashboard import start_dashboard
    print("\n📊 启动简洁版 Dashboard...")
    print("   URL: http://localhost:5000")
    print("   按 Ctrl+C 停止")
    start_dashboard(port=5000)


def run_api_server():
    """启动 REST API"""
    from src.api import start_api_server
    print("\n🔌 启动 REST API Server...")
    print("   API: http://localhost:5001")
    print("   Docs: http://localhost:5001/")
    print("   按 Ctrl+C 停止")
    start_api_server(port=5001)


def show_analytics():
    """显示统计信息"""
    from src.analytics import show_analytics
    show_analytics()


def run_test_mode():
    """测试模式"""
    from src.fetcher import fetch_news
    from src.summarizer import generate_article
    from src.mock_data import get_mock_news
    
    print("\n🧪 测试模式")
    print("="*50)
    
    print("\n[1/2] 获取新闻...")
    news_items = fetch_news()
    
    if not news_items:
        print("   未获取到新闻，使用模拟数据")
        news_items = get_mock_news(5)
    
    print(f"   获取到 {len(news_items)} 条新闻")
    
    print("\n[2/2] 生成文章...")
    article = generate_article(news_items)
    
    print(f"\n✅ 文章生成完成 ({len(article)} 字符)")
    print("\n" + "="*50)
    print("📄 文章预览 (前2000字符):")
    print("="*50)
    print(article[:2000])
    if len(article) > 2000:
        print(f"\n... 还有 {len(article) - 2000} 字符")


def run_health_check():
    """健康检查"""
    from src.health import get_health_checker
    
    print("\n🏥 健康检查")
    print("="*50)
    
    checker = get_health_checker()
    report = checker.get_status_report()
    
    print(f"\n📊 整体状态: {report['status']}")
    print(f"⏰ 检查时间: {report['timestamp']}")
    
    print("\n📋 检查详情:")
    for name, check in report['checks'].items():
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌",
            "unknown": "❓"
        }
        emoji = status_emoji.get(check['status'], "❓")
        print(f"   {emoji} {name}: {check['message']} ({check['duration_ms']:.1f}ms)")


def run_config_validation():
    """验证配置"""
    from src.validate_config import validate_all
    
    print("\n✅ 配置验证")
    print("="*50)
    
    try:
        results = validate_all()
        
        for category, checks in results.items():
            print(f"\n📁 {category}:")
            for check, status in checks.items():
                emoji = "✅" if status else "❌"
                print(f"   {emoji} {check}")
    except Exception as e:
        print(f"❌ 验证失败: {e}")


def run_mock_mode():
    """使用模拟数据运行"""
    from src.mock_data import get_mock_news
    from src.summarizer import generate_article
    from src.unified_publisher import publish_article_unified
    
    print("\n🎭 模拟数据模式")
    print("="*50)
    
    news_items = get_mock_news(5)
    print(f"\n📰 模拟新闻: {len(news_items)} 条")
    
    article = generate_article(news_items)
    print(f"📝 文章生成: {len(article)} 字符")
    
    today = datetime.now().strftime("%Y年%m月%d日")
    title = f"🎯 {today} AI 资讯日报（模拟）"
    
    result = publish_article_unified(
        title=title,
        content=article,
        mode="simple"
    )
    
    if result["success"]:
        print(f"\n✅ 运行完成!")
        for f in result["files"]:
            print(f"   - {f}")
    else:
        print(f"\n❌ 运行失败: {result.get('error')}")


def run_custom_article(args=None):
    """生成自定义文章"""
    from src.custom_article import generate_custom_article
    from src.publisher import publish_article
    
    print("\n" + "="*50)
    print("[INFO] AI News Publisher - 生成自定义文章")
    print("="*50)
    
    start_time = datetime.now()
    
    try:
        # 1. 确定文章类型
        article_type = "meeting_tools_review"
        if args and hasattr(args, 'type'):
            article_type = args.type
        
        print(f"\n[STEP 1/3] 生成{article_type}文章...")
        
        # 2. 生成文章
        article_content = generate_custom_article(article_type)
        print(f"   生成完成 ({len(article_content)} 字符)")
        
        # 3. 确定标题
        today = datetime.now().strftime("%Y年%m月%d日")
        if article_type == "meeting_tools_review":
            title = "AI Meeting Tools Review"
        else:
            title = f"{today} Custom Article"
        
        # 4. 如果指定了发布参数，发布到草稿箱
        if args and hasattr(args, 'publish') and args.publish:
            print("\n[STEP 2/2] 发布到微信草稿箱...")
            publish_success = publish_article(
                title=title,
                content=article_content,
                auto_publish=False
            )
            if publish_success:
                print("   [SUCCESS] 已发布到微信草稿箱")
            else:
                print("   [ERROR] 发布到微信草稿箱失败")
        else:
            # 仅保存到本地
            print("\n[STEP 2/2] 保存文章到本地...")
            from pathlib import Path
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            md_path = output_dir / f"article_{datetime.now().strftime('%Y%m%d')}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(article_content)
            print(f"   已保存: {md_path}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*50)
        print("[SUCCESS] 运行完成！")
        print(f"   耗时: {elapsed:.1f}秒")
        print("="*50)
        
    except Exception as e:
        print(f"\n[ERROR] 运行失败: {e}")
        logger.error(f"run_custom_article 失败: {e}", exc_info=True)


if __name__ == "__main__":
    main()