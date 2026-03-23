#!/usr/bin/env python3
"""
测试微信草稿箱API
"""
import os
import sys
import requests
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config


def get_access_token(app_id: str, app_secret: str) -> str:
    """获取 access_token"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if "access_token" in data:
        return data["access_token"]
    else:
        raise Exception(f"获取 access_token 失败: {data}")


def upload_thumb(token: str, image_path: str) -> str:
    """上传封面图"""
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    params = {"access_token": token, "type": "thumb"}
    
    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, params=params, files=files, timeout=60)
        result = response.json()
    
    if result.get("media_id"):
        return result["media_id"]
    else:
        raise Exception(f"上传封面图失败: {result}")


def create_draft(token: str, title: str, content: str, thumb_media_id: str) -> str:
    """创建草稿"""
    url = "https://api.weixin.qq.com/cgi-bin/draft/add"
    params = {"access_token": token}
    
    article = {
        "title": title,
        "author": "AI观察",
        "content": content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }
    
    data = {"articles": [article]}
    
    response = requests.post(url, params=params, json=data, timeout=30)
    result = response.json()
    
    print(f"[DEBUG] API响应: {result}")
    
    if result.get("media_id"):
        return result.get("media_id")
    else:
        raise Exception(f"创建草稿失败: {result}")


def main():
    """主函数"""
    print("="*50)
    print("微信草稿箱API测试")
    print("="*50)
    
    # 获取配置
    config = load_config()
    wechat_config = config.get("wechat", {})
    app_id = wechat_config.get("app_id", "")
    app_secret = wechat_config.get("app_secret", "")
    
    if not app_id or app_id == "your_app_id_here":
        print("\n[ERROR] 微信公众号未配置")
        return
    
    try:
        # 获取 access_token
        print("\n[Step 1] 获取 access_token...")
        token = get_access_token(app_id, app_secret)
        print("[OK] access_token 获取成功")
        
        # 检查封面图
        cover_path = "cover.png"
        if not os.path.exists(cover_path):
            print(f"[ERROR] 封面图不存在: {cover_path}")
            return
        
        # 上传封面图
        print("\n[Step 2] 上传封面图...")
        thumb_media_id = upload_thumb(token, cover_path)
        print(f"[OK] 封面图上传成功，media_id: {thumb_media_id}")
        
        # 创建简单测试文章
        print("\n[Step 3] 创建测试草稿...")
        test_content = """<h1>AI热点速递</h1>
<p>这是一篇测试文章，用于验证微信草稿箱API是否正常工作。</p>
<h2>技术突破</h2>
<p>OpenAI发布GPT-5.4，首次在通用模型中引入原生计算机操控能力。</p>
<h2>产品发布</h2>
<p>阿里巴巴发布"悟空"企业级AI原生工作平台。</p>
<h2>行业动态</h2>
<p>腾讯混元3.0即将发布，全力押注AI Agent。</p>"""
        
        media_id = create_draft(
            token=token,
            title="AI热点速递",
            content=test_content,
            thumb_media_id=thumb_media_id
        )
        print(f"[OK] 草稿创建成功！media_id: {media_id}")
        
        print("\n" + "="*50)
        print("[SUCCESS] 测试成功！")
        print("="*50)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")


if __name__ == "__main__":
    main()
