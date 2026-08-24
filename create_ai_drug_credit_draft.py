"""将 AI 药物署名权原创文建为草稿（不群发，AGENTS 规范允许 create_draft）"""
import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import os, datetime
from publisher import WeChatPublisher

publisher = WeChatPublisher()

# 封面已生成 output/cv_ai_drug_credit.jpg
cv_path = "output/cv_ai_drug_credit.jpg"
if not os.path.exists(cv_path):
    print("封面缺失:", cv_path)
    sys.exit(1)
cv = publisher._upload_media(cv_path, "image")
print("封面上传:", "OK" if cv else "FAILED")

# 读正文
html = open("output/sample_ai_drug_credit_2026-08-24.html", encoding="utf-8").read()

did = publisher.create_draft(
    title="AI设计出能救命的药，功劳算谁的？",
    content=html,
    author="AI前沿观察",
    cover_media_id=cv or ""
)
print("草稿 media_id:", did)
print("已建草稿（未群发）。" if did else "草稿创建失败")
