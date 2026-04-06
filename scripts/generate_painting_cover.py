#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Painting Tools Cover Generator
生成AI绘画设计工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math
import random

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_painting_cover():
    """创建AI绘画设计工具主题封面"""
    # 创建多彩渐变背景（绘画/艺术主题）
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 绘画/艺术主题（多彩）
    colors = [
        (30, 20, 60),      # 深紫
        (80, 30, 100),     # 紫
        (120, 60, 80),     # 粉紫
        (40, 80, 120),     # 蓝
    ]
    
    # 绘制渐变
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.33:
            local_t = t / 0.33
            r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * local_t)
            g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * local_t)
            b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * local_t)
        elif t < 0.66:
            local_t = (t - 0.33) / 0.33
            r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * local_t)
            g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * local_t)
            b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * local_t)
        else:
            local_t = (t - 0.66) / 0.34
            r = int(colors[2][0] + (colors[3][0] - colors[2][0]) * local_t)
            g = int(colors[2][1] + (colors[3][1] - colors[2][1]) * local_t)
            b = int(colors[2][2] + (colors[3][2] - colors[2][2]) * local_t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # 绘制绘画相关图形元素
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    
    font_big = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_big = ImageFont.truetype(font_path, 50)
                break
            except:
                continue
    
    # 1. 绘制调色板
    palette_colors = [
        (255, 100, 100),   # 红
        (255, 200, 100),   # 橙
        (255, 255, 100),   # 黄
        (100, 255, 100),   # 绿
        (100, 200, 255),   # 蓝
        (200, 100, 255),   # 紫
    ]
    
    for i, color in enumerate(palette_colors):
        x = 40 + i * 50
        y = 60
        draw.ellipse([(x, y), (x+40, y+40)], fill=color + (255,))
    
    # 2. 绘制画笔符号
    if font_big:
        draw.text((200, 50), "🎨", fill=(255, 255, 255, 255), font=font_big)
    
    # 3. 绘制彩色斑块（模拟颜料）
    blob_positions = [
        (350, 80, 60, (255, 100, 150)),
        (420, 120, 50, (100, 200, 255)),
        (500, 60, 55, (255, 200, 100)),
        (380, 150, 45, (150, 255, 150)),
    ]
    
    for x, y, size, color in blob_positions:
        draw.ellipse([(x, y), (x+size, y+size)], fill=color + (150,))
    
    # 4. 绘制"AI绘画"大字
    if font_big:
        big_font = ImageFont.truetype(font_paths[0], 50)
        draw.text((550, 80), "AI绘画", fill=(255, 200, 100, 255), font=big_font)
    
    # 5. 绘制标题区域背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(30, 270), (870, 370)],
        radius=15,
        fill=(0, 0, 0, 120)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 6. 绘制标题文字
    if font_big:
        title_font = ImageFont.truetype(font_paths[0], 32)
        subtitle_font = ImageFont.truetype(font_paths[0], 18)
        
        draw.text((50, 280), "2026 AI绘画设计工具横评", fill=(255, 255, 255, 255), font=title_font)
        draw.text((50, 325), "Midjourney vs DALL-E vs Stable Diffusion vs Flux", fill=(200, 180, 255, 255), font=subtitle_font)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/painting_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_painting_cover()