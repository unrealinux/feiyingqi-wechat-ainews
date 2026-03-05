"""
Cover Generator CLI - 封面图生成命令行工具
"""
import argparse
import sys
from src.cover_generator import generate_cover_image, CoverGenerator


def main():
    parser = argparse.ArgumentParser(
        description="生成公众号封面图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m src.cover_generator "OpenAI发布GPT-5"
  python -m src.cover_generator "AI新闻日报" -o output/cover.png
  python -m src.cover_generator "今日AI资讯" --ai --provider tongyi
        """
    )
    
    parser.add_argument("title", nargs="?", help="文章标题")
    parser.add_argument("-o", "--output", default="output/cover.png", help="输出路径")
    parser.add_argument("-s", "--style", default="modern", choices=["modern", "minimal", "bold"], help="风格")
    parser.add_argument("--ai", action="store_true", help="使用AI生成背景")
    parser.add_argument("--provider", default="tongyi", choices=["tongyi", "baidu", "stability"], help="AI提供商")
    parser.add_argument("--list-styles", action="store_true", help="列出可用风格")
    
    args = parser.parse_args()
    
    if args.list_styles:
        print("可用风格:")
        print("  modern  - 现代科技风 (默认)")
        print("  minimal - 简约风格")
        print("  bold    - 醒目大胆风格")
        return
    
    if not args.title:
        parser.print_help()
        return
    
    # 生成封面
    print(f"🎨 正在生成封面: {args.title}")
    print(f"   风格: {args.style}")
    print(f"   输出: {args.output}")
    
    if args.ai:
        print(f"   AI: {args.provider} (生成中...)")
    
    result = generate_cover_image(
        title=args.title,
        output_path=args.output,
        use_ai=args.ai,
        provider=args.provider
    )
    
    if result:
        print(f"\n✅ 封面已生成: {result}")
    else:
        print("\n❌ 生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
