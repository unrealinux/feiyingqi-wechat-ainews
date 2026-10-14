"""把界面截图做成公众号封面：保证列表缩略图裁切后仍能看到品牌。

微信公众号列表/会话里的封面缩略图是 ~2.35:1 居中裁切（实测 900x383），
16:9 的封面上下各会被切掉约 12%（1440x810 只剩中间 613px）。
所以把界面截图里“WorkBuddy 标识 + 对话 + 结果”这条横带放在正中，
上下用背景色补齐到 1440x810：正文页看是完整 16:9，列表缩略图看到的是那条带。
"""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from PIL import Image, ImageFilter  # noqa: E402

parser = argparse.ArgumentParser(description="截图 -> 公众号封面（缩略图安全）")
parser.add_argument("src", help="界面截图路径")
parser.add_argument("out", help="输出封面路径（1440x810）")
args = parser.parse_args()
SRC, OUT = args.src, args.out
W, H = 1440, 810
THUMB_RATIO = 2.35  # 微信列表缩略图比例（实测）

src = Image.open(SRC).convert("RGB")
band_h_src = int(src.width / THUMB_RATIO)  # 2.35:1 的横带高度（原图坐标）
band = src.crop((0, 0, src.width, band_h_src))

band_h = int(W / THUMB_RATIO)
band = band.resize((W, band_h), Image.Resampling.LANCZOS)

canvas = Image.new("RGB", (W, H), (247, 244, 238))  # 与母版底色一致
canvas.paste(band, (0, (H - band_h) // 2))

# 上下留白处放一条极淡的底色阴影，避免两条白线太生硬
edge = canvas.crop((0, 0, W, (H - band_h) // 2)).filter(ImageFilter.GaussianBlur(6))
canvas.paste(edge, (0, 0))
canvas.paste(edge, (0, H - (H - band_h) // 2))
canvas.save(OUT, quality=92)
print("  缩略图模拟:", str(Path(OUT).with_name("_thumb_preview.jpg")))

# 验：模拟微信缩略图裁切，确认品牌在视野内
crop_h = int(W / THUMB_RATIO)
top = (H - crop_h) // 2
canvas.crop((0, top, W, top + crop_h)).save(
    Path(OUT).with_name("_thumb_preview.jpg"), quality=92
)
print(f"封面: {OUT} {canvas.size}  横带高 {band_h}  （缩略图取中间 {crop_h}px）")
