"""第六篇原创建为草稿（不群发）"""
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

# 封面：红色警示系 + 暂停主题
W, H = 1440, 810
img = Image.new('RGB', (W, H), (26, 8, 8))
d = ImageDraw.Draw(img)

# 顶部警示条
d.rectangle([0, 0, W, 8], fill=(220, 38, 38))

# 暂停符号
d.rectangle([80, 70, 200, 240], fill=(220, 38, 38))
d.rectangle([230, 70, 350, 240], fill=(220, 38, 38))

# 标题
d.text((420, 80), "PAUSE", (239, 68, 68), font(72))
d.text((80, 280), "AI 开始让创造它的人害怕了", (255, 255, 255), font(46))

# 副标题
d.text((80, 360), "OpenAI 历史上第一次按下暂停键", (251, 191, 36), font(38))
d.text((80, 430), "Astra 模型训练停摆 · 全球股市震动", (203, 213, 225), font(24))

# 关键信息卡
d.rounded_rectangle([80, 510, 700, 640], radius=12, fill=(40, 12, 12), outline=(220, 38, 38), width=2)
d.text((100, 525), "8/7 判定关键级安全阈值", (248, 113, 113), font(20))
d.text((100, 565), "30分钟警报 · 20%算力监控", (226, 232, 240), font(20))

d.rounded_rectangle([720, 510, 1360, 640], radius=12, fill=(40, 12, 12), outline=(234, 179, 8), width=2)
d.text((740, 525), "Astra 8月发布概率降至 13%", (251, 191, 36), font(20))
d.text((740, 565), "Polymarket 预测市场数据", (226, 232, 240), font(20))

# 底部信息
d.text((80, H - 70), "AI前沿观察  ·  本周热点  ·  2026-08-20", (150, 150, 160), font(18))

img.save("output/cv_openai_pause.jpg", quality=95)
cv = publisher._upload_media("output/cv_openai_pause.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

# 读正文
html = open("output/sample_openai_pause_2026-08-20.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="AI开始让创造它的人害怕了 OpenAI首次按下暂停键",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")