#!/usr/bin/env python3
"""用 workbuddy-guide 技能里的《WorkBuddy 实战蓝皮书》出一篇使用向文章（只生成预览，不建草稿）。

素材是本地技能目录里的章节原文（自带出处：章节号 + 标题），不是模型凭记忆写的
WorkBuddy 参数 —— 这是走"工具怎么用"这条路的前提。

用法：
    python scripts/gen_workbuddy_article.py [--chapters N] [--out output/preview_workbuddy.html]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import editorial_template  # noqa: E402
from src.ai_score import check_ai_score  # noqa: E402
from src.fetcher import NewsItem  # noqa: E402
from src.summarizer import Summarizer  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

# 使用手册篇（第一篇）里最像"怎么用"的章节。
# 注意：蓝皮书是社区项目（AlephAITech/WorkBuddyGuide, MIT, workbuddy.homes），
# 不是腾讯官方文档 —— 署名不能搞错，产品界面/价格以官方为准（skill 里写明的三层区分）。
SKILL_DIR = (
    Path.home() / ".agents/skills/workbuddy-guide/skills/workbuddy-guide/references"
)
SOURCE_LABEL = "《WorkBuddy 实战蓝皮书》（社区整理，非官方文档）"

EXTRA_INSTRUCTION = (
    "\n\n取材说明（必须体现到成稿里）：本篇素材来自社区整理的《WorkBuddy 实战蓝皮书》"
    "（GitHub: AlephAITech/WorkBuddyGuide，站点 workbuddy.homes，MIT），**不是腾讯官方文档**；"
    "sources 里不要写成“腾讯《WorkBuddy 实战蓝皮书》”，要写清是社区整理、并只列实际用到的章节；"
    "涉及界面、价格、额度、权限时加一句“以 WorkBuddy 官方渠道为准”。"
)
CHAPTERS = [
    ("chapters/part1-ch01.md", "第 1 章 初识 WorkBuddy"),
    ("chapters/part1-ch02.md", "第 2 章 下载、安装、登录与更新"),
    ("chapters/part1-ch03.md", "第 3 章 主界面、任务与工作区"),
    ("chapters/part1-ch04.md", "第 4 章 快速完成第一个任务"),
    ("chapters/part1-ch05.md", "第 5 章 加载一个真正用得上的 Skill"),
    ("chapters/part1-ch06.md", "第 6 章 专家和专家团"),
    ("chapters/part1-ch07.md", "第 7 章 使用连接器"),
    ("chapters/part1-ch08.md", "第 9 章 接入小程序与 IM 助理"),
    ("chapters/part1-ch09.md", "第 10 章 接入外部 API"),
    ("chapters/part1-ch10.md", "第 11 章 自动化任务"),
]


def _excerpt(text: str, limit: int = 500) -> str:
    """取章节开头一段：去掉标题行和空行，压成一行。NewsItem 自身也会截到 500 字。"""
    lines = [ln.strip() for ln in text.splitlines()]
    body = [
        ln for ln in lines if ln and not ln.startswith("#") and not ln.startswith(">")
    ]
    return " ".join(body)[:limit]


def build_material(chapter_count: int):
    items = []
    for rel, label in CHAPTERS[:chapter_count]:
        path = SKILL_DIR / rel
        if not path.exists():
            print(f"跳过（不存在）: {path}")
            continue
        items.append(
            NewsItem(
                title=label,
                url="",  # 蓝皮书是本地文本，没有单章 URL，出处靠"蓝皮书 + 章号"
                source=SOURCE_LABEL,
                description=_excerpt(path.read_text(encoding="utf-8")),
            )
        )
    return items


def main():
    parser = argparse.ArgumentParser(description="用 workbuddy-guide 技能出使用向文章")
    parser.add_argument(
        "--chapters", type=int, default=len(CHAPTERS), help="用前几章做素材"
    )
    parser.add_argument("--out", default="output/preview_workbuddy.html")
    args = parser.parse_args()

    if not SKILL_DIR.exists():
        print(f"找不到技能目录: {SKILL_DIR}")
        return 1

    items = build_material(args.chapters)
    if not items:
        print("没有可用素材")
        return 1
    print(f"素材: {len(items)} 个章节，来自 {SKILL_DIR}")

    spec = Summarizer().generate_editorial_spec(
        items, allow_mock=False, extra_instruction=EXTRA_INSTRUCTION
    )
    title = editorial_template.draft_title(spec)
    html = editorial_template.render(spec)

    out = Path(args.out)
    out.write_text(
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        f"<title>{title}</title></head><body style='background:#EDEAE3'>{html}</body></html>",
        encoding="utf-8",
    )

    from src.utils import html_to_text

    passed, report = check_ai_score(html_to_text(html))
    print(f"\n标题: {title}")
    print(f"预览: {out}  （正文 {len(html_to_text(html))} 字）")
    print(f"AI 味: {report['total_score']} / 100  {'通过' if passed else '不通过'}")
    if report["hit_phrases"] or report["hit_vocab"]:
        print(f"  命中套话: {report['hit_phrases']}")
        print(f"  高频词  : {report['hit_vocab']}")
    print("\n未创建任何草稿。看过预览再决定要不要发。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
