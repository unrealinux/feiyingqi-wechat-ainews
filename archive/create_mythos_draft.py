"""第三篇原创建为草稿（不群发）"""
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

# 封面：深蓝背景 + 蓝色数据卡片风格
W, H = 1440, 810
img = Image.new('RGB', (W, H), (15, 23, 42))
d = ImageDraw.Draw(img)

# 顶部装饰条
d.rectangle([0, 0, W, 6], fill=(59, 130, 246))

# 标题区
d.text((80, 60), "AI PATCH SPEED", (59, 130, 246), font(64))
d.text((80, 150), "找漏洞 vs 修漏洞", (255, 255, 255), font(48))

# 数据卡片
def card(x, y, num, label, color):
    d.rounded_rectangle([x, y, x+280, y+140], radius=12, fill=(30, 41, 59), outline=color, width=2)
    d.text((x+20, y+15), num, color, font(48))
    d.text((x+20, y+85), label, (148, 163, 184), font(16))

card(80, 280, "90", "critical / 4月", (239, 68, 68))
card(400, 280, "600+", "Patch 7月", (234, 179, 8))
card(720, 280, "300+", "待修补", (124, 58, 237))
card(1040, 280, "50", "微软员工", (6, 182, 212))

# 副标题
d.text((80, 460), "ProPublica 调查：微软工程师正在\"疯狂冲刺\"", (203, 213, 225), font(22))
d.text((80, 500), "但漏洞被发现的速度，已经超过修补的速度", (203, 213, 225), font(22))

# 底部信息
d.text((80, H - 80), "AI前沿观察  ·  深度原创  ·  2026-07-30", (100, 116, 139), font(18))

img.save("output/cv_mythos_msft.jpg", quality=95)
cv = publisher._upload_media("output/cv_mythos_msft.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

# 读正文
html = open("output/sample_mythos_vs_msft_2026-07-30.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="AI找漏洞的速度已经超过人类修补的速度",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")
