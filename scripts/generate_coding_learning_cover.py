#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Coding Learning Tools Cover Generator
生成AI编程学习工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_coding_learning_cover():
    """创建AI编程学习工具主题封面"""
    # 创建蓝绿渐变背景（编程/学习主题）
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 编程/学习主题
    colors = [
        (10, 30, 50),      # 深蓝黑
        (20, 60, 80),      # 深蓝
        (30, 100, 90),     # 蓝绿
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
    
    # 绘制编程相关图形元素
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
    
    # 1. 左侧绘制代码符号（< > { } 等）
    code_symbols = [
        (40, 50, "<"),
        (80, 50, ">"),
        (120, 50, "{"),
        (160, 50, "}"),
        (40, 100, "["),
        (80, 100, "]"),
        (120, 100, "("),
        (160, 100, ")"),
    ]
    
    for x, y, symbol in code_symbols:
        if font_big:
            draw.text((x, y), symbol, fill=(255, 255, 255, 150), font=font_big)
    
    # 2. 绘制代码行（模拟代码编辑器）
    lines = [
        (200, 50, 500, "def learn_coding():"),
        (220, 80, 400, "return 'Hello World'"),
        (200, 110, 450, "for i in range(10):"),
        (220, 140, 350, "print(i)"),
        (200, 170, 480, "class AI_Learner:"),
        (220, 200, 420, "def study(self):"),
    ]
    
    for x, y, width, text in lines:
        # 行背景
        draw.rectangle([(x, y), (x+width, y+25)], fill=(255, 255, 255, 30))
        if font_big:
            small_font = ImageFont.truetype(font_paths[0], 14)
            draw.text((x+10, y+3), text, fill=(180, 220, 255, 200), font=small_font)
    
    # 3. 绘制"AI编程"大字
    if font_big:
        big_font = ImageFont.truetype(font_paths[0], 55)
        draw.text((40, 250), "AI编程", fill=(255, 200, 100, 255), font=big_font)
    
    # 4. 绘制右侧工具图标（简化版）
    tools = [
        (600, 50, "C"),   # Cursor
        (650, 50, "G"),   # GitHub Copilot
        (700, 50, "R"),   # Replit
        (600, 120, "Cd"),  # Codecademy
        (650, 120, "Cr"),  # Coursera
        (700, 120, "L"),  # LeetCode
    ]
    
    for x, y, label in tools:
        draw.rounded_rectangle([(x, y), (x+40, y+40)], radius=8, fill=(255, 255, 255, 50))
        if font_big:
            small_font = ImageFont.truetype(font_paths[0], 18)
            draw.text((x+8, y+8), label, fill=(255, 255, 255, 255), font=small_font)
    
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
        
        draw.text((50, 280), "2026 AI编程学习工具横评", fill=(255, 255, 255, 255), font=title_font)
        draw.text((50, 325), "Cursor vs GitHub Copilot vs Replit vs Codecademy", fill=(180, 220, 255, 255), font=subtitle_font)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/coding_learning_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_coding_learning_cover()