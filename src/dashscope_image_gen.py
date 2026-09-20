"""
DashScope Image Generator - 阿里云图片生成模块

使用 qwen-image-2.0-pro 模型生成写实风格封面图
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Optional

from src.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class DashScopeImageGenerator:
    """阿里云 DashScope 图片生成器"""
    
    def __init__(self):
        config = load_config()
        openai_config = config.get("openai", {})
        
        self.api_key = openai_config.get("api_key", "")
        if not self.api_key:
            # 尝试从环境变量读取
            self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        
        self.base_url = openai_config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        # 图片生成模型
        self.image_model = "qwen-image-2.0-pro"
        
    def generate_cover_image(self, 
                          prompt: str, 
                          output_path: str,
                          size: str = "1024*1024") -> Optional[str]:
        """
        生成封面图
        
        Args:
            prompt: 图片描述
            output_path: 输出路径
            size: 图片尺寸 (1024*1024, 720*1280, etc.)
            
        Returns:
            str: 生成的图片路径，失败返回 None
        """
        if not self.api_key:
            logger.error("DashScope API key not configured")
            return None
        
        # DashScope 多模态生成 API（qwen-image-2.0-pro 正确端点）
        # 北京地域
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 解析尺寸
        if '*' in size:
            width, height = size.split('*')
        else:
            width, height = "1024", "1024"
        
        payload = {
            "model": self.image_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "size": f"{width}*{height}",
                "n": 1,
                "prompt_extend": True,
                "watermark": False
            }
        }
        
        try:
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            # 检查响应是否为 JSON
            content_type = response.headers.get('Content-Type', '')
            if 'json' not in content_type.lower():
                logger.error(f"Non-JSON response ({response.status_code}): {response.text[:500]}")
                return None
                
            result = response.json()
            
            if response.status_code == 200 and "output" in result:
                # 获取图片 URL
                output_data = result.get("output", {})
                choices = output_data.get("choices", [])
                
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    content = message.get("content", [])
                    
                    if content and len(content) > 0 and "image" in content[0]:
                        image_url = content[0]["image"]
                        
                        # 下载图片
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
                            # 确保输出目录存在
                            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(output_path, "wb") as f:
                                f.write(img_response.content)
                            
                            logger.info(f"Image saved: {output_path}")
                            return output_path
                        else:
                            logger.error(f"Failed to download image: {img_response.status_code}")
                else:
                    logger.error(f"No image results in response: {result}")
            else:
                logger.error(f"Image generation failed ({response.status_code}): {result}")
                
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
        
        return None
        
        # DashScope 原生图片生成 API
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 解析尺寸
        if '*' in size:
            width, height = size.split('*')
        else:
            width, height = "1024", "1024"
        
        payload = {
            "model": self.image_model,
            "input": {
                "prompt": prompt
            },
            "parameters": {
                "width": int(width),
                "height": int(height),
                "n": 1
            }
        }
        
        try:
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            # 检查响应是否为 JSON
            content_type = response.headers.get('Content-Type', '')
            if 'json' not in content_type.lower():
                logger.error(f"Non-JSON response ({response.status_code}): {response.text[:200]}")
                return None
                
            result = response.json()
            
            if response.status_code == 200 and "output" in result:
                # 获取图片 URL
                output_data = result.get("output", {})
                results = output_data.get("results", [])
                
                if results and len(results) > 0:
                    image_url = results[0].get("url")
                    
                    if image_url:
                        # 下载图片
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
                            # 确保输出目录存在
                            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(output_path, "wb") as f:
                                f.write(img_response.content)
                            
                            logger.info(f"Image saved: {output_path}")
                            return output_path
                        else:
                            logger.error(f"Failed to download image: {img_response.status_code}")
                else:
                    logger.error(f"No image results in response: {result}")
            else:
                logger.error(f"Image generation failed ({response.status_code}): {result}")
                
        except Exception as e:
            logger.error(f"Error generating image: {e}", exc_info=True)
        
        return None
    
    def generate_ai_meeting_cover(self, title: str, output_dir: str = "output") -> Optional[str]:
        """
        生成 AI 会议工具相关的写实封面图
        
        Args:
            title: 文章标题
            output_dir: 输出目录
            
        Returns:
            str: 生成的图片路径
        """
        prompt = """A realistic professional photography style cover image for an AI meeting tools review article. 
Features: modern conference room with holographic AI interface projections, 
laptops showing AI tools like Zoom, Teams, Google Meet, Tencent Meeting, and Feishu, 
clean minimalist design, soft lighting, blue and white color scheme, 
high-tech atmosphere, 8K resolution, photorealistic, 
cinematic composition, professional business photography style."""

        # 使用时间戳生成文件名，避免特殊字符问题
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"ai_meeting_cover_{timestamp}.png"
        
        return self.generate_cover_image(prompt, str(output_path), size="1024*1024")


def generate_ai_cover(title: str = "AI Meeting Tools Review") -> Optional[str]:
    """
    便捷函数：生成 AI 相关封面图
    
    Args:
        title: 文章标题
        
    Returns:
        str: 图片路径或 None
    """
    generator = DashScopeImageGenerator()
    return generator.generate_ai_meeting_cover(title)


if __name__ == "__main__":
    print("Testing DashScope Image Generator...")
    result = generate_ai_cover("AI会议工具大横评")
    if result:
        print(f"Image generated: {result}")
    else:
        print("Image generation failed")
