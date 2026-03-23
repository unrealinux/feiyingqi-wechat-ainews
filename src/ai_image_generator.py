#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI图片生成API支持模块
参考 FeiqingqiWechatMP 的 ai-image-generator.js 实现

支持的API：
1. 智谱AI CogView (推荐 - 国内)
2. 阿里通义万相 Z-Image (国内)
3. 百度文心一格 (国内)
4. OpenAI DALL-E (国际)
5. Google Gemini (国际)
6. Stability AI Stable Diffusion (国际)
"""
import os
import base64
import requests
from typing import Optional, Dict, Any
from pathlib import Path


class AIImageGenerator:
    """AI图片生成器 - 支持多种API"""
    
    # 写实风格的AI科技提示词模板
    REALISTIC_PROMPTS = {
        "datacenter": """Professional photorealistic photograph of a modern AI data center interior.
Rows of glowing blue server racks with LED lights, dramatic lighting from above.
Holographic neural network visualization floating between the racks.
Cinematic lighting, 8K resolution, commercial photography style.
Blue and purple color scheme, high-tech atmosphere.""",

        "chip": """Close-up product photography of a futuristic AI processor chip.
Glowing golden circuit traces on dark silicon surface.
Light particles flowing through the circuits representing data processing.
Professional studio lighting, shallow depth of field, ultra-detailed.
Dark background with subtle blue ambient light.""",

        "robot": """Photorealistic image of a humanoid AI robot in a modern office.
The robot has a sleek white and blue design, interacting with a holographic display.
Modern minimalist office environment with large windows showing city skyline.
Professional commercial photography, soft natural lighting.
Technology and innovation theme.""",

        "neural": """Abstract visualization of a deep neural network.
Glowing nodes connected by luminous data streams in a dark void.
Blue, purple and gold color palette.
3D rendering with depth of field, particle effects.
Scientific visualization style, photorealistic quality.""",

        "office": """Modern tech company office with AI integration.
Large transparent displays showing real-time data analytics.
Employees working with advanced AI assistants.
Floor-to-ceiling windows, modern architecture, plants.
Natural lighting mixed with ambient blue accent lights.
Professional interior photography.""",
    }
    
    def __init__(self, config: Dict[str, str] = None):
        """
        初始化AI图片生成器
        
        Args:
            config: API配置字典，包含各种API的密钥
                    {
                        "zhipu": "sk-xxx",
                        "openai": "sk-xxx",
                        "baidu_api_key": "xxx",
                        "baidu_secret_key": "xxx",
                        "stability": "sk-xxx",
                        "gemini": "xxx"
                    }
        """
        self.config = config or {}
        self.output_dir = Path("output/covers")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, 
                 title: str,
                 style: str = "datacenter",
                 provider: str = "auto",
                 size: str = "1024x1024") -> Optional[bytes]:
        """
        生成AI图片
        
        Args:
            title: 图片标题（用于生成提示词）
            style: 风格 (datacenter, chip, robot, neural, office)
            provider: API提供商 (auto, zhipu, openai, baidu, stability, gemini)
            size: 图片尺寸
        
        Returns:
            图片字节数据，失败返回None
        """
        # 获取提示词
        base_prompt = self.REALISTIC_PROMPTS.get(style, self.REALISTIC_PROMPTS["datacenter"])
        full_prompt = f"{base_prompt}\n\nArticle title: {title}\nNo text overlay needed."
        
        # 自动选择可用的API
        if provider == "auto":
            provider = self._select_available_provider()
            if not provider:
                print("[Error] 未配置任何AI图片生成API")
                return None
        
        print(f"[AI Cover] 使用 {provider} 生成封面图...")
        
        # 调用对应的API
        generators = {
            "zhipu": self._generate_with_zhipu,
            "zimage": self._generate_with_zimage,
            "openai": self._generate_with_openai,
            "baidu": self._generate_with_baidu,
            "stability": self._generate_with_stability,
            "gemini": self._generate_with_gemini,
        }
        
        generator_func = generators.get(provider)
        if not generator_func:
            print(f"[Error] 不支持的API提供商: {provider}")
            return None
        
        return generator_func(full_prompt, size)
    
    def _select_available_provider(self) -> Optional[str]:
        """选择可用的API提供商"""
        # 优先级：国内API > 国际API
        providers = [
            ("zhipu", "zhipu"),
            ("zimage", "zimage"),
            ("baidu", "baidu_api_key"),
            ("openai", "openai"),
            ("stability", "stability"),
            ("gemini", "gemini"),
        ]
        
        for provider, config_key in providers:
            if self.config.get(config_key):
                return provider
        
        return None
    
    # ==================== 智谱AI CogView ====================
    def _generate_with_zhipu(self, prompt: str, size: str = "1024x1024") -> Optional[bytes]:
        """
        使用智谱AI CogView生成图片
        
        注册地址: https://open.bigmodel.cn
        免费额度: 15积分（约50张图片）
        特点: 国内服务器，速度快，中文优化
        """
        api_key = self.config.get("zhipu")
        if not api_key:
            print("[Error] 未配置智谱AI API密钥")
            return None
        
        try:
            response = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "cogview-4",
                    "prompt": prompt,
                    "size": size
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                image_url = data["data"][0]["url"]
                
                # 下载图片
                img_response = requests.get(image_url, timeout=60)
                if img_response.status_code == 200:
                    print("[OK] 智谱AI CogView 生成成功")
                    return img_response.content
            else:
                print(f"[Error] 智谱AI API错误: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"[Error] 智谱AI生成失败: {e}")
        
        return None
    
    # ==================== OpenAI DALL-E ====================
    def _generate_with_openai(self, prompt: str, size: str = "1024x1024") -> Optional[bytes]:
        """
        使用OpenAI DALL-E生成图片
        
        注册地址: https://platform.openai.com
        特点: 高质量，支持多种尺寸
        """
        api_key = self.config.get("openai")
        if not api_key:
            print("[Error] 未配置OpenAI API密钥")
            return None
        
        try:
            # DALL-E 3支持的尺寸
            dalle_size = "1792x1024" if "1792" in size else "1024x1024"
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "size": dalle_size,
                    "quality": "hd",
                    "n": 1,
                    "response_format": "b64_json"
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                image_data = base64.b64decode(data["data"][0]["b64_json"])
                print("[OK] OpenAI DALL-E 生成成功")
                return image_data
            else:
                print(f"[Error] OpenAI API错误: {response.status_code}")
                
        except Exception as e:
            print(f"[Error] OpenAI生成失败: {e}")
        
        return None
    
    # ==================== 阿里通义万相 Z-Image ====================
    def _generate_with_zimage(self, prompt: str, size: str = "1024x1024") -> Optional[bytes]:
        """
        使用阿里通义万相 Z-Image 生成图片
        
        注册地址: https://www.modelscope.cn
        特点: 国内服务器，速度快，有免费额度
        模型: z-image-turbo (快速) 或 z-image (高质量)
        """
        api_key = self.config.get("zimage")
        if not api_key:
            print("[Error] 未配置阿里Z-Image API密钥")
            return None
        
        try:
            # 解析尺寸
            width, height = 1024, 1024
            if size and "x" in size:
                parts = size.split("x")
                width, height = int(parts[0]), int(parts[1])
            
            response = requests.post(
                "https://api.modelscope.cn/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "z-image-turbo",  # 使用turbo版本，速度更快
                    "prompt": prompt,
                    "negative_prompt": "blurry, low quality, cartoon, text, watermark, deformed",
                    "steps": 8,  # 推理步数，turbo版本建议8步
                    "width": min(width, 1024),
                    "height": min(height, 1024)
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查响应格式
                if data.get("data") and data["data"][0].get("image"):
                    # 返回的是base64编码的图片
                    image_data = base64.b64decode(data["data"][0]["image"])
                    print("[OK] 阿里Z-Image 生成成功")
                    return image_data
                elif data.get("data") and data["data"][0].get("url"):
                    # 返回的是URL
                    img_url = data["data"][0]["url"]
                    img_response = requests.get(img_url, timeout=60)
                    if img_response.status_code == 200:
                        print("[OK] 阿里Z-Image 生成成功")
                        return img_response.content
                else:
                    print(f"[Error] 阿里Z-Image 响应格式不正确: {data}")
            else:
                print(f"[Error] 阿里Z-Image API错误: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"[Error] 阿里Z-Image生成失败: {e}")
        
        return None
    
    # ==================== 百度文心一格 ====================
    def _generate_with_baidu(self, prompt: str, size: str = "1024x1024") -> Optional[bytes]:
        """
        使用百度文心一格生成图片
        
        注册地址: https://yige.baidu.com
        特点: 国内服务，中文理解好
        """
        api_key = self.config.get("baidu_api_key")
        secret_key = self.config.get("baidu_secret_key")
        
        if not api_key or not secret_key:
            print("[Error] 未配置百度API密钥")
            return None
        
        try:
            # 获取access_token
            token_url = "https://aip.baidubce.com/oauth/2.0/token"
            token_response = requests.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": secret_key
            })
            access_token = token_response.json().get("access_token")
            
            if not access_token:
                print("[Error] 获取百度access_token失败")
                return None
            
            # 生成图片
            url = f"https://aip.baidubce.com/rpc/2.0/ernievilg/v1/txt2img?access_token={access_token}"
            
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "text": prompt,
                    "style": "写实风格",
                    "resolution": "1024*1024"
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                # 百度API返回的是异步任务，需要轮询获取结果
                task_id = data.get("data", {}).get("task_id")
                if task_id:
                    return self._poll_baidu_result(task_id, access_token)
            
        except Exception as e:
            print(f"[Error] 百度生成失败: {e}")
        
        return None
    
    def _poll_baidu_result(self, task_id: str, access_token: str, max_retries: int = 30) -> Optional[bytes]:
        """轮询百度文心一格结果"""
        import time
        
        url = f"https://aip.baidubce.com/rpc/2.0/ernievilg/v1/getImg?access_token={access_token}"
        
        for i in range(max_retries):
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={"task_id": task_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    task_status = data.get("data", {}).get("task_status")
                    
                    if task_status == "SUCCESS":
                        img_url = data.get("data", {}).get("img_url")
                        if img_url:
                            img_response = requests.get(img_url, timeout=60)
                            if img_response.status_code == 200:
                                print("[OK] 百度文心一格 生成成功")
                                return img_response.content
                    
                    elif task_status == "FAILED":
                        print("[Error] 百度文心一格 生成失败")
                        return None
                
                time.sleep(2)
                print(f"[Waiting] 等待百度生成结果... ({i+1}/{max_retries})")
                
            except Exception as e:
                print(f"[Error] 轮询百度结果失败: {e}")
                return None
        
        print("[Error] 百度生成超时")
        return None
    
    # ==================== Stability AI ====================
    def _generate_with_stability(self, prompt: str, size: str = "1024x1024") -> Optional[bytes]:
        """
        使用Stability AI Stable Diffusion生成图片
        
        注册地址: https://platform.stability.ai
        特点: 开源模型，高质量，可定制
        """
        api_key = self.config.get("stability")
        if not api_key:
            print("[Error] 未配置Stability AI API密钥")
            return None
        
        try:
            width, height = map(int, size.split("x"))
            
            response = requests.post(
                "https://api.stability.ai/v2beta/stable-image/generate/sd3",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "image/*"
                },
                files={"none": ""},
                data={
                    "prompt": prompt,
                    "negative_prompt": "text, watermark, blurry, low quality",
                    "aspect_ratio": "16:9" if width > height else "1:1",
                    "output_format": "png"
                },
                timeout=120
            )
            
            if response.status_code == 200:
                print("[OK] Stability AI 生成成功")
                return response.content
            else:
                print(f"[Error] Stability AI API错误: {response.status_code}")
                
        except Exception as e:
            print(f"[Error] Stability AI生成失败: {e}")
        
        return None
    
    # ==================== Google Gemini ====================
    def _generate_with_gemini(self, prompt: str, size: str = "1024x1024") -> Optional[bytes]:
        """
        使用Google Gemini生成图片
        
        注册地址: https://aistudio.google.com/app/apikey
        特点: 每天免费500张，国际服务
        """
        api_key = self.config.get("gemini")
        if not api_key:
            print("[Error] 未配置Gemini API密钥")
            return None
        
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseModalities": ["image"]
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                
                for part in parts:
                    if "inlineData" in part:
                        image_data = base64.b64decode(part["inlineData"]["data"])
                        print("[OK] Google Gemini 生成成功")
                        return image_data
            
            print(f"[Error] Gemini API错误: {response.status_code}")
                
        except Exception as e:
            print(f"[Error] Gemini生成失败: {e}")
        
        return None


# 便捷函数
def generate_ai_cover(title: str, 
                      style: str = "datacenter",
                      provider: str = "auto",
                      config: Dict[str, str] = None) -> Optional[bytes]:
    """生成AI封面图的便捷函数"""
    generator = AIImageGenerator(config)
    return generator.generate(title, style, provider)


def save_ai_cover(title: str,
                  output_path: str = "cover.png",
                  style: str = "datacenter",
                  provider: str = "auto",
                  config: Dict[str, str] = None) -> Optional[str]:
    """生成并保存AI封面图"""
    image_data = generate_ai_cover(title, style, provider, config)
    
    if image_data:
        # 调整大小为微信封面尺寸
        try:
            from PIL import Image
            from io import BytesIO
            
            img = Image.open(BytesIO(image_data))
            img = img.resize((900, 383), Image.Resampling.LANCZOS)
            img.save(output_path, "PNG")
            print(f"[Saved] AI封面图已保存: {output_path}")
            return output_path
        except ImportError:
            # 如果没有PIL，直接保存
            with open(output_path, "wb") as f:
                f.write(image_data)
            print(f"[Saved] AI封面图已保存: {output_path}")
            return output_path
    
    return None


# API信息
API_INFO = """
============================================================
AI图片生成API对比
============================================================

【国内API - 推荐优先使用】

1. 智谱AI CogView ⭐⭐⭐⭐⭐
   注册: https://open.bigmodel.cn
   免费额度: 15积分（约50张图片）
   特点: 国内服务器，速度快，中文优化，质量高
   配置: zhipu_api_key=sk-xxxxxxxx

2. 阿里通义万相 Z-Image ⭐⭐⭐⭐
   注册: https://www.modelscope.cn
   免费额度: 有免费额度
   特点: 国内服务器，速度快
   配置: zimage_api_key=xxxxxxxx

3. 百度文心一格 ⭐⭐⭐⭐
   注册: https://yige.baidu.com
   免费额度: 新用户赠送体验额度
   特点: 国内服务，中文理解好
   配置: baidu_api_key=xxx, baidu_secret_key=xxx

【国际API - 需要代理】

4. OpenAI DALL-E 3 ⭐⭐⭐⭐⭐
   注册: https://platform.openai.com
   价格: $0.040/张 (标准), $0.080/张 (高清)
   特点: 质量最高，支持多种尺寸
   配置: openai_api_key=sk-xxxxxxxx

5. Google Gemini ⭐⭐⭐⭐
   注册: https://aistudio.google.com/app/apikey
   免费额度: 每天500张免费
   特点: 免费额度大，国际服务
   配置: gemini_api_key=xxxxxxxx

6. Stability AI ⭐⭐⭐⭐
   注册: https://platform.stability.ai
   免费额度: 25积分免费
   特点: 开源模型，可定制
   配置: stability_api_key=sk-xxxxxxxx

============================================================
"""


if __name__ == "__main__":
    print(API_INFO)
    
    # 测试生成
    from src.config import load_config
    config = load_config()
    
    api_keys = {
        "zhipu": config.get("zhipu", {}).get("api_key", ""),
        "openai": config.get("openai", {}).get("api_key", ""),
    }
    
    generator = AIImageGenerator(api_keys)
    
    # 测试生成
    result = generator.generate(
        title="AI热点速递 | 2026年3月22日",
        style="datacenter",
        provider="auto"
    )
    
    if result:
        output_path = "output/test_ai_cover.png"
        with open(output_path, "wb") as f:
            f.write(result)
        print(f"测试封面图已保存: {output_path}")
