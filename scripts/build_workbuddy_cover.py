#!/usr/bin/env python3
"""WorkBuddy 风格封面（原创手绘，不搬任何原图）。

视觉语言来自社区《WorkBuddy 实战蓝皮书》的 banner / og 图：荧光黄绿底 + 黑色超粗
中文标题 + 白色像素图标卡 + 底部黑条 + 等宽小字。只学配色、层级、构图，
图素全部用 PIL 自己画（skill wechat-tietu 的红线也是“不搬原图”）。

用法：
    python scripts/build_workbuddy_cover.py output/workbuddy_cover_brand.jpg
"""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 1440, 810
THUMB_RATIO = 2.35  # 微信列表缩略图比例：关键信息要落在中间这条带里

BG = (216, 241, 75)  # 蓝皮书品牌荧光绿
INK = (16, 16, 16)
TILE = (255, 255, 255)

FONTS = [
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]


def font(size, bold=True):
    order = FONTS if bold else FONTS[1:] + FONTS[:1]
    for path in order:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError("找不到可用中文字体")


def draw_tracked(draw, xy, text, fnt, fill, tracking=8):
    """逐字画，做出 banner 那种拉开字距的等宽小字效果。"""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking


def icon_laptop(d, x, y, s):
    d.rectangle([x, y, x + 8 * s, y + 5 * s], outline=INK, width=s)
    d.rectangle([x - s, y + 6 * s, x + 9 * s, y + 7 * s], fill=INK)


def icon_bot(d, x, y, s):
    d.rectangle([x, y + s, x + 8 * s, y + 7 * s], outline=INK, width=s)
    d.line([x + 4 * s, y + s, x + 4 * s, y - s], fill=INK, width=s)
    d.rectangle([x + 3 * s, y - 2 * s, x + 5 * s, y], fill=INK)
    d.rectangle([x + 2 * s, y + 3 * s, x + 3 * s, y + 4 * s], fill=INK)
    d.rectangle([x + 5 * s, y + 3 * s, x + 6 * s, y + 4 * s], fill=INK)


def icon_case(d, x, y, s):
    d.rectangle([x, y + s, x + 8 * s, y + 6 * s], outline=INK, width=s)
    d.rectangle([x + 3 * s, y - s, x + 5 * s, y + s], outline=INK, width=s)
    d.rectangle([x, y + 3 * s, x + 8 * s, y + 4 * s], fill=INK)


def tile(draw, x, y, size, icon, scale=14):
    draw.rectangle([x, y, x + size, y + size], fill=TILE)
    icon(draw, x + size * 0.2, y + size * 0.28, scale)


def build(out_path: str):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 左上小字
    draw_tracked(
        d,
        (84, 96),
        "社区蓝皮书 · 10 章实操 · 2026",
        font(22, bold=False),
        INK,
        tracking=4,
    )

    # 主标题（两行，超粗）
    d.text((84, 190), "WorkBuddy 怎么用", font=font(96), fill=INK)
    d.text((84, 310), "从第一项任务开始", font=font(96), fill=INK)

    # 副标题
    d.text(
        (88, 462),
        "专家团 · Skill · 连接器 · 自动化任务",
        font=font(38, bold=False),
        fill=INK,
    )

    # 右侧像素图标卡（位置错落，模仿 banner 的漂浮卡）
    tile(d, 1000, 120, 210, icon_bot)
    tile(d, 1180, 300, 200, icon_laptop)
    tile(d, 960, 400, 200, icon_case)

    # 底部黑条
    d.rectangle([0, H - 96, W, H], fill=INK)
    d.text(
        (84, H - 72), "把重复劳动变成可复用的系统", font=font(34, bold=False), fill=BG
    )
    draw_tracked(d, (W - 190, H - 66), "WB_", font(30, bold=False), BG, tracking=2)

    img.save(out_path, quality=93)

    # 缩略图安全区自检：微信列表取中间 2.35:1
    crop_h = int(W / THUMB_RATIO)
    top = (H - crop_h) // 2
    thumb = Path(out_path).with_name("_thumb_preview.jpg")
    img.crop((0, top, W, top + crop_h)).save(thumb, quality=92)
    print(f"封面: {out_path} {img.size} | 缩略图模拟: {thumb}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WorkBuddy 风格封面（原创）")
    parser.add_argument("out", nargs="?", default="output/workbuddy_cover_brand.jpg")
    build(parser.parse_args().out)
