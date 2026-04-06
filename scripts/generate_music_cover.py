#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Music Tools Cover Generator
生成AI音乐生成工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math
import random

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_music_cover():
    """创建AI音乐工具主题封面"""
    # 创建深色渐变背景（音乐/节奏主题）
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 音乐/节奏主题
    colors = [
        (20, 10, 40),      # 深紫黑
        (60, 20, 80),      # 深紫
        (100, 40, 60),     # 紫红
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
    
    # 绘制音乐相关图形元素
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
    
    # 1. 绘制音频波形（左侧）
    for i in range(30):
        x = 30 + i * 12
        # 模拟音频波形
        h = 20 + abs(math.sin(i * 0.3) * 60) + random.randint(5, 20)
        y_center = HEIGHT // 2 - 20
        color_val = int(150 + math.sin(i * 0.5) * 100)
        draw.rounded_rectangle(
            [(x, y_center - h//2), (x + 6, y_center + h//2)],
            radius=3,
            fill=(color_val, 100, 255, 200)
        )
    
    # 2. 绘制音符符号
    if font_big:
        music_font = ImageFont.truetype(font_paths[0], 60)
        draw.text((400, 40), "🎵", fill=(255, 200, 100, 255), font=music_font)
        draw.text((500, 40), "🎶", fill=(255, 150, 150, 255), font=music_font)
        draw.text((600, 40), "🎸", fill=(150, 255, 200, 255), font=music_font)
        draw.text((700, 40), "🎹", fill=(150, 200, 255, 255), font=music_font)
    
    # 3. 绘制五线谱线条
    for i in range(5):
        y = 150 + i * 15
        draw.line([(400, y), (850, y)], fill=(255, 255, 255, 60), width=1)
    
    # 4. 绘制"AI Music"大字
    if font_big:
        big_font = ImageFont.truetype(font_paths[0], 50)
        draw.text((420, 180), "AI Music", fill=(255, 200, 100, 255), font=big_font)
    
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
        
        draw.text((50, 280), "2026 AI音乐生成工具横评", fill=(255, 255, 255, 255), font=title_font)
        draw.text((50, 325), "Suno vs Udio vs 网易天音 vs 腾讯XMusic", fill=(200, 180, 255, 255), font=subtitle_font)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/music_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_music_cover()