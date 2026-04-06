#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成代码Agent文章的封面图 - 使用更写实的关键词
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.free_image_api import FreeImageAPI
import requests

def download_realistic_image():
    """下载写实风格的代码/AI相关封面图"""
    
    # 使用更写实、更具体的搜索关键词
    realistic_keywords = [
        "programmer coding computer",
        "software developer workstation",
        "AI artificial intelligence technology",
        "computer code screen",
        "developer programming laptop"
    ]
    
    api = FreeImageAPI()
    
    for keyword in realistic_keywords:
        print(f"Searching with keyword: {keyword}")
        try:
            images = api.search_images(keyword, per_page=5)
            if images:
                # 下载第一张图片
                result = api.download_image(images[0], "output/codeagent_cover.png")
                if result:
                    print(f"Successfully downloaded: {result}")
                    return True
        except Exception as e:
            print(f"Error with keyword '{keyword}': {e}")
            continue
    
    print("All keywords failed, trying fallback...")
    return False

if __name__ == "__main__":
    success = download_realistic_image()
    if success:
        print("Cover image generated successfully!")
    else:
        print("Failed to generate cover image")