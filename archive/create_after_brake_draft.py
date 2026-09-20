"""第七篇原创建为草稿（不群发）"""
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

# 封面：深蓝+暗红警示，全球联动感
W, H = 1440, 810
img = Image.new('RGB', (W, H), (12, 21, 48))
d = ImageDraw.Draw(img)

# 顶部多色条（美/欧/中 三色呼应）
d.rectangle([0,0,W//3,8], fill=(220,38,38))
d.rectangle([W//3,0,2*W//3,8], fill=(37,99,235))
d.rectangle([2*W//3,0,W,8], fill=(234,179,8))

# 主标题
d.text((80, 90), "刹车之后", (255,255,255), font(72))
d.text((80, 195), "全世界开始紧张", (199,210,254), font(56))

# 副标题
d.text((80, 300), "OpenAI 暂停 Astra 训练，引发连锁反应", (251,191,36), font(30))

# 三块反应卡
cards = [
    (80, 400, "政治", "参议员桑德斯", "呼吁全行业停摆", (220,38,38)),
    (530, 400, "监管", "欧盟·中国", "分级治理已上路", (37,99,235)),
    (980, 400, "现实", "360 周报", "AI 恶意代码入攻击链", (234,179,8)),
]
for x, y, t, big, small, col in cards:
    d.rounded_rectangle([x, y, x+420, y+230], radius=12, fill=(20,30,60), outline=col, width=2)
    d.text((x+24, y+24), t, col, font(26))
    d.text((x+24, y+70), big, (248,250,252), font(28))
    d.text((x+24, y+130), small, (203,213,225), font(20))

d.text((80, H-70), f"AI前沿观察 · 续章 · {today}", (150,150,160), font(18))

img.save("output/cv_after_brake.jpg", quality=95)
cv = publisher._upload_media("output/cv_after_brake.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

html = open(f"output/sample_after_brake_{today}.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="OpenAI踩了刹车后全世界开始紧张 监管与攻击链齐动",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")