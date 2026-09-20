#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Data Analysis Tools Cover Generator
生成AI数据分析工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_data_analysis_cover():
    """创建AI数据分析工具主题封面"""
    # 创建蓝绿渐变背景（数据/分析主题）
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 数据/分析主题
    colors = [
        (10, 30, 40),      # 深蓝黑
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
    
    # 绘制数据相关图形元素
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
    
    # 1. 左侧绘制数据图表（模拟柱状图）
    bar_data = [100, 180, 120, 200, 150, 90]
    bar_width = 40
    x_start = 40
    for i, height in enumerate(bar_data):
        x = x_start + i * (bar_width + 20)
        y_top = 300 - height
        # 渐变色柱状图
        color_val = int(100 + i * 25)
        draw.rectangle(
            [(x, y_top), (x + bar_width, 300)],
            fill=(color_val, 150, 255 - i * 20)
        )
    
    # 2. 绘制折线图（模拟趋势）
    points = [(250, 250), (320, 200), (390, 220), (460, 180), (530, 150)]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(255, 200, 100), width=4)
    # 数据点
    for x, y in points:
        draw.ellipse([(x-5, y-5), (x+5, y+5)], fill=(255, 255, 255))
    
    # 3. 绘制"AI数据分析"大字
    if font_big:
        big_font = ImageFont.truetype(font_paths[0], 55)
        draw.text((40, 50), "AI数据分析", fill=(255, 200, 100, 255), font=big_font)
    
    # 4. 绘制右侧工具图标（简化版）
    tools = [
        (600, 80, "PBI"),
        (680, 80, "Tab"),
        (760, 80, "Lkr"),
        (600, 160, "Met"),
        (680, 160, "Tht"),
        (760, 160, "LSt"),
    ]
    
    for x, y, label in tools:
        draw.rounded_rectangle([(x, y), (x+60, y+50)], radius=8, fill=(255, 255, 255, 50))
        if font_big:
            small_font = ImageFont.truetype(font_paths[0], 18)
            draw.text((x+10, y+12), label, fill=(255, 255, 255, 255), font=small_font)
    
    # 5. 绘制标题区域背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(30, 270), (870, 370)],
        fill=(0, 0, 0, 120)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 6. 绘制标题文字
    if font_big:
        title_font = ImageFont.truetype(font_paths[0], 32)
        subtitle_font = ImageFont.truetype(font_paths[0], 18)
        
        draw.text((50, 280), "2026 AI数据分析工具横评", fill=(255, 255, 255, 255), font=title_font)
        draw.text((50, 325), "Power BI vs Tableau vs Looker vs Metabase", fill=(180, 220, 255, 255), font=subtitle_font)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/data_analysis_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_data_analysis_cover()