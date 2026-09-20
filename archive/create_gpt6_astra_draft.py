"""第九篇原创《OpenAI 秀出来的 99.9%，和它藏起来的 41.4%》——GPT-6 Astra 深读
草稿创建脚本（不群发）。

用法（在仓库根目录运行）：
    python archive\\create_gpt6_astra_draft.py --preview   # 仅本地生成封面，无网络请求
    python archive\\create_gpt6_astra_draft.py             # 生成封面 + 创建微信草稿

事实与数据来源（均在文章内标注）：
    - OpenAI GPT-6 Astra 官方发布页/开发者文档/系统卡
    - TechWeb（腾讯新闻 20260904A03YU400 转载）
    - DataLearner 模型库、卡码笔记 9/5 整理
封面：1440×810，纸面报告风（区别于前八篇的深色渐变卡片）。
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import os
import datetime
from PIL import Image, ImageDraw, ImageFont

from publisher import WeChatPublisher

TITLE = "OpenAI 秀出来的 99.9%，和它藏起来的 41.4%"
DIGEST = "GPT-6 Astra 发布一周冷分析：发布会页面上两组数字的落差"
AUTHOR = "AI前沿观察"
COVER_PATH = str(ROOT / "output" / "cv_gpt6_astra.jpg")
HTML_PATH = str(ROOT / "output" / "sample_gpt6_astra_2026-09-10.html")


def font(sz):
    for p in ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def draw_cover():
    """纸面报告风封面：米白纸底 + 两组大数字（墨色 99.9% / 朱红 41.4%）"""
    today = datetime.date.today().strftime("%Y.%m.%d")
    W, H = 1440, 810
    PAPER = (247, 244, 238)
    INK = (28, 27, 24)
    RED = (200, 64, 31)
    TEAL = (31, 111, 91)
    MUTED = (110, 106, 94)
    HAIR = (216, 210, 196)

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # 上下细线框
    d.rectangle([40, 40, W - 40, H - 40], outline=HAIR, width=2)
    d.rectangle([52, 52, W - 52, H - 52], outline=HAIR, width=1)

    # 报头
    d.text((80, 78), "AI 前沿观察 · 第九篇 · 深读", RED, font(26))
    d.text((W - 300, 80), today, MUTED, font(26))
    d.line([80, 130, W - 80, 130], fill=HAIR, width=2)

    # 双数字主体：99.9%（墨色） vs 41.4%（朱红）
    num_y = 200
    d.text((100, num_y), "99.9%", INK, font(150))
    d.text((100, num_y + 180), "ARC-AGI-3 · 放大的那组", MUTED, font(30))

    # 中间竖分隔线
    d.line([W // 2, num_y + 30, W // 2, num_y + 220], fill=HAIR, width=2)

    d.text((W // 2 + 100, num_y), "41.4%", RED, font(150))
    d.text((W // 2 + 100, num_y + 180), "AutomationBench · 藏起来的那组", MUTED, font(30))

    # 主标题
    d.text((100, 620), "GPT-6 Astra：它开始接管鼠标了", INK, font(56))
    d.text((100, 700), "两组都是真的数字，描述的却是两件不同的事", TEAL, font(28))

    img.save(COVER_PATH, quality=95)
    print(f"封面已生成: {COVER_PATH} (1440x810)")


def main():
    if "--preview" in sys.argv:
        draw_cover()
        print(f"本地预览: {HTML_PATH}（用浏览器打开确认排版）")
        return

    # 正式发布流程：本地封面 -> 上传 -> 建草稿（不群发）
    if not os.path.exists(HTML_PATH):
        print(f"[ERROR] 未找到 {HTML_PATH}，请先确认文章预览")
        return

    draw_cover()
    pub = WeChatPublisher()
    html = open(HTML_PATH, encoding="utf-8").read()

    did = pub.create_draft(
        title=TITLE,
        content=html,
        author=AUTHOR,
        digest=DIGEST,
        cover_path=COVER_PATH,
    )
    print("草稿 media_id:", did)
    print("✅ 已建草稿（未群发），请登录 https://mp.weixin.qq.com 查看" if did else "❌ 草稿创建失败")


if __name__ == "__main__":
    main()
