#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Meeting Tools Cover Generator
生成AI会议工具横评封面图
"""
from PIL import Image, ImageDraw, ImageFont
import os

# 微信封面尺寸
WIDTH, HEIGHT = 900, 383

def create_meeting_cover():
    """创建AI会议工具主题封面"""
    # 创建深蓝色渐变背景
    img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # 渐变颜色 - 会议/科技主题
    colors = [
        (15, 23, 42),    # 深蓝黑
        (30, 58, 95),    # 深蓝
        (59, 130, 246),  # 亮蓝
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
    
    # 绘制会议相关图形元素
    # 1. 视频会议网格图标
    draw.rounded_rectangle([(50, 50), (200, 180)], radius=15, outline=(255, 255, 255, 180), width=3)
    draw.rounded_rectangle([(220, 50), (370, 180)], radius=15, outline=(255, 255, 255, 180), width=3)
    draw.rounded_rectangle([(50, 200), (200, 330)], radius=15, outline=(255, 255, 255, 180), width=3)
    draw.rounded_rectangle([(220, 200), (370, 330)], radius=15, outline=(255, 255, 255, 180), width=3)
    
    # 2. 在视频框内画小人图标
    for cx, cy in [(125, 115), (295, 115), (125, 265), (295, 265)]:
        # 头部
        draw.ellipse([(cx-15, cy-25), (cx+15, cy+5)], fill=(255, 255, 255, 100))
        # 身体
        draw.rectangle([(cx-20, cy+10), (cx+20, cy+35)], fill=(255, 255, 255, 100))
    
    # 3. AI波形/声波效果
    for i in range(20):
        x = 420 + i * 22
        h = 30 + abs(((i * 7) % 50) - 25) * 2
        y_center = HEIGHT // 2
        draw.rounded_rectangle(
            [(x, y_center - h//2), (x + 8, y_center + h//2)],
            radius=4,
            fill=(96, 165, 250, 200)
        )
    
    # 4. 添加文字区域背景
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(400, 0), (WIDTH, HEIGHT)],
        fill=(0, 0, 0, 100)
    )
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)
    
    # 尝试加载字体
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/microsoftyahei.ttc",
    ]
    
    font_title = None
    font_subtitle = None
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_title = ImageFont.truetype(font_path, 36)
                font_subtitle = ImageFont.truetype(font_path, 20)
                break
            except:
                continue
    
    if not font_title:
        font_title = ImageFont.load_default()
        font_subtitle = font_title
    
    # 绘制标题
    title = "2026 AI会议工具横评"
    draw.text((420, 80), title, fill=(255, 255, 255, 255), font=font_title)
    
    # 绘制副标题
    subtitle = "Otter vs Fireflies vs Fathom"
    draw.text((420, 140), subtitle, fill=(147, 197, 253, 255), font=font_subtitle)
    
    subtitle2 = "vs tl;dv vs MeetGeek vs Krisp"
    draw.text((420, 175), subtitle2, fill=(147, 197, 253, 255), font=font_subtitle)
    
    # 绘制亮点文字
    highlight = "自动记录 | 智能摘要 | CRM同步"
    draw.text((420, 240), highlight, fill=(250, 204, 21, 255), font=font_subtitle)
    
    # 转换为RGB保存
    img = img.convert('RGB')
    output_path = "output/meeting_cover.png"
    img.save(output_path, "PNG")
    print(f"封面已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    create_meeting_cover()