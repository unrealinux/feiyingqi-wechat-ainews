#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成微信公众号封面图 - 纯Python实现（无需PIL）
参考 FeiqingqiWechatMP 的封面图生成逻辑
"""
import struct
import zlib
import os
from pathlib import Path


def hex_to_rgb(hex_color):
    """将十六进制颜色转换为RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient_background(width, height, colors):
    """创建渐变背景"""
    pixel_data = []
    
    # 转换颜色
    rgb_colors = [hex_to_rgb(c) for c in colors]
    
    for y in range(height):
        row = []
        for x in range(width):
            # 计算渐变位置（对角线方向）
            t = (x / width + y / height) / 2
            
            # 在颜色之间插值
            if len(rgb_colors) == 2:
                r = int(rgb_colors[0][0] + (rgb_colors[1][0] - rgb_colors[0][0]) * t)
                g = int(rgb_colors[0][1] + (rgb_colors[1][1] - rgb_colors[0][1]) * t)
                b = int(rgb_colors[0][2] + (rgb_colors[1][2] - rgb_colors[0][2]) * t)
            else:
                # 多色渐变
                segment = t * (len(rgb_colors) - 1)
                idx = int(segment)
                if idx >= len(rgb_colors) - 1:
                    r, g, b = rgb_colors[-1]
                else:
                    local_t = segment - idx
                    r = int(rgb_colors[idx][0] + (rgb_colors[idx+1][0] - rgb_colors[idx][0]) * local_t)
                    g = int(rgb_colors[idx][1] + (rgb_colors[idx+1][1] - rgb_colors[idx][1]) * local_t)
                    b = int(rgb_colors[idx][2] + (rgb_colors[idx+1][2] - rgb_colors[idx][2]) * local_t)
            
            row.extend([r, g, b])
        pixel_data.extend(row)
    
    return bytes(pixel_data)


def add_glow_effect(pixel_data, width, height, glow_color, glow_intensity=0.15):
    """添加光晕效果"""
    import math
    
    pixel_list = list(pixel_data)
    
    # 光晕中心（左上角）
    center_x, center_y = width * 0.3, height * 0.5
    max_dist = math.sqrt(center_x**2 + center_y**2)
    
    glow_r, glow_g, glow_b = hex_to_rgb(glow_color)
    
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            if dist < max_dist * 0.5:
                intensity = 1 - (dist / (max_dist * 0.5))
                intensity = intensity * glow_intensity
                
                idx = (y * width + x) * 3
                r = pixel_list[idx]
                g = pixel_list[idx + 1]
                b = pixel_list[idx + 2]
                
                # 混合光晕颜色
                r = min(255, int(r + (glow_r - r) * intensity))
                g = min(255, int(g + (glow_g - g) * intensity))
                b = min(255, int(b + (glow_b - b) * intensity))
                
                pixel_list[idx] = r
                pixel_list[idx + 1] = g
                pixel_list[idx + 2] = b
    
    return bytes(pixel_list)


def create_png(filename, width, height, pixels):
    """创建PNG文件"""
    def png_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xffffffff
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)
    
    # PNG 签名
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = png_chunk(b'IHDR', ihdr_data)
    
    # IDAT chunk (图像数据)
    # 为每一行添加过滤器字节 (0 = 无过滤)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # 过滤器字节
        for x in range(width):
            idx = (y * width + x) * 3
            raw_data += bytes([pixels[idx], pixels[idx+1], pixels[idx+2]])
    
    compressed = zlib.compress(raw_data, 9)
    idat = png_chunk(b'IDAT', compressed)
    
    # IEND chunk
    iend = png_chunk(b'IEND', b'')
    
    # 写入文件
    with open(filename, 'wb') as f:
        f.write(signature)
        f.write(ihdr)
        f.write(idat)
        f.write(iend)


def generate_cover(title, output_path="cover.png", style="gradient_blue"):
    """生成封面图
    
    Args:
        title: 文章标题
        output_path: 输出路径
        style: 风格 (gradient_blue, tech_blue, dark_purple, ai_purple)
    """
    # 微信公众号封面图标准尺寸
    width, height = 900, 383
    
    # 配色方案 (参考FeiqingqiWechatMP)
    color_schemes = {
        'gradient_blue': ['#0f172a', '#1e3a5f', '#3b82f6', '#60a5fa'],
        'tech_blue': ['#0a1628', '#1a3a5c', '#2d5a8e', '#1e90ff'],
        'dark_purple': ['#1a0a2e', '#2d1452', '#4a1a7a', '#6b2d9e'],
        'ai_purple': ['#0f0f23', '#1a1a3e', '#2d2d6e', '#4a4a9e'],
        'modern_dark': ['#111827', '#1f2937', '#374151', '#4b5563'],
    }
    
    colors = color_schemes.get(style, color_schemes['gradient_blue'])
    
    print(f"[Step 1] 创建渐变背景...")
    pixel_data = create_gradient_background(width, height, colors)
    
    print(f"[Step 2] 添加光晕效果...")
    pixel_data = add_glow_effect(pixel_data, width, height, colors[-1], 0.15)
    
    print(f"[Step 3] 保存PNG文件...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    create_png(output_path, width, height, pixel_data)
    
    print(f"[Done] 封面图已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    # 生成封面图
    generate_cover(
        title="AI热点速递 | 2026年3月22日",
        output_path="cover.png",
        style="gradient_blue"
    )
