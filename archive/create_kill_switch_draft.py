"""第八篇原创建为草稿（不群发）"""
import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import os, datetime
from PIL import Image, ImageDraw, ImageFont
from publisher import WeChatPublisher

publisher = WeChatPublisher()

def font(sz):
    for p in ["C:/Windows/Fonts/msyhbd.ttc","C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

today = datetime.date.today().strftime("%Y-%m-%d")

# 封面：紫罗兰暗色 + 停止键/成绩感
W, H = 1440, 810
img = Image.new('RGB', (W, H), (20, 12, 48))
d = ImageDraw.Draw(img)

# 顶部警示条
d.rectangle([0,0,W,8], fill=(124,58,237))

# 巨大停止键符号
d.ellipse([80,90,300,310], fill=(220,38,38))
d.rectangle([150,160,230,240], fill=(255,255,255))

d.text((360, 110), "STOP?", (255,255,255), font(64))
d.text((80, 340), "如果 AI 真的失控了", (255,255,255), font(46))
d.text((80, 415), "有谁按下停止键？", (199,210,254), font(44))

# 成绩卡
d.rounded_rectangle([80, 510, 700, 640], radius=12, fill=(30,18,60), outline=(124,58,237), width=2)
d.text((100, 525), "Guidelight 评级：OpenAI 3/5", (196,181,253), font(20))
d.text((100, 565), "Anthropic / Meta 并列最低", (226,232,240), font(20))

d.rounded_rectangle([720, 510, 1360, 640], radius=12, fill=(30,18,60), outline=(220,38,38), width=2)
d.text((740, 525), "JADEPUFFER：首个全自动勒索", (248,113,113), font(20))
d.text((740, 565), "全程零人类 · 31秒自我纠错", (226,232,240), font(20))

d.text((80, H-60), f"AI前沿观察 · 第八篇 · {today}", (150,150,160), font(18))

img.save("output/cv_kill_switch.jpg", quality=95)
cv = publisher._upload_media("output/cv_kill_switch.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

html = open(f"output/sample_kill_switch_{today}.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="如果AI真的失控了 谁来按下停止键 实验室关停预案缺失",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")