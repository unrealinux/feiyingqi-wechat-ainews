#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Cover Generator - 基于 FeiqingqiWechatMP 的 ai-image-generator.js 实现

支持多种AI图片生成API：
- 智谱AI CogView (国内首选)
- 阿里Z-Image (国内备选)
- Google Gemini (国际备选)
- 渐变降级方案
"""
import os
import sys
import json
import base64
import requests
from typing import Optional, Dict, Tuple
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent))


class AICoverGenerator:
    """AI封面图生成器 - 参考FeiqingqiWechatMP实现"""
    
    # 微信公众号封面尺寸
    WECHAT_WIDTH = 900
    WECHAT_HEIGHT = 383
    
    # AI科技主题提示词模板 (参考WINE_PROMPTS)
    AI_PROMPTS = {
        "datacenter": {
            "prompt": "Professional photorealistic photograph of a modern AI data center interior. Rows of glowing blue server racks with LED lights, dramatic lighting from above. Holographic neural network visualization floating between the racks. Cinematic lighting, 8K resolution, commercial photography style. Blue and purple color scheme, high-tech atmosphere.",
            "negative": "blurry, low quality, cartoon, text, watermark, deformed, overexposed"
        },
        "chip": {
            "prompt": "Close-up product photography of a futuristic AI processor chip. Glowing golden circuit traces on dark silicon surface. Light particles flowing through the circuits representing data processing. Professional studio lighting, shallow depth of field, ultra-detailed. Dark background with subtle blue ambient light.",
            "negative": "blurry, low quality, cartoon, text, watermark, deformed"
        },
        "robot": {
            "prompt": "Photorealistic image of a humanoid AI robot in a modern office. The robot has a sleek white and blue design, interacting with a holographic display. Modern minimalist office environment with large windows showing city skyline. Professional commercial photography, soft natural lighting.",
            "negative": "blurry, ugly, deformed, low quality, text, watermark"
        },
        "neural": {
            "prompt": "Abstract visualization of a deep neural network. Glowing nodes connected by luminous data streams in a dark void. Blue, purple and gold color palette. 3D rendering with depth of field, particle effects. Scientific visualization style, photorealistic quality.",
            "negative": "blurry, low quality, cartoon, text, watermark"
        },
        "office": {
            "prompt": "Modern tech company office with AI integration. Large transparent displays showing real-time data analytics. Employees working with advanced AI assistants. Floor-to-ceiling windows, modern architecture, plants. Natural lighting mixed with ambient blue accent lights.",
            "negative": "blurry, low quality, cartoon, text, watermark, modern"
        }
    }
    
    def __init__(self, config: Dict = None, proxy: str = None):
        """
        初始化AI封面图生成器
        
        Args:
            config: API配置字典
            proxy: 代理地址 (如 http://127.0.0.1:10809)
        """
        self.config = config or {}
        self.proxy = proxy
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        self.output_dir = Path("output/covers")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, 
                 title: str,
                 element: str = "datacenter",
                 date: str = None,
                 output_path: str = "cover.png") -> Tuple[Optional[str], Optional[str]]:
        """
        生成封面图
        
        Args:
            title: 文章标题
            element: 元素类型 (datacenter, chip, robot, neural, office)
            date: 日期
            output_path: 输出路径
        
        Returns:
            (图片路径, 使用的提供商)
        """
        # 获取提示词
        prompt_data = self.AI_PROMPTS.get(element, self.AI_PROMPTS["datacenter"])
        
        # 检查可用的API密钥
        glm_key = self.config.get("zhipu", {}).get("api_key", "")
        zimage_key = self.config.get("zimage", {}).get("api_key", "")
        gemini_key = self.config.get("gemini", {}).get("api_key", "")
        
        image_buffer = None
        used_provider = None
        
        # 优先级：国内API > 国际API > 渐变降级
        
        # 1. 尝试智谱AI (GLM)
        if not image_buffer and glm_key:
            try:
                print("[AI Cover] 尝试智谱AI CogView...")
                image_buffer = self._generate_with_glm(glm_key, prompt_data["prompt"])
                used_provider = "GLM-Image (智谱AI)"
                print("[OK] 智谱AI生成成功")
            except Exception as e:
                print(f"[Warning] 智谱AI失败: {e}")
        
        # 2. 尝试阿里Z-Image
        if not image_buffer and zimage_key:
            try:
                print("[AI Cover] 尝试阿里Z-Image...")
                image_buffer = self._generate_with_zimage(zimage_key, prompt_data["prompt"], prompt_data["negative"])
                used_provider = "Z-Image (阿里通义)"
                print("[OK] 阿里Z-Image生成成功")
            except Exception as e:
                print(f"[Warning] 阿里Z-Image失败: {e}")
        
        # 3. 尝试Google Gemini
        if not image_buffer and gemini_key:
            try:
                print("[AI Cover] 尝试Google Gemini...")
                image_buffer = self._generate_with_gemini(gemini_key, prompt_data["prompt"], prompt_data["negative"])
                used_provider = "Google Gemini"
                print("[OK] Google Gemini生成成功")
            except Exception as e:
                print(f"[Warning] Google Gemini失败: {e}")
        
        # 4. 渐变降级
        if not image_buffer:
            print("[AI Cover] 使用渐变降级方案")
            image_buffer = self._create_gradient_fallback(element)
            used_provider = "Gradient (降级)"
        
        print(f"[Provider] 使用的提供商: {used_provider}")
        
        # 裁剪为微信封面尺寸
        image_buffer = self._crop_to_wechat_cover(image_buffer)
        
        # 添加文字叠加
        image_buffer = self._add_text_overlay(image_buffer, title, date)
        
        # 保存图片
        with open(output_path, "wb") as f:
            f.write(image_buffer)
        
        print(f"[Saved] 封面图已保存: {output_path}")
        return output_path, used_provider
    
    def _generate_with_glm(self, api_key: str, prompt: str) -> bytes:
        """
        使用智谱AI CogView生成图片
        
        API文档: https://open.bigmodel.cn/api/paas/v4/images/generations
        """
        response = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "cogview-4",
                "prompt": prompt,
                "size": "1024x1024"
            },
            proxies=self.proxies,
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"GLM API错误: {response.status_code}")
        
        data = response.json()
        
        if not data.get("data") or not data["data"][0].get("url"):
            raise Exception("GLM响应中没有图片URL")
        
        # 下载图片
        image_url = data["data"][0]["url"]
        image_response = requests.get(image_url, timeout=60)
        
        if image_response.status_code != 200:
            raise Exception(f"下载图片失败: {image_response.status_code}")
        
        return image_response.content
    
    def _generate_with_zimage(self, api_key: str, prompt: str, negative_prompt: str = "") -> bytes:
        """
        使用阿里Z-Image生成图片
        
        API文档: https://api.modelscope.cn/v1/images/generations
        """
        response = requests.post(
            "https://api.modelscope.cn/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "z-image-turbo",
                "prompt": prompt,
                "negative_prompt": negative_prompt or "blurry, low quality, cartoon, text, watermark",
                "steps": 8,
                "width": 1024,
                "height": 1024
            },
            proxies=self.proxies,
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"Z-Image API错误: {response.status_code}")
        
        data = response.json()
        
        if not data.get("data") or not data["data"][0].get("image"):
            raise Exception("Z-Image响应中没有图片数据")
        
        # 解码base64图片
        return base64.b64decode(data["data"][0]["image"])
    
    def _generate_with_gemini(self, api_key: str, prompt: str, negative_prompt: str = "") -> bytes:
        """
        使用Google Gemini生成图片
        
        API文档: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent
        """
        full_prompt = f"{prompt}. {f'Negative: {negative_prompt}' if negative_prompt else ''}"
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"responseModalities": "image"}
            },
            proxies=self.proxies,
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"Gemini API错误: {response.status_code}")
        
        data = response.json()
        
        if not data.get("candidates") or not data["candidates"][0].get("content"):
            raise Exception("Gemini响应中没有图片数据")
        
        # 查找图片部分
        parts = data["candidates"][0]["content"].get("parts", [])
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        
        raise Exception("Gemini响应中没有找到图片")
    
    def _crop_to_wechat_cover(self, image_data: bytes) -> bytes:
        """裁剪为微信封面尺寸 (900x383)"""
        try:
            from PIL import Image
            
            img = Image.open(BytesIO(image_data))
            
            # 计算裁剪比例
            target_ratio = self.WECHAT_WIDTH / self.WECHAT_HEIGHT  # 约2.35:1
            img_ratio = img.width / img.height
            
            if img_ratio > target_ratio:
                # 图片太宽，按高度裁剪
                new_width = int(img.height * target_ratio)
                left = (img.width - new_width) // 2
                img = img.crop((left, 0, left + new_width, img.height))
            else:
                # 图片太高，按宽度裁剪
                new_height = int(img.width / target_ratio)
                top = (img.height - new_height) // 2
                img = img.crop((0, top, img.width, top + new_height))
            
            # 调整大小
            img = img.resize((self.WECHAT_WIDTH, self.WECHAT_HEIGHT), Image.Resampling.LANCZOS)
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
            
        except ImportError:
            # 如果没有PIL，直接返回原图
            print("[Warning] PIL未安装，跳过裁剪")
            return image_data
    
    def _add_text_overlay(self, image_data: bytes, title: str, date: str = None) -> bytes:
        """添加文字叠加层"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.open(BytesIO(image_data))
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
                "/System/Library/Fonts/PingFang.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
            ]
            
            font_title = None
            font_date = None
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font_title = ImageFont.truetype(font_path, 32)
                        font_date = ImageFont.truetype(font_path, 14)
                        break
                    except Exception:
                        continue
            
            if not font_title:
                font_title = ImageFont.load_default()
                font_date = font_title
            
            # 绘制半透明背景条
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(
                [(0, 250), (self.WECHAT_WIDTH, self.WECHAT_HEIGHT)],
                fill=(0, 0, 0, 153)  # 60%透明度
            )
            
            # 合成背景条
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)
            
            # 绘制标题
            title_lines = []
            line = ""
            max_chars = 22
            
            for char in title:
                if len(line) >= max_chars and char != ' ':
                    title_lines.append(line)
                    line = char
                else:
                    line += char
            title_lines.append(line)
            
            # 限制行数
            title_lines = title_lines[:2]
            
            y_start = 280
            for i, line in enumerate(title_lines):
                # 阴影效果
                draw.text((32, y_start + i * 38 + 2), line, fill=(0, 0, 0, 128), font=font_title)
                # 主文字
                draw.text((30, y_start + i * 38), line, fill=(212, 175, 55), font=font_title)
            
            # 绘制日期
            if date:
                draw.text(
                    (self.WECHAT_WIDTH - 30, self.WECHAT_HEIGHT - 25),
                    date,
                    fill=(212, 175, 55, 230),
                    font=font_date,
                    anchor="rs"
                )
            
            # 转换为RGB并保存
            img = img.convert('RGB')
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
            
        except ImportError:
            print("[Warning] PIL未安装，跳过文字叠加")
            return image_data
    
    def _create_gradient_fallback(self, element: str) -> bytes:
        """创建渐变降级背景"""
        gradients = {
            "datacenter": ["#0a1628", "#1a3a5c", "#2d5a8e"],
            "chip": ["#0f0f23", "#1a1a3e", "#2d2d6e"],
            "robot": ["#111827", "#1f2937", "#374151"],
            "neural": ["#1a0a2e", "#2d1452", "#4a1a7a"],
            "office": ["#0f172a", "#1e3a5f", "#3b82f6"]
        }
        
        colors = gradients.get(element, gradients["datacenter"])
        
        try:
            from PIL import Image, ImageDraw
            
            img = Image.new('RGB', (1024, 1024))
            draw = ImageDraw.Draw(img)
            
            # 转换颜色
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            rgb_colors = [hex_to_rgb(c) for c in colors]
            
            # 创建渐变
            for y in range(1024):
                t = y / 1024
                if len(rgb_colors) == 2:
                    r = int(rgb_colors[0][0] + (rgb_colors[1][0] - rgb_colors[0][0]) * t)
                    g = int(rgb_colors[0][1] + (rgb_colors[1][1] - rgb_colors[0][1]) * t)
                    b = int(rgb_colors[0][2] + (rgb_colors[1][2] - rgb_colors[0][2]) * t)
                else:
                    segment = t * (len(rgb_colors) - 1)
                    idx = min(int(segment), len(rgb_colors) - 2)
                    local_t = segment - idx
                    r = int(rgb_colors[idx][0] + (rgb_colors[idx+1][0] - rgb_colors[idx][0]) * local_t)
                    g = int(rgb_colors[idx][1] + (rgb_colors[idx+1][1] - rgb_colors[idx][1]) * local_t)
                    b = int(rgb_colors[idx][2] + (rgb_colors[idx+1][2] - rgb_colors[idx][2]) * local_t)
                
                draw.line([(0, y), (1024, y)], fill=(r, g, b))
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()
            
        except ImportError:
            # 如果没有PIL，返回简单的PNG
            import struct
            import zlib
            
            r, g, b = hex_to_rgb(colors[0])
            
            raw_data = b''
            for y in range(1024):
                raw_data += b'\x00'
                for x in range(1024):
                    raw_data += bytes([r, g, b])
            
            def png_chunk(chunk_type, data):
                chunk = chunk_type + data
                crc = zlib.crc32(chunk) & 0xffffffff
                return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)
            
            signature = b'\x89PNG\r\n\x1a\n'
            ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1024, 1024, 8, 2, 0, 0, 0))
            idat = png_chunk(b'IDAT', zlib.compress(raw_data, 9))
            iend = png_chunk(b'IEND', b'')
            
            return signature + ihdr + idat + iend


# 便捷函数
def generate_ai_cover(title: str,
                      element: str = "datacenter",
                      date: str = None,
                      output_path: str = "cover.png",
                      config: Dict = None,
                      proxy: str = None) -> Tuple[Optional[str], Optional[str]]:
    """生成AI封面图的便捷函数"""
    generator = AICoverGenerator(config, proxy)
    return generator.generate(title, element, date, output_path)


if __name__ == "__main__":
    # 测试
    from src.config import load_config
    
    config = load_config()
    proxy = "http://127.0.0.1:10809"
    
    result = generate_ai_cover(
        title="AI热点速递 | 2026年3月22日",
        element="datacenter",
        date="2026-03-22",
        output_path="output/test_ai_cover.png",
        config=config,
        proxy=proxy
    )
    
    print(f"生成结果: {result}")
