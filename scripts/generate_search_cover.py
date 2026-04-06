#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Search Tools Cover Generator
生成AI搜索工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os
import random

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_search_cover():
    """创建AI搜索工具主题封面"""
    # 创建蓝紫渐变背景
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 搜索/信息主题
    colors = [
        (20, 30, 60),     # 深蓝
        (40, 60, 120),    # 中蓝
        (80, 40, 140),    # 紫
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
    
    # 绘制搜索相关图形元素
    # 1. 左侧大搜索图标
    draw.ellipse([(60, 60), (220, 220)], outline=(255, 255, 255, 200), width=8)
    draw.line([(180, 180), (240, 240)], fill=(255, 255, 255, 200), width=12)
    
    # 2. 搜索框内的文字线条
    draw.rounded_rectangle([(70, 70), (210, 210)], radius=70, fill=(255, 255, 255, 50))
    draw.line([(90, 120), (190, 120)], fill=(255, 255, 255, 150), width=4)
    draw.line([(90, 145), (170, 145)], fill=(255, 255, 255, 150), width=4)
    draw.line([(90, 170), (150, 170)], fill=(255, 255, 255, 150), width=4)
    
    # 3. 右侧信息流/搜索结果卡片
    for i in range(4):
        y = 40 + i * 85
        draw.rounded_rectangle([(400, y), (860, y+70)], radius=10, fill=(255, 255, 255, 40))
        draw.rounded_rectangle([(420, y+10), (460, y+50)], radius=5, fill=(100, 150, 255, 150))
        draw.line([(480, y+20), (750, y+20)], fill=(255, 255, 255, 150), width=4)
        draw.line([(480, y+40), (650, y+40)], fill=(200, 200, 200, 100), width=3)
    
    # 4. 绘制"AI"大文字
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    
    font_big = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_big = ImageFont.truetype(font_path, 80)
                break
            except:
                continue
    
    if font_big:
        draw.text((60, 250), "AI", fill=(100, 200, 255, 200), font=font_big)
    
    # 5. 绘制标题区域背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(30, 260), (870, 370)],
        radius=15,
        fill=(0, 0, 0, 120)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 6. 绘制标题文字
    if font_big:
        title_font = ImageFont.truetype(font_paths[0], 36)
        subtitle_font = ImageFont.truetype(font_paths[0], 20)
        
        draw.text((50, 270), "2026 AI搜索工具横评", fill=(255, 255, 255, 255), font=title_font)
        draw.text((50, 320), "Perplexity vs Kimi vs 秘塔 vs 天工 vs 360", fill=(180, 200, 255, 255), font=subtitle_font)
    
    # 7. 添加装饰小元素（数据点/连线）
    for _ in range(20):
        x = random.randint(300, 850)
        y = random.randint(20, 300)
        size = random.randint(2, 5)
        draw.ellipse([(x, y), (x+size, y+size)], fill=(150, 180, 255, 100))
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/search_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_search_cover()