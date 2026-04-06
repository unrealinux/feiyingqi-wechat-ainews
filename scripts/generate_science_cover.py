#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI科普文章封面生成器
生成通俗易懂风格的科普封面
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_science_cover():
    """创建AI科普主题封面"""
    # 创建温暖明亮的渐变背景
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 科普/教育主题（温暖明亮）
    colors = [
        (255, 245, 230),    # 浅黄
        (255, 220, 180),    # 橙色
        (255, 180, 150),    # 粉橙
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
    
    # 绘制装饰元素
    # 1. 左侧大问号（科普标志）
    draw.ellipse([(50, 50), (200, 200)], fill=(255, 255, 255, 200))
    draw.ellipse([(60, 60), (190, 190)], fill=(255, 150, 100, 150))
    
    # 绘制问号
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    
    font_big = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_big = ImageFont.truetype(font_path, 120)
                break
            except:
                continue
    
    if font_big:
        draw.text((90, 60), "?", fill=(255, 255, 255, 255), font=font_big)
    
    # 2. 绘制Token可视化（小方块网格）
    token_colors = [(255, 100, 100), (100, 200, 255), (100, 255, 150), (255, 200, 100)]
    for i in range(8):
        for j in range(4):
            x = 400 + i * 60
            y = 50 + j * 70
            color = token_colors[(i + j) % len(token_colors)]
            draw.rounded_rectangle([(x, y), (x+45, y+55)], radius=8, fill=color + (180,))
            # 在小方块内写Token
            if font_big:
                small_font = ImageFont.truetype(font_paths[0], 12)
                draw.text((x+5, y+15), "词元", fill=(255, 255, 255, 200), font=small_font)
    
    # 3. 绘制"140万亿"大数字
    if font_big:
        big_num_font = ImageFont.truetype(font_paths[0], 60)
        draw.text((420, 220), "140万亿", fill=(100, 50, 150, 255), font=big_num_font)
        draw.text((420, 290), "日均Token调用量", fill=(150, 100, 50, 200), font=ImageFont.truetype(font_paths[0], 20))
    
    # 4. 绘制标题区域背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(30, 250), (380, 360)],
        radius=15,
        fill=(255, 255, 255, 180)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 5. 绘制标题文字
    if font_big:
        title_font = ImageFont.truetype(font_paths[0], 28)
        subtitle_font = ImageFont.truetype(font_paths[0], 18)
        
        draw.text((50, 260), "AI科普", fill=(100, 50, 150, 255), font=title_font)
        draw.text((50, 300), "140万亿Token是什么概念？", fill=(80, 80, 80, 255), font=subtitle_font)
    
    # 6. 添加装饰小元素
    # 小星星
    for _ in range(15):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(2, 6)
        draw.ellipse([(x, y), (x+size, y+size)], fill=(255, 255, 200, 150))
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/science_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    import random
    create_science_cover()