"""用 v2 内容替换旧草稿"""
import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import os
from publisher import WeChatPublisher

publisher = WeChatPublisher()

# 1. 列出当前草稿，找到旧的那篇
drafts = publisher.list_drafts()
old_id = None
for d in drafts:
    if "AI逃出实验室" in d.get("title", ""):
        old_id = d["media_id"]
        break

if old_id:
    print("找到旧草稿，media_id:", old_id)
    ok = publisher.delete_draft(old_id)
    print("已删除旧草稿" if ok else "删除失败")
else:
    print("未找到旧草稿，直接创建新的")

# 2. 读 v2 正文
html = open("output/sample_rogue_agent_v2_2026-07-23.html", encoding="utf-8").read()

# 3. 重新生成封面（用新设计）
import PIL.Image as Image, PIL.ImageDraw as Draw, PIL.ImageFont as Font

def font(sz):
    for p in ["C:/Windows/Fonts/msyhbd.ttc","C:/Windows/Fonts/msyh.ttc","C:/Windows/Fonts/simhei.ttf"]:
        if os.path.exists(p): return Font.truetype(p, sz)
    return Font.load_default()

W, H = 1440, 810
img = Image.new('RGB', (W, H), (15, 8, 8))
Draw.Draw(img).rectangle([0, 200, W, 280], fill=(220, 50, 40))
d = Draw.Draw(img)
d.text((80, 80), "AI ESCAPED", (240, 60, 50), font(72))
d.text((80, 290), "逃出实验室的 AI", (255, 255, 255), font(44))
d.text((80, 370), "攻击了另一家公司", (255, 200, 80), font(44))
d.text((80, 480), "原创评论 · OpenAI 承认 · 2026-07-22", (180, 180, 190), font(22))
d.text((80, H - 70), "AI前沿观察", (130, 130, 145), font(20))
img.save("output/cv_rogue_agent_v2.jpg", quality=95)
cv = publisher._upload_media("output/cv_rogue_agent_v2.jpg", "image")
print("封面:", "OK" if cv else "FAILED")

# 4. 创建新草稿（不群发）
did = publisher.create_draft(
    title="AI逃出实验室攻击了另一家公司: OpenAI刚承认",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("新草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")
