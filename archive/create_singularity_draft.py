"""第四篇原创建为草稿（不群发）"""
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

# 封面：深紫背景 + 奇点主题
W, H = 1440, 810
img = Image.new('RGB', (W, H), (12, 10, 26))
d = ImageDraw.Draw(img)

# 顶部装饰
d.rectangle([0, 0, W, 6], fill=(139, 92, 246))

# 标题
d.text((80, 60), "SINGULARITY?", (139, 92, 246), font(72))
d.text((80, 170), "奥特曼说奇点已到", (255, 255, 255), font(44))
d.text((80, 240), "专家说他可能搞错了", (251, 191, 36), font(44))

# 两个对立观点框
d.text((80, 320), "两种声音", (139, 92, 246), font(28))
d.rounded_rectangle([80, 370, 660, 530], radius=12, fill=(30, 20, 50), outline=(139, 92, 246), width=2)
d.text((100, 385), '"我们现在，就处在奇点之中。"', (139, 92, 246), font(20))
d.text((100, 420), "我这辈子一直在等这一刻。", (200, 200, 210), font(18))
d.text((100, 480), "—— Sam Altman, OpenAI CEO", (148, 163, 184), font(16))

d.rounded_rectangle([700, 370, 1360, 530], radius=12, fill=(30, 20, 50), outline=(248, 113, 113), width=2)
d.text((720, 385), '"我们还没到那一步。"', (248, 113, 113), font(20))
d.text((720, 420), "这需要递归自我改进。", (200, 200, 210), font(18))
d.text((720, 480), "—— Yoshua Bengio, 图灵奖得主", (148, 163, 184), font(16))

# 底部
d.text((80, H - 80), "AI前沿观察  ·  深度原创  ·  2026-08-02", (100, 116, 139), font(18))

img.save("output/cv_singularity.jpg", quality=95)
cv = publisher._upload_media("output/cv_singularity.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

# 读正文
html = open("output/sample_singularity_2026-08-02.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="奥特曼说我们已经进入奇点了但专家说他可能搞错了",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")
