"""第五篇原创建为草稿（不群发）"""
import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import os
from PIL import Image, ImageDraw, ImageFont
from publisher import WeChatPublisher

publisher = WeChatPublisher()

def font(sz):
    for p in ["C:/Windows/Fonts/msyhbd.ttc","C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

# 封面：青蓝对比风格
W, H = 1440, 810
img = Image.new('RGB', (W, H), (15, 23, 42))
d = ImageDraw.Draw(img)

# 顶部装饰
d.rectangle([0, 0, W, 6], fill=(34, 211, 238))

# 主标题
d.text((80, 60), "HARNESS", (34, 211, 238), font(76))
d.text((80, 150), "DeepSeek Harness  vs  Pi", (255, 255, 255), font(44))

# 两个阵营框
d.rounded_rectangle([80, 260, 690, 430], radius=12, fill=(30, 41, 59), outline=(99, 102, 241), width=2)
d.text((100, 275), "一切皆插件", (129, 140, 248), font(30))
d.text((100, 330), "官方 · 刚发布", (203, 213, 225), font(22))
d.text((100, 365), "模型 + Harness 协同", (148, 163, 184), font(18))

d.rounded_rectangle([750, 260, 1360, 430], radius=12, fill=(30, 41, 59), outline=(20, 184, 166), width=2)
d.text((770, 275), "极简 · 200 token", (45, 212, 191), font(30))
d.text((770, 330), "社区老炮 · 实测第一", (203, 213, 225), font(22))
d.text((770, 365), "四个核心工具 read/write/edit/bash", (148, 163, 184), font(18))

# 副标题
d.text((80, 480), "同一个公式 Model+Harness=Agent", (203, 213, 225), font(24))
d.text((80, 520), "两条完全相反的工程路线", (203, 213, 225), font(24))

# 底部信息
d.text((80, H - 80), "AI前沿观察  ·  技术评测  ·  2026-08-15", (100, 116, 139), font(18))

img.save("output/cv_harness_pi.jpg", quality=95)
cv = publisher._upload_media("output/cv_harness_pi.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

# 读正文
html = open("output/sample_harness_vs_pi_2026-08-15.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="DeepSeek Harness vs Pi：同一个公式两条相反的路线",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")
