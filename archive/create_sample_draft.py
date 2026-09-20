"""将 WAIC 2026 示范文建为草稿（不群发）"""
import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import os, datetime
from PIL import Image, ImageDraw, ImageFont
from publisher import WeChatPublisher

publisher = WeChatPublisher()

# --- 封面（原创设计，不用 pil 渐变模板套路）---
def font(sz):
    for p in ["C:/Windows/Fonts/msyhbd.ttc","C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

W, H = 1440, 810
img = Image.new('RGB', (W, H), (12, 16, 28))
# 简单两色块区分"两套规则"
ImageDraw.Draw(img).rectangle([0,0,W//2,H], fill=(30, 58, 138))   # 蓝：一套
ImageDraw.Draw(img).rectangle([W//2,0,W,H], fill=(153, 27, 27))    # 红：另一套
ImageDraw.Draw(img).rectangle([W//2-3,0,W//2+3,H], fill=(240,240,240))
d = ImageDraw.Draw(img)
d.text((80, 120), "WAIC 2026", (255,255,255), font(72))
d.text((80, 230), "当世界开始有", (235,238,245), font(40))
d.text((80, 300), "两套 AI 规则", (245,205,90), font(52))
d.text((80, 430), "原创评论 · 真实事件 · 带来源", (200,210,230), font(24))
d.text((80, H-70), "AI前沿观察", (150,160,185), font(20))
img.save("output/cv_waic2026.jpg", quality=95)
cv = publisher._upload_media("output/cv_waic2026.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

# --- 正文 ---
html = open("output/sample_waic2026_2026-07-20.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="WAIC 2026 落幕：当世界开始有两套 AI 规则",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")
