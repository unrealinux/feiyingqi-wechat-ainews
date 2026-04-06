#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成代码Agent文章的封面图
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.free_image_api import FreeImageAPI

api = FreeImageAPI()

# 尝试不同风格
styles = ["robot", "chip", "neural", "office", "datacenter"]

for style in styles:
    print(f"Trying style: {style}")
    try:
        image_data = api.search_tech_image(style=style, use_proxy=False)
        if image_data:
            output_path = "output/codeagent_cover.png"
            with open(output_path, "wb") as f:
                f.write(image_data)
            print(f"Success: {output_path}")
            break
    except Exception as e:
        print(f"Error: {e}")
        continue