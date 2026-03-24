#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Z-Image API连接
"""
import os
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.config import load_config


def test_zimage_connection(api_key, proxy=None):
    """测试Z-Image API连接"""
    print("=" * 50)
    print("阿里Z-Image API连接测试")
    print("=" * 50)
    
    # 测试提示词
    prompt = """Professional photorealistic photograph of a modern AI data center.
Glowing blue server racks, holographic neural network visualization.
Cinematic lighting, 8K resolution, commercial photography style."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "z-image-turbo",
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, text, watermark",
        "steps": 8,
        "width": 1024,
        "height": 1024
    }
    
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
        print(f"\n[Proxy] 使用代理: {proxy}")
    
    print(f"\n[API Key] {api_key[:20]}...")
    print(f"[URL] https://api.modelscope.cn/v1/images/generations")
    
    try:
        print("\n[Testing] 正在测试连接...")
        response = requests.post(
            "https://api.modelscope.cn/v1/images/generations",
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=120
        )
        
        print(f"[Status] HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data") and result["data"][0].get("image"):
                print("[OK] API连接成功！")
                
                # 保存测试图片
                import base64
                image_data = base64.b64decode(result["data"][0]["image"])
                output_path = "output/test_zimage_cover.png"
                os.makedirs("output", exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"[Saved] 测试图片已保存: {output_path}")
                return True
        else:
            print(f"[Error] {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"[Error] 连接失败: {e}")
        print("\n[Try] 尝试以下解决方案：")
        print("1. 检查网络连接")
        print("2. 配置代理服务器")
        print("3. 使用其他AI图片API")
    except Exception as e:
        print(f"[Error] {e}")
    
    return False


def main():
    config = load_config()
    api_key = config.get("zimage", {}).get("api_key", "")
    
    if not api_key:
        print("[Error] 未配置Z-Image API密钥")
        return
    
    # 检查是否有代理配置
    http_proxy = os.environ.get("HTTP_PROXY", "")
    https_proxy = os.environ.get("HTTPS_PROXY", "")
    proxy = https_proxy or http_proxy
    
    # 如果没有环境变量代理，询问用户
    if not proxy:
        print("\n[Proxy] 检测代理设置...")
        use_proxy = input("是否需要使用代理? (y/n, 默认n): ").strip().lower()
        if use_proxy == 'y':
            proxy = input("请输入代理地址 (如 http://127.0.0.1:7890): ").strip()
    
    # 测试连接
    test_zimage_connection(api_key, proxy)


if __name__ == "__main__":
    main()
