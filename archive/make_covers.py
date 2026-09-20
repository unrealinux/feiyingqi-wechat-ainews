"""生成简单矢量风格封面并更新草稿"""
import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont
import os, io
from publisher import WeChatPublisher

publisher = WeChatPublisher()

def find_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttf" if bold else "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def make_vector_cover(title, subtitle, tags, bg_color, accent_color):
    """生成矢量风格封面图"""
    W, H = 1920, 1080
    img = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # 几何装饰 - 半透明圆形
    for cx, cy, r, color in [
        (1600, -100, 500, accent_color + '20'),
        (-100, 900, 400, accent_color + '15'),
        (1400, 600, 200, accent_color + '10'),
        (300, -50, 150, accent_color + '18'),
    ]:
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d = ImageDraw.Draw(overlay)
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

    # 底部色条
    draw.rectangle([(0, H-100), (W, H)], fill=accent_color + '40')

    # 标题
    font_big = find_font(72, bold=True)
    font_mid = find_font(36, bold=False)
    font_sm = find_font(22, bold=False)
    font_xs = find_font(18, bold=False)

    # 主标题
    text_color = (255, 255, 255)
    draw.text((80, 180), title, fill=text_color, font=font_big)

    # 副标题
    draw.text((80, 280), subtitle, fill=(200, 210, 255), font=font_mid)

    # 标签
    y = 400
    for tag in tags:
        tx, ty = 80, y
        tag_bg = accent_color + '60'
        overlay = Image.new('RGBA', (W, H), (0,0,0,0))
        d = ImageDraw.Draw(overlay)
        tw = font_sm.getlength(tag) + 30
        d.rounded_rectangle([tx, ty, tx+tw, ty+40], 20, fill=tag_bg)
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        draw.text((tx+15, ty+8), tag, fill=text_color, font=font_sm)
        y += 50

    # 底部日期
    draw.text((80, H-70), "AI前沿观察 · 2026年5月", fill=(180, 190, 220), font=font_xs)

    # 右侧装饰文字
    draw.text((W-250, H-70), "AI REVIEW", fill=(100, 120, 180, 100), font=font_xs)

    return img

# 文章封面配置
articles = [
    {
        "id": "1-main",
        "title": "2026年5月AI大模型横评",
        "subtitle": "Ring·文心5.1·GPT-Realtime·GPT-5.5·星火",
        "tags": ["蚂蚁百灵Ring", "百度文心5.1", "OpenAI实时语音", "GPT-5.5", "讯飞星火"],
        "bg": "#1a1a2e",
        "accent": "#16213e",
        "draft_id": "tonl23VyVW4yxD9x9eRoGj2ketWKl1q3SfbxZuzvEcEZezu4QjZCmtNb9G-dJaW2"
    },
    {
        "id": "2-video",
        "title": "AI视频生成模型横评",
        "subtitle": "Sora 2 · Veo 3.1 · Kling 3.0 · Seedance 2.0",
        "tags": ["Sora 2 - 物理真实感", "Veo 3.1 - 企业级", "Kling 3.0 - 极致性价比", "Seedance 2.0 - 最强控制"],
        "bg": "#0f1729",
        "accent": "#1e3a5f",
        "draft_id": "tonl23VyVW4yxD9x9eRoGlaVndWdvKxsSl98jFdMHw4vEgxUncobUYyUpcYgixkH"
    },
    {
        "id": "3-code",
        "title": "AI编程工具终极对比",
        "subtitle": "Claude · GPT · DeepSeek · Kimi · GLM",
        "tags": ["Kimi K2.5 SWE-Bench 65.6%", "Claude Opus 4.6 架构设计", "GPT-5.4 均衡全面", "DeepSeek V4 极致成本"],
        "bg": "#1a1a2e",
        "accent": "#4a1a3a",
        "draft_id": "tonl23VyVW4yxD9x9eRoGjafg6GmNPtWrgMYqNqLx1qhAUKyErfo2mvsZkvNWopN"
    },
    {
        "id": "4-os",
        "title": "开源大模型选型指南",
        "subtitle": "Qwen 3.5 · GLM-5 · DeepSeek V4 · Llama 4",
        "tags": ["Qwen 3.5 - 中文最强", "GLM-5 - 国产合规", "DeepSeek V4 - 极致性价比", "Llama 4 - 全球社区"],
        "bg": "#0a1a0e",
        "accent": "#1a3a2a",
        "draft_id": "tonl23VyVW4yxD9x9eRoGmZ7yUjs6krWj8vGhidFXUh529z0qlmlpC9pRRV4f7Yw"
    }
]

for art in articles:
    print(f"[{art['id']}] {art['title']}")
    # 生成封面图
    img = make_vector_cover(art['title'], art['subtitle'], art['tags'], art['bg'], art['accent'])
    # 保存
    out_jpg = f"output/cover_{art['id']}.jpg"
    img.save(out_jpg, quality=92)
    size_kb = os.path.getsize(out_jpg) // 1024
    print(f"  生成: {out_jpg} ({size_kb}KB)")
    
    # 上传到微信
    mid = publisher._upload_media(out_jpg, "image")
    if mid:
        print(f"  上传: {mid}")
        # 草稿箱 - 微信API不支持更新草稿封面，需要删除重建
        # 这里就不重建了，但封面已上传到素材库
    else:
        print(f"  上传失败")

print(f"\n完成！新封面已输出到 output/cover_*.jpg")
print(f"登录微信公众平台 -> 素材库 可看到上传的封面")
print(f"在草稿箱中手动替换封面即可")