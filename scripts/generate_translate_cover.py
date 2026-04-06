#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Translation Tools Cover Generator
生成AI翻译工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os
import random

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_translate_cover():
    """创建AI翻译工具主题封面"""
    # 创建蓝绿渐变背景（翻译/沟通主题）
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 翻译/沟通主题
    colors = [
        (10, 40, 60),     # 深蓝
        (20, 80, 80),     # 蓝绿
        (40, 120, 60),    # 绿
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
    
    # 绘制翻译相关图形元素
    # 1. 左侧"A→B"翻译符号
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    
    font_big = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_big = ImageFont.truetype(font_path, 60)
                break
            except:
                continue
    
    # 绘制翻译符号
    draw.rounded_rectangle([(40, 40), (300, 160)], radius=20, fill=(255, 255, 255, 60))
    if font_big:
        draw.text((60, 55), "中文 → English", fill=(255, 255, 255, 255), font=font_big)
    
    # 2. 绘制语言气泡
    bubbles = [
        (350, 50, "你好", (255, 100, 100)),
        (550, 50, "Hello", (100, 200, 255)),
        (350, 130, "こんにちは", (100, 255, 150)),
        (550, 130, "Bonjour", (255, 200, 100)),
    ]
    
    for x, y, text, color in bubbles:
        draw.rounded_rectangle([(x, y), (x+150, y+60)], radius=15, fill=color + (150,))
        if font_big:
            small_font = ImageFont.truetype(font_paths[0], 24)
            draw.text((x+20, y+15), text, fill=(255, 255, 255, 255), font=small_font)
    
    # 3. 绘制翻译箭头
    draw.polygon([(200, 200), (220, 180), (220, 220)], fill=(255, 255, 255, 200))
    draw.polygon([(280, 200), (300, 180), (300, 220)], fill=(255, 255, 255, 200))
    draw.rectangle([(210, 190), (290, 210)], fill=(255, 255, 255, 200))
    
    # 4. 绘制"6大工具"标签
    if font_big:
        label_font = ImageFont.truetype(font_paths[0], 40)
        draw.text((40, 240), "6大翻译工具", fill=(255, 200, 100, 255), font=label_font)
    
    # 5. 绘制标题区域背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(30, 280), (870, 370)],
        radius=15,
        fill=(0, 0, 0, 120)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 6. 绘制标题文字
    if font_big:
        title_font = ImageFont.truetype(font_paths[0], 32)
        subtitle_font = ImageFont.truetype(font_paths[0], 20)
        
        draw.text((50, 290), "2026 AI翻译工具横评", fill=(255, 255, 255, 255), font=title_font)
        draw.text((50, 335), "DeepL vs Google vs 讯飞 vs 腾讯 vs ChatGPT vs 百度", fill=(180, 220, 255, 255), font=subtitle_font)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/translate_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_translate_cover()