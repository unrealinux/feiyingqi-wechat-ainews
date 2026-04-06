#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Daily News Cover Generator
生成AI每日热点速递封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_daily_cover():
    """创建AI每日热点封面"""
    # 创建深色科技风渐变背景
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 新闻/热点主题
    colors = [
        (10, 15, 30),     # 深蓝黑
        (30, 40, 80),     # 深蓝
        (90, 30, 60),     # 深红
    ]
    
    # 绘制渐变
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.5:
            local_t = t / 0.5
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * local_t)
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * local_t)
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * local_t)
        else:
            local_t = (t - 0.5) / 0.5
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * local_t)
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * local_t)
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * local_t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # 绘制新闻/热点相关图形元素
    # 1. 左侧大数字 "140万亿" 突出显示
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(30, 30), (350, 350)],
        radius=20,
        fill=(255, 255, 255, 30)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 2. 绘制上升箭头/趋势线
    points = [(400, 300), (500, 250), (600, 200), (700, 150), (800, 80)]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(255, 100, 100, 200), width=4)
    # 箭头
    draw.polygon([(800, 60), (820, 90), (780, 90)], fill=(255, 100, 100, 200))
    
    # 3. 绘制数据点
    for x, y in points:
        draw.ellipse([(x-8, y-8), (x+8, y+8)], fill=(255, 200, 100, 200))
        draw.ellipse([(x-4, y-4), (x+4, y+4)], fill=(255, 255, 255, 255))
    
    # 4. 绘制新闻图标元素
    # 报纸图标
    draw.rounded_rectangle([(50, 50), (130, 120)], radius=8, fill=(255, 255, 255, 50))
    draw.line([(60, 70), (120, 70)], fill=(255, 255, 255, 150), width=3)
    draw.line([(60, 85), (120, 85)], fill=(255, 255, 255, 150), width=3)
    draw.line([(60, 100), (100, 100)], fill=(255, 255, 255, 150), width=3)
    
    # 5. AI芯片图标
    draw.rounded_rectangle([(180, 50), (250, 120)], radius=8, outline=(100, 200, 255, 200), width=3)
    draw.rectangle([(195, 65), (235, 105)], outline=(100, 200, 255, 200), width=2)
    # 引脚
    for i in range(3):
        y = 70 + i * 15
        draw.line([(180, y), (195, y)], fill=(100, 200, 255, 200), width=2)
        draw.line([(235, y), (250, y)], fill=(100, 200, 255, 200), width=2)
    
    # 尝试加载字体
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/microsoftyahei.ttc",
    ]
    
    font_big = None
    font_title = None
    font_subtitle = None
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_big = ImageFont.truetype(font_path, 48)
                font_title = ImageFont.truetype(font_path, 32)
                font_subtitle = ImageFont.truetype(font_path, 18)
                break
            except:
                continue
    
    if not font_big:
        font_big = ImageFont.load_default()
        font_title = font_big
        font_subtitle = font_big
    
    # 绘制大数字
    draw.text((50, 150), "140万亿", fill=(255, 200, 100, 255), font=font_big)
    draw.text((50, 220), "日均Token调用量", fill=(200, 200, 200, 255), font=font_subtitle)
    
    # 绘制标题
    draw.text((400, 30), "AI行业热点速递", fill=(255, 255, 255, 255), font=font_title)
    draw.text((400, 80), "2026年4月1日", fill=(150, 200, 255, 255), font=font_subtitle)
    
    # 绘制关键词标签
    tags = ["具身智能", "大模型", "AI视频", "产业政策"]
    for i, tag in enumerate(tags):
        x = 400 + i * 120
        y = 130
        draw.rounded_rectangle([(x, y), (x + 100, y + 30)], radius=15, fill=(255, 100, 100, 150))
        draw.text((x + 15, y + 5), tag, fill=(255, 255, 255, 255), font=font_subtitle)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/daily_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_daily_cover()