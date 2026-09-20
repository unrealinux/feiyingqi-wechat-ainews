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

# 封面：深青渐变+琥珀高亮，与文章配色一致（区别于第七篇深蓝+暗红）
W, H = 1440, 810
img = Image.new('RGB', (W, H), (4, 47, 46))
d = ImageDraw.Draw(img)

# 顶部刻度条（表示漏洞扫描进度）
d.rectangle([0,0,W,10], fill=(16,185,129))
d.rectangle([0,0,int(W*0.845),10], fill=(245,158,11))

# 主标题
d.text((80, 90), "它找到了2436个漏洞", (255,255,255), font(76))
d.text((80, 200), "然后决定先不发", (255,255,255), font(56))

# 副标题
d.text((80, 310), "GLM-5.3 追平前沿攻击能力，Z.ai 主动暂扣权重", (245,158,11), font(30))

# 三块数据卡
cards = [
    (80, 420, "84.5%", "CyberGym 自主漏洞发现", "超过 Mythos 5 (83.8%)"),
    (530, 420, "2436", "269 个开源项目中的漏洞", "约半数中高危"),
    (980, 420, "40年", "最老漏洞所在代码年龄", "被今天的模型翻出"),
]
for x, y, big, mid, small in cards:
    d.rounded_rectangle([x, y, x+420, y+240], radius=12, fill=(6,78,59), outline=(16,185,129), width=2)
    d.text((x+24, y+24), big, (245,158,11), font(52))
    d.text((x+24, y+110), mid, (255,255,255), font(26))
    d.text((x+24, y+165), small, (209,250,229), font(20))

d.text((80, H-70), f"AI前沿观察 · 第八篇 · {today}", (110,140,135), font(18))

img.save("output/cv_glm53.jpg", quality=95)
cv = publisher._upload_media("output/cv_glm53.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

html = open(f"output/sample_glm53_{today}.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="它找到了2436个漏洞，然后决定先不发",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")
