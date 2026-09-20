"""给三张生成图加上可读的中文文字"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont
import os

def find_font(size):
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc",  # 微软雅黑加粗
        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttf",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

FONT_BIG = find_font(60)
FONT_MID = find_font(36)
FONT_SM = find_font(24)
FONT_XS = find_font(18)

# === 封面图 ===
if os.path.exists("output/ai-review-cover.png"):
    img = Image.open("output/ai-review-cover.png").convert('RGBA')
    w, h = img.size
    # 半透明黑底
    overlay = Image.new('RGBA', (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    # 顶部标题区域
    draw.rectangle([(0,0), (w, 160)], fill=(0,0,0,180))
    draw.text((50, 30), "2026年5月AI大模型横评", fill=(255,255,255), font=FONT_BIG)
    draw.text((50, 105), "5款新品深度对比与选型指南", fill=(200,210,255), font=FONT_MID)

    # 底部标签
    draw.rectangle([(0,h-90), (w, h)], fill=(0,0,0,180))
    products = "蚂蚁百灵Ring · 文心5.1 · OpenAI实时语音 · GPT-5.5 · 讯飞星火"
    draw.text((50, h-68), products, fill=(180,200,255), font=FONT_SM)

    # 品牌标记
    draw.text((w-200, h-60), "2026.05", fill=(100,150,255), font=FONT_XS)

    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    img.save("output/ai-review-cover-text.png", quality=92)
    print("[OK] ai-review-cover-text.png")

# === 对比表格图 ===
if os.path.exists("output/ai-review-table.png"):
    img = Image.open("output/ai-review-table.png").convert('RGBA')
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    draw.rectangle([(0,0), (w, 90)], fill=(0,20,80,200))
    draw.text((40, 18), "产品横向对比", fill=(255,255,255), font=FONT_BIG)
    draw.text((40, 70), "5月新品核心参数一览", fill=(150,200,255), font=FONT_XS)

    # 表格行1
    row_data = [
        ("蚂蚁百灵Ring", "蚂蚁集团", "万亿参数·可调推理", "限时免费"),
        ("文心5.1", "百度", "训练成本降94%·效价比", "待定"),
        ("GPT-Realtime-2", "OpenAI", "GPT-5级实时语音", "$32/M"),
        ("GPT-5.5 Instant", "OpenAI", "幻觉降52.5%", "已上线"),
        ("讯飞星火党政", "科大讯飞", "Agent·端云协同", "面议"),
    ]
    row_h = (h - 200) // 5
    col_w = (w - 60) // 4
    col_starts = [30, 30+col_w, 30+col_w*2, 30+col_w*3]
    color_bar = Image.new('RGBA', (w, h), (0,0,0,0))
    cdraw = ImageDraw.Draw(color_bar)
    for ri, (p, m, f, pr) in enumerate(row_data):
        y = 190 + ri * row_h
        bg = (0, 60, 150, 160) if ri % 2 == 0 else (0, 40, 100, 140)
        cdraw.rectangle([(30, y), (w-30, y+row_h-5)], fill=bg)
        cdraw.text((40, y+8), p, fill=(255,255,255), font=FONT_MID)
        cdraw.text((col_starts[1]+10, y+12), m, fill=(180,220,255), font=FONT_XS)
        cdraw.text((col_starts[2]+10, y+12), f, fill=(200,230,255), font=FONT_XS)
        cdraw.text((col_starts[3]+10, y+12), pr, fill=(255,200,100), font=FONT_SM)
    img = Image.alpha_composite(img, color_bar)
    img = img.convert('RGB')
    img.save("output/ai-review-table-text.png", quality=92)
    print("[OK] ai-review-table-text.png")

# === 指南图 ===
if os.path.exists("output/ai-review-guide.png"):
    img = Image.open("output/ai-review-guide.png").convert('RGBA')
    w, h = img.size
    overlay = Image.new('RGBA', (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    draw.rectangle([(0,0), (w, 90)], fill=(0,80,60,200))
    draw.text((40, 18), "选型建议（场景对照表）", fill=(255,255,255), font=FONT_BIG)

    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    img.save("output/ai-review-guide-text.png", quality=92)
    print("[OK] ai-review-guide-text.png")

print("\n全部完成！新文件:")
for f in ["ai-review-cover-text.png", "ai-review-table-text.png", "ai-review-guide-text.png"]:
    p = f"output/{f}"
    if os.path.exists(p):
        print(f"  {p} ({os.path.getsize(p)//1024}KB)")