#!/usr/bin/env python3
"""用 workbuddy-guide 技能里的《WorkBuddy 实战蓝皮书》出一篇使用向文章（只生成预览，不建草稿）。

素材是本地技能目录里的章节原文（自带出处：章节号 + 标题），不是模型凭记忆写的
WorkBuddy 参数 —— 这是走"工具怎么用"这条路的前提。

用法：
    python scripts/gen_workbuddy_article.py            # 生成预览（不建草稿）
    python scripts/gen_workbuddy_article.py --publish  # 把审过的预览发成草稿（一天最多一篇）
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import editorial_template  # noqa: E402
from src.ai_score import check_ai_score  # noqa: E402
from src.fetcher import NewsItem  # noqa: E402
from src.summarizer import Summarizer  # noqa: E402
from src.materials import chapter_url, references_dir, source_label  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

# 使用手册篇（第一篇）里最像"怎么用"的章节。
# 注意：蓝皮书是社区项目（AlephAITech/WorkBuddyGuide, MIT, workbuddy.homes），
# 不是腾讯官方文档 —— 署名不能搞错，产品界面/价格以官方为准（skill 里写明的三层区分）。
# 素材路径统一登记在 src/materials.py（原来这里写死的 ~/.agents/skills 早已不存在）
SKILL_DIR = references_dir("workbuddy")
BRAND_COVER = Path("output/workbuddy_cover_brand.jpg")  # 手绘品牌风封面，优先复用
BODY_FILE = Path("output/workbuddy_body.html")
TUTORIAL_BODY_FILE = Path("output/workbuddy_body_tutorial.html")
CASES_BODY_FILE = Path("output/workbuddy_body_cases.html")
SOURCE_LABEL = source_label("workbuddy")

EXTRA_INSTRUCTION = (
    "\n\n取材说明（必须体现到成稿里）：本篇素材来自社区整理的《WorkBuddy 实战蓝皮书》"
    "（GitHub: AlephAITech/WorkBuddyGuide，站点 workbuddy.homes，MIT），**不是腾讯官方文档**；"
    "sources 里不要写成“腾讯《WorkBuddy 实战蓝皮书》”，要写清是社区整理、并只列实际用到的章节；"
    "涉及界面、价格、额度、权限时加一句“以 WorkBuddy 官方渠道为准”。"
)
DOUBAO_EXTRA_INSTRUCTION = (
    "\n\n取材说明（必须体现到成稿里）：本篇素材来自社区整理的《豆包工作实战指南》"
    "（GitHub: AlephAITech/DoubaoWorkGuide，站点 doubaowork.homes，MIT），**不是字节跳动官方文档**；"
    "sources 里不要写成“字节《豆包工作实战指南》”，要写清是社区整理、并只列实际用到的章节"
    "（每章都有 doubaowork.homes 的在线地址，能列就列全）；"
    "涉及界面、价格、额度、权限时加一句“以豆包工作官方渠道为准”。"
)


def extra_instruction(material: str) -> str:
    return DOUBAO_EXTRA_INSTRUCTION if material == "doubaowork" else EXTRA_INSTRUCTION


# --tutorial 时叠加的结构要求：操作指南不能写成“深读”
TUTORIAL_INSTRUCTION = (
    "\n\n本篇是**操作指南**，不是观点深读。硬要求："
    "① kicker 写“AI 前沿观察 · 实操指南”，meta_line 写清“读者看完能干什么”；"
    "② 第二到第四节必须是**可执行步骤**：用 steps 块（{{type: steps, items: [{{title, detail}}]}}），"
    "title 写动作（如“在设置里接入自己的 API Key”），detail 写“在哪个界面 → 点什么 → 填什么 → 会看到什么”；不许写成概念介绍；"
    "③ 单独一节写“容易踩的坑”：素材里写到的限制（额度/权限/本机与云端差异）+ 怎么绕；"
    "④ 最后一节写“什么情况下不值得用”，不要堆夸张形容词；"
    "⑤ **正文里不要写“第 N 章”这类章号**（容易标错），章号只在 sources 里出现；"
    "⑥ 链接要把完整地址写出来（含 https://），因为这是操作指南，读者要能直接点。"
    "标题写成读者会搜的句式（如“WorkBuddy 怎么用：从装到跑通第一个任务”），不要抽象口号。"
)

# --cases 时叠加的结构要求：案例篇写“把哪类活派给它、任务怎么描述、验收看什么”
CASES_INSTRUCTION = (
    "\n\n本篇是**派活指南**（第二篇，假设读者已经装好能用），不是安装教程。硬要求："
    "① kicker 写“AI 前沿观察 · 实操指南”，meta_line 写清“读者看完能把哪几类活交出去”；"
    "② 主体按“任务类型”分节，每节讲清：这类活原来怎么做 → 交给它时要交代哪几件事（目标/受众/材料/格式/验收）→ 产出后人工检查什么；"
    "③ 至少一节用 steps 块（{{type: steps, items: [{{title, detail}}]}}）写会议后落到待办的具体链路；"
    "④ 单独一节写“派活失败最常见的原因”，要具体（交付标准没说清、材料口径不唯一、验收标准缺失），不要写空话；"
    "⑤ 最后一节写“哪些活别交给它”；"
    "⑥ 正文里不要写“第 N 章”这类章号，章号只在 sources 里出现；不要重复讲下载安装、界面三栏这类第一篇已讲的内容。"
    "标题写成读者会搜的句式（如“WorkBuddy 能替你干哪些活：四类任务怎么派”），不要抽象口号。"
)

# 案例篇：已经装好之后，哪些真实的活可以派出去（与第一篇选题不重叠）
CASES = [
    ("chapters/part2-ch11.md", "第 12 章 办公三件套：Word、Excel、PPT"),
    ("chapters/part2-ch12.md", "第 13 章 从整理桌面文件这些小事做起"),
    ("chapters/part2-ch15.md", "第 16 章 资讯整合：把信息流变成每日通知"),
    ("chapters/part2-ch17.md", "第 18 章 会议结束不是终点，工作才刚刚开始"),
    ("chapters/part3-ch25.md", "第 26 章 自动化工作流的可靠性"),
]

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

# 每日 16:00 轮换用：周一→周日七套选题，同一主题至少隔 7 天，
# 避免“同一套结构换名词”被判低质（AGENTS.md 第 0 节）。
DAILY_INSTRUCTION = (
    "\n\n本篇是**实操指南**，读者是已经知道 WorkBuddy 是什么、想按图操作的职场人。硬要求："
    "① kicker 写“AI 前沿观察 · 实操指南”，meta_line 写清“读完能干什么”；"
    "② 至少一节用 steps 块（{{type: steps, items: [{{title, detail}}]}}）：title 写动作，detail 写“在哪个界面 → 点什么 → 填什么 → 会看到什么”；"
    "③ 单独一节写“容易踩的坑”（额度/权限/本机与云端差异），每条给出绕法；"
    "④ 最后一节写“什么情况下不值得用”；"
    "⑤ 正文里不要写“第 N 章”这类章号，章号只在 sources 里出现；不要写“在上一篇文章中”这类延续性表述；"
    "⑥ 标题必须以“{name}”开头，写成读者会搜的句式，10~28 个字。"
)

PRESETS = [
    dict(
        name="安装与第一个任务",
        cover_sub="装好、登录、跑通第一个任务",
        cover_title="WorkBuddy 上手|从装到第一个任务",
        cover_label="下载 → 登录 → 任务 → 结果",
        focus="下载安装、登录、主界面三栏结构、完成第一个任务、加载一个能用的 Skill",
        chapters=CHAPTERS[:5],
    ),
    dict(
        name="办公文档",
        cover_sub="写 Word/Excel/PPT 前要交代的五件事",
        cover_title="WorkBuddy 写文档|Word Excel PPT",
        cover_label="说清目标 → 指定材料 → 验收",
        focus="Word/Excel/PPT 三件套：派活前要交代的五个问题（目标、受众、材料、格式、验收）、Office 类 Skill 怎么选、产出后人工检查什么",
        chapters=[
            ("chapters/part2-ch11.md", "第 12 章 办公三件套：Word、Excel、PPT"),
            ("chapters/part1-ch05.md", "第 5 章 加载一个真正用得上的 Skill"),
        ],
    ),
    dict(
        name="文件与琐事",
        cover_sub="桌面发票与下载目录，先只读再动手",
        cover_title="WorkBuddy 理文件|桌面不再靠人扛",
        cover_label="只读扫描 → 清单 → 台账",
        focus="桌面发票/下载文件整理、生活琐事（通知、缴费、行程类）交给它做初筛，以及本机权限边界",
        chapters=[
            ("chapters/part2-ch12.md", "第 13 章 从整理桌面文件这些小事做起"),
            ("chapters/part2-ch13.md", "第 14 章 远程控制你的电脑，不用发愁不在电脑前"),
            ("chapters/part2-ch14.md", "第 15 章 生活助手的价值，是减少琐碎"),
        ],
    ),
    dict(
        name="连接器与外部系统",
        cover_sub="先接连接器，再开远程入口，最后换模型",
        cover_title="WorkBuddy 接系统|MCP 连接器与 API",
        cover_label="连接器 → 小程序 → 外部 API",
        focus="连接器/MCP 的接入顺序、微信小程序与 IM 助理怎么当远程入口、接外部 API 时要交代的密钥与权限",
        chapters=[
            ("chapters/part1-ch07.md", "第 7 章 使用连接器"),
            ("chapters/part1-ch08.md", "第 9 章 接入小程序与 IM 助理"),
            ("chapters/part1-ch09.md", "第 10 章 接入外部 API"),
        ],
    ),
    dict(
        name="会议与资讯",
        cover_sub="会前议程到会后待办，一条链走完",
        cover_title="WorkBuddy 做闭环|会议纪要到待办",
        cover_label="会前 → 转写 → 待办 → 追踪",
        focus="会议前中后一条链（议程、转写、纪要、待办、追踪）和资讯整合（信息流变每日通知），以及必须留人的检查点",
        chapters=[
            ("chapters/part2-ch17.md", "第 18 章 会议结束不是终点，工作才刚刚开始"),
            ("chapters/part2-ch15.md", "第 16 章 资讯整合：把信息流变成每日通知"),
        ],
    ),
    dict(
        name="自动化与可靠性",
        cover_sub="手动跑稳三次，再挂定时任务",
        cover_title="WorkBuddy 自动化|从手动到定时可靠",
        cover_label="手动三次 → 定时 → 告警停用",
        focus="自动化任务怎么设、什么条件才配自动化（三个门槛）、失败告警与停用、可靠性怎么验",
        chapters=[
            ("chapters/part1-ch10.md", "第 11 章 自动化任务"),
            ("chapters/part3-ch25.md", "第 26 章 自动化工作流的可靠性"),
        ],
    ),
    dict(
        name="多 Agent 与岗位落地",
        cover_sub="专家团怎么分工，岗位从哪先用",
        cover_title="WorkBuddy 组队|多 Agent 与岗位路线",
        cover_label="专家团 → 多 Agent → 岗位路线",
        focus="专家/专家团、多 Agent 系统怎么分工、不同岗位（运营、产品、职能）从哪个场景先用起来",
        chapters=[
            ("chapters/part1-ch06.md", "第 6 章 专家和专家团"),
            ("chapters/part3-ch24.md", "第 25 章 如何进行多 Agent 系统设计"),
            (
                "chapters/part4-ch26.md",
                "第 27 章 岗位路线图：不同岗位如何把 WorkBuddy 用深",
            ),
        ],
    ),
]


# 豆包工作：另一套社区指南素材，15:00 那档跟 WorkBuddy 隔天轮换。
# 章节相对路径都在 ~/文档/doubaowork-guide-skill/.../references/ 下。
DOUBAO_PRESETS = [
    dict(
        name="装好并跑通第一个任务",
        cover_sub="下载 → 登录 → 第一个任务",
        cover_title="豆包工作上手|从装到第一个任务",
        cover_label="下载 → 登录 → 任务 → 结果",
        focus="下载安装与登录、主界面/任务/项目的关系、五分钟跑完第一个任务",
        chapters=[
            ("chapters/part1-02.md", "豆包工作的下载、安装和登录"),
            ("chapters/part1-03.md", "主界面、任务和项目，一张图讲明白"),
            ("chapters/part1-04.md", "五分钟跑完第一个豆包工作任务"),
        ],
    ),
    dict(
        name="Skill 与连接器怎么选",
        cover_sub="Skill / 连接器 / API 三条路怎么分工",
        cover_title="豆包工作|Skill 与连接器怎么选",
        cover_label="先定场景 → 再选通道",
        focus="Skill 怎么选怎么用、连接器怎么跑通一个能验收的小任务、API 服务与连接器怎么选",
        chapters=[
            ("chapters/part1-06.md", "豆包工作的 Skill 怎么选，怎么用"),
            ("chapters/part1-05.md", "连接器怎么用，先跑一个能验收的小任务"),
            ("chapters/part1-09.md", "API 服务和连接器，到底该怎么选？"),
        ],
    ),
    dict(
        name="定时任务",
        cover_sub="定时任务怎么建才稳定出结果",
        cover_title="豆包工作|定时任务怎么建",
        cover_label="定时间 → 定产出 → 定验收",
        focus="定时任务怎么建才能稳定产出结果、每天早上自动收到资讯简报、工作日报自动总结",
        chapters=[
            ("chapters/part1-10.md", "定时任务怎么建，才能稳定产出结果"),
            ("chapters/part2-06.md", "每天早上自动收到一份能用的资讯简报"),
            ("chapters/part3-personal-06.md", "自动总结工作日报，提醒每日工作事项"),
        ],
    ),
    dict(
        name="办公三件套",
        cover_sub="一份材料接着做 Word / Excel / PPT",
        cover_title="豆包工作|接着做 Word Excel PPT",
        cover_label="给材料 → 说格式 → 验产出",
        focus="一份材料怎么让它接着做 Word/Excel/PPT、Word 校对润色到排版交付、Excel 数据分析",
        chapters=[
            (
                "chapters/part2-01.md",
                "一份材料，怎么让豆包工作接着做 Word、Excel 和 PPT",
            ),
            ("chapters/part3-personal-03.md", "一份 Word，从校对润色到排版交付"),
            ("chapters/part3-personal-04.md", "随意操作Excel，秒变数据分析大师"),
        ],
    ),
    dict(
        name="多 Agent 工作小队",
        cover_sub="什么时候开小队，什么时候自己干",
        cover_title="豆包工作|多 Agent 怎么用",
        cover_label="拆任务 → 派角色 → 合结果",
        focus="什么时候找工作伙伴/小队、多 Agent（工作小队）怎么用、常用指令模板怎么改",
        chapters=[
            ("chapters/part1-07.md", "什么时候找工作伙伴/小队，什么时候直接开新任务"),
            ("chapters/part1-11.md", "多 Agent（工作小队）怎么用？"),
            ("chapters/part1-12.md", "豆包工作常用指令模板，随手复制就能用"),
        ],
    ),
    dict(
        name="手机接管电脑任务",
        cover_sub="出门之后怎么接着跑电脑上的活",
        cover_title="豆包工作|手机接着跑",
        cover_label="任务在电脑 → 验收在手机",
        focus="怎么用手机操控电脑端豆包工作、出门以后怎么用手机接着跑电脑上的任务",
        chapters=[
            ("chapters/part1-08.md", "怎么用手机操控电脑端豆包工作"),
            ("chapters/part2-04.md", "出门以后，怎么用手机接着跑电脑上的任务"),
        ],
    ),
]


def material_spec(material: str) -> dict:
    """素材源 → 选题表与署名口径（两套都是社区整理，不是官方文档）。"""
    if material == "doubaowork":
        return {
            "name": "豆包工作",
            "presets": DOUBAO_PRESETS,
            "kicker": "豆包工作 · 每日实操",
            "footer": "素材出自社区整理指南，界面以官方为准",
        }
    return {
        "name": "WorkBuddy",
        "presets": PRESETS,
        "kicker": "WorkBuddy · 每日实操",
        "footer": "素材出自社区整理蓝皮书，界面以官方为准",
    }


def _excerpt(text: str, limit: int = 500) -> str:
    """取章节开头一段：去掉标题行和空行，压成一行。NewsItem 自身也会截到 500 字。"""
    lines = [ln.strip() for ln in text.splitlines()]
    body = [
        ln for ln in lines if ln and not ln.startswith("#") and not ln.startswith(">")
    ]
    return " ".join(body)[:limit]


def build_material(chapter_count: int, chapters=None, material: str = "workbuddy"):
    base = references_dir(material)
    label_src = source_label(material)
    items = []
    for rel, label in (chapters or CHAPTERS)[:chapter_count]:
        path = base / rel
        if not path.exists():
            print(f"跳过（不存在）: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        items.append(
            NewsItem(
                title=label,
                # 豆包工作的章节头部带单章在线地址；WorkBuddy 只有上游 GitHub 路径，
                # 没有 URL 时出处靠"蓝皮书 + 章号"（由 EXTRA_INSTRUCTION 约束署名）
                url=chapter_url(text) or "",
                source=label_src,
                description=_excerpt(text),
            )
        )
    return items


def publish_reviewed(preview_path: str, body_path: Path = BODY_FILE) -> int:
    """把已审阅的预览发成草稿：不重新生成正文，否则发的就不是你审的那一篇。

    日产上限按 config.yaml 的 scheduler.max_drafts_per_day（默认 1）。
    """
    import re

    from src.publisher import count_drafts_created_today, publish_article

    preview = Path(preview_path)
    if not body_path.exists() or not preview.exists():
        print(f"没有可发的正文（先跑一次不带 --publish 的生成）: {body_path}")
        return 1

    max_per_day = drafts_today_limit()
    already = count_drafts_created_today()
    if already >= max_per_day:
        print(f"今天草稿箱里已有 {already} 篇（上限 {max_per_day}），拒绝再发。")
        print("要今天发就先人工处理掉当天那篇，或明天再跑。")
        return 1

    match = re.search(
        r"<title>(.*?)</title>", preview.read_text(encoding="utf-8"), re.S
    )
    title = (match.group(1).strip() if match else "").replace(chr(10), " ")
    content = body_path.read_text(encoding="utf-8")

    # 优先用手绘品牌风封面（迭代过的那版），没有再按当天日期找/生成
    cover = (
        str(BRAND_COVER)
        if BRAND_COVER.exists()
        else f"output/workbuddy_cover_{datetime.now().strftime('%Y%m%d')}.jpg"
    )
    if not Path(cover).exists():
        print(f"生成封面: {cover}")
        from src.ai_photo_cover import generate_ai_photo_cover

        ok, theme = generate_ai_photo_cover(title, cover, theme="workbench")
        print(f"  封面 {'成功' if ok else '失败'}（主题 {theme}）")
        if not ok:
            cover = ""

    print(f"创建草稿（仅草稿，不群发）: {title}")
    ok = publish_article(
        title=title,
        content=content,
        author="AI前沿观察",
        cover_path=cover,
        content_is_html=True,
        auto_publish=False,
    )
    print("成功：草稿已建" if ok else "失败：见上文日志")
    if not ok:
        _notify_failure(f"建草稿失败（{preview.name}），见日志")
    return 0 if ok else 1


def generate_article(
    chapters, instruction, preview_path, body_path, material: str = "workbuddy"
):
    """出稿并落盘（预览 + 正文两份，publish 用的是 body）。返回 (title, html)。"""
    items = build_material(len(chapters), chapters, material=material)
    if not items:
        raise RuntimeError("没有可用素材")
    print(f"素材: {len(items)} 个章节，来自 {references_dir(material)}")

    spec = Summarizer().generate_editorial_spec(
        items, allow_mock=False, extra_instruction=instruction
    )
    title = editorial_template.draft_title(spec)
    html = editorial_template.render(spec)

    Path(preview_path).write_text(
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        f"<title>{title}</title></head><body style='background:#EDEAE3'>{html}</body></html>",
        encoding="utf-8",
    )
    # 正文单独存一份：--publish 用的是这一份，也就是人看过的那一版
    Path(body_path).write_text(html, encoding="utf-8")
    return title, html


def _remote_material_titles(keyword: str):
    """草稿箱里今天还没发出去的该产品稿；接口不可用返回 None。"""
    import requests

    from src.publisher import WeChatPublisher

    try:
        token = WeChatPublisher().get_access_token()
        if not token:
            return None
        resp = requests.post(
            "https://api.weixin.qq.com/cgi-bin/draft/batchget",
            params={"access_token": token},
            json={"offset": 0, "count": 20},
            timeout=15,
        )
        resp.encoding = "utf-8"  # 响应不带 charset，requests 会按 latin-1 解
        data = resp.json()
        if data.get("errcode"):
            return None
        today = datetime.now().date()
        return [
            item["content"]["news_item"][0]["title"]
            for item in data.get("item", [])
            if datetime.fromtimestamp(item["update_time"]).date() == today
            and keyword in item["content"]["news_item"][0]["title"]
        ]
    except Exception as e:
        print(f"读草稿箱失败，改用本地台账去重: {e}")
        return None


def drafts_today_limit() -> int:
    """日产上限：config.yaml 的 scheduler.max_drafts_per_day（缺省 1）。"""
    from src.config import get_scheduler_config, load_config

    return int(get_scheduler_config(load_config()).get("max_drafts_per_day", 1) or 1)


def material_titles_today(material: str = "workbuddy") -> list:
    """今天草稿箱里已有的该产品稿（定时任务去重用，不靠人记得）。

    以草稿箱为准：用户手动删掉的稿不该继续占着“今天已发”的名额。
    接口读不到才退回本地台账 —— 宁可少发一篇，也不要同一天出两篇。
    """
    keyword = material_spec(material)["name"]
    remote = _remote_material_titles(keyword)
    if remote is not None:
        return remote
    return _ledger_material_titles(keyword)


def _ledger_material_titles(keyword: str) -> list:
    """本地台账里今天的该产品稿（草稿箱读不到时的兜底）。"""
    import json

    from src.monitoring import DRAFT_LEDGER  # 台账只有这一处定义，测试能替换掉

    path = Path(DRAFT_LEDGER)
    if not path.exists():
        return []
    today = datetime.now().strftime("%Y-%m-%d")
    titles = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(record.get("time", "")).startswith(today) and keyword in str(
            record.get("title", "")
        ):
            titles.append(record["title"])
    return titles


def _notify_failure(reason: str) -> None:
    """定时任务失败要有声音：2026-10-27 16:00 那次 LLM 连接失败，没人知道。

    复用调度器已有的通知通道；通知本身失败不得影响退出码。
    """
    try:
        from src.monitoring import record_alert, send_run_notification

        send_run_notification("error", {"error": reason})
        record_alert(f"WorkBuddy 定时任务失败: {reason}")
    except Exception as e:
        print(f"失败通知没发出去（不影响退出码）: {e}")


def run_daily(
    force: bool = False, preset_name: str = "", material: str = "workbuddy"
) -> int:
    """定时任务入口：按星期轮换选题 → 出稿 → 建草稿（不群发）。

    没人先审预览，所以封面和 AI 味门禁由代码保证：publish_article 自带门禁，
    封面用本地手绘版式（不调外部出图，也不会挑错图）。

    material: workbuddy / doubaowork，两套社区指南素材，各自一套选题。
    force / preset_name 只给人工临时补稿用；定时任务不需要。
    """
    from src.publisher import publish_article

    spec = material_spec(material)
    refs = references_dir(material)
    presets = spec["presets"]

    if not refs.exists():
        print(f"找不到素材目录: {refs}")
        return 1

    from src.publisher import count_drafts_created_today

    max_per_day = drafts_today_limit()
    already_today = count_drafts_created_today()
    if already_today >= max_per_day:
        print(f"今天已有 {already_today} 篇草稿（上限 {max_per_day}），本次不产出。")
        return 0

    done = material_titles_today(material)
    if done and not force:
        print(f"今天已有 {spec['name']} 草稿《{done[0]}》，本次跳过。")
        return 0
    if done:
        print(f"今天已有 {len(done)} 篇，按人工要求强制再出一篇。")

    now = datetime.now()
    preset = presets[now.weekday() % len(presets)]
    if preset_name:
        match = [p for p in presets if preset_name in p["name"]]
        if not match:
            print(
                f"没有这个选题: {preset_name}（可选: {[p['name'] for p in presets]}）"
            )
            return 1
        preset = match[0]
    print(f"今日选题: {preset['name']}（周{now.isoweekday()}）")

    stamp = now.strftime("%Y%m%d")
    body_path = Path(f"output/{material}_body_{stamp}.html")
    instruction = (
        extra_instruction(material)
        + DAILY_INSTRUCTION.format(name=spec["name"])
        + f"\n\n本次聚焦：{preset['focus']}"
    )
    try:
        title, html = generate_article(
            preset["chapters"],
            instruction,
            f"output/preview_{material}_{stamp}.html",
            body_path,
            material=material,
        )
    except Exception as e:
        print(f"出稿失败，本次不建草稿: {e}")
        _notify_failure(f"出稿失败（{preset['name']}）: {e}")
        return 1

    from src.utils import html_to_text

    passed, report = check_ai_score(html_to_text(html))
    print(
        f"标题: {title} | AI 味 {report['total_score']} {'通过' if passed else '不通过'}"
    )
    if not passed:
        print("门禁不通过，不建草稿（预览已落盘，改完手动重跑）")
        _notify_failure(f"AI 味门禁拦截（{preset['name']}）: {report['total_score']}")
        return 1

    # 封面：复用 build_workbuddy_cover 的 steps 版式，文案跟当天选题走
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_workbuddy_cover import build as build_cover

    cover = f"output/{material}_cover_{stamp}.jpg"
    try:
        build_cover(
            cover,
            title_lines=preset["cover_title"].split("|"),
            kicker=f"{spec['kicker']} · {now.strftime('%Y-%m-%d')}",
            subtitle=preset["cover_sub"],
            footer=spec["footer"],
            variant="steps",
            steps_label=preset["cover_label"],
        )
    except Exception as e:
        print(f"封面生成失败，用兜底封面: {e}")
        cover = str(BRAND_COVER) if BRAND_COVER.exists() else ""

    ok = publish_article(
        title=title,
        content=body_path.read_text(encoding="utf-8"),
        author="AI前沿观察",
        cover_path=cover,
        content_is_html=True,
        auto_publish=False,
    )
    print("成功：草稿已建" if ok else "失败：见上文日志")
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description="用 workbuddy-guide 技能出使用向文章")
    parser.add_argument(
        "--chapters",
        type=int,
        default=0,
        help="用前几章做素材（默认等于所选选题的章数）",
    )
    parser.add_argument("--out", default="")
    parser.add_argument(
        "--tutorial",
        action="store_true",
        help="按操作指南结构出稿（前置→步骤→坑→边界），而不是观点深读",
    )
    parser.add_argument(
        "--cases",
        action="store_true",
        help="按派活指南结构出稿（任务类型→怎么交代→验收），第二篇选题",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="把已审阅的预览发成微信草稿（不重新生成正文，不群发）",
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="定时任务模式：按星期轮换选题，直接出稿并建草稿（每天最多一篇）",
    )
    parser.add_argument(
        "--material",
        default="workbuddy",
        choices=["workbuddy", "doubaowork"],
        help="素材源：workbuddy（蓝皮书）/ doubaowork（豆包工作指南）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="配合 --daily：今天已有 WorkBuddy 稿也再出一篇（人工补稿用）",
    )
    parser.add_argument(
        "--preset", default="", help="配合 --daily：指定选题名（不按星期轮换）"
    )
    args = parser.parse_args()

    if args.daily:
        return run_daily(
            force=args.force, preset_name=args.preset, material=args.material
        )

    if args.cases:
        chapters, instruction, body_path = (
            CASES,
            EXTRA_INSTRUCTION + CASES_INSTRUCTION,
            CASES_BODY_FILE,
        )
        args.out = args.out or "output/preview_workbuddy_cases.html"
    elif args.tutorial:
        chapters, instruction, body_path = (
            CHAPTERS,
            EXTRA_INSTRUCTION + TUTORIAL_INSTRUCTION,
            TUTORIAL_BODY_FILE,
        )
        args.out = args.out or "output/preview_workbuddy.html"
    else:
        chapters, instruction, body_path = CHAPTERS, EXTRA_INSTRUCTION, BODY_FILE
        args.out = args.out or "output/preview_workbuddy.html"

    if args.publish:
        return publish_reviewed(args.out, body_path)

    if not SKILL_DIR.exists():
        print(f"找不到技能目录: {SKILL_DIR}")
        return 1

    if args.chapters:
        chapters = chapters[: args.chapters]
    try:
        title, html = generate_article(chapters, instruction, args.out, body_path)
    except Exception as e:
        print(f"出稿失败: {e}")
        return 1

    from src.utils import html_to_text

    passed, report = check_ai_score(html_to_text(html))
    print(f"\n标题: {title}")
    print(f"预览: {args.out}  （正文 {len(html_to_text(html))} 字）")
    print(f"AI 味: {report['total_score']} / 100  {'通过' if passed else '不通过'}")
    if report["hit_phrases"] or report["hit_vocab"]:
        print(f"  命中套话: {report['hit_phrases']}")
        print(f"  高频词  : {report['hit_vocab']}")
    print("\n未创建任何草稿。看过预览再决定要不要发。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
