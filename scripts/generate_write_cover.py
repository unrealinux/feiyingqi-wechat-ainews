#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Writing Tools Cover Generator
生成AI写作工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_write_cover():
    """创建AI写作工具主题封面"""
    # 创建暖色渐变背景（写作/创作主题）
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 写作/创作主题（暖色调）
    colors = [
        (40, 20, 50),      # 深紫
        (80, 40, 80),      # 紫
        (120, 60, 100),    # 粉紫
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
    
    # 绘制写作相关图形元素
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
    
    # 1. 左侧写作图标（羽毛笔/文档）
    draw.rounded_rectangle([(30, 30), (180, 200)], radius=15, fill=(255, 255, 255, 50))
    # 画羽毛笔形状
    if font_big:
        draw.text((50, 50), "✍️", fill=(255, 255, 255, 255), font=font_big)
    
    # 2. 绘制文字输入行
    lines = [
        (220, 50, 700, "在山的那边，是海吗？", (200, 200, 200)),
        (220, 90, 600, "是用信念凝成的海", (150, 150, 150)),
        (220, 130, 500, "今天啊，我竟听到", (200, 200, 200)),
        (220, 170, 550, "海在远方喧响", (150, 150, 150)),
    ]
    
    for x, y, width, text, color in lines:
        draw.line([(x, y), (x+width, y)], fill=color, width=3)
    
    # 3. 绘制"AI写作"大字
    if font_big:
        big_font = ImageFont.truetype(font_paths[0], 55)
        draw.text((40, 250), "AI写作", fill=(255, 200, 100, 255), font=big_font)
    
    # 4. 绘制标题区域背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(30, 270), (870, 370)],
        radius=15,
        fill=(0, 0, 0, 100)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 5. 绘制标题文字
    if font_big:
        title_font = ImageFont.truetype(font_paths[0], 32)
        subtitle_font = ImageFont.truetype(font_paths[0], 18)
        
        draw.text((50, 280), "2026 AI写作工具横评", fill=(255, 255, 255, 255), font=title_font)
        draw.text((50, 325), "ChatGPT vs Claude vs Kimi vs 秘塔 vs 讯飞 vs 字节", fill=(200, 180, 220, 255), font=subtitle_font)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/write_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_write_cover()