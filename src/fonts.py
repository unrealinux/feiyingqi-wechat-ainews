"""中文字体查找：三个地方（AI 写实封面 / 渐变封面 / 品牌风封面）共用一份候选表。

之前每个文件各写一份 Windows 路径（C:/Windows/Fonts/msyhbd.ttc），
在 Linux 上必然抛"找不到可用中文字体"——2026-11-13 15:00 的工具指南封面
就是这么退化成兜底图的。候选表按"粗体优先"排，跨平台。
"""

import os
from typing import List

CANDIDATES_BOLD: List[str] = [
    # Windows
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    # Linux（Debian/Ubuntu 的 fonts-noto-cjk）
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]

CANDIDATES_REGULAR: List[str] = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]


def find_font(bold: bool = True) -> str:
    """返回第一个存在的字体路径；一个都没有时返回空串（调用方自行降级）。"""
    for path in CANDIDATES_BOLD if bold else CANDIDATES_REGULAR:
        if os.path.exists(path):
            return path
    return ""


def load_font(size: int, bold: bool = True):
    """按尺寸加载中文字体；全都找不到时退回 PIL 默认字体（不抛异常）。"""
    from PIL import ImageFont

    path = find_font(bold)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()
