#!/usr/bin/env python3
"""
发布Code Agent横向测评文章到微信公众号草稿箱
"""
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import load_config


def get_access_token(app_id, app_secret):
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": app_id, "secret": app_secret}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    if "access_token" in data:
        return data["access_token"]
    raise Exception(f"获取access_token失败: {data}")


def upload_thumb(token, image_path):
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    params = {"access_token": token, "type": "thumb"}
    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, params=params, files=files, timeout=60)
        result = response.json()
    if result.get("media_id"):
        return result["media_id"]
    raise Exception(f"上传封面图失败: {result}")


def create_draft(token, title, content, thumb_media_id, author):
    url = "https://api.weixin.qq.com/cgi-bin/draft/add"
    params = {"access_token": token}
    article = {
        "title": title,
        "author": author,
        "content": content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }
    data = {"articles": [article]}
    json_data = json.dumps(data, ensure_ascii=False)
    response = requests.post(url, params=params, data=json_data.encode('utf-8'), headers={"Content-Type": "application/json; charset=utf-8"}, timeout=30)
    result = response.json()
    if result.get("media_id"):
        return result["media_id"]
    raise Exception(f"创建草稿失败: {result}")


def main():
    print("=" * 50)
    print("Code Agent横向测评文章发布工具")
    print("=" * 50)
    
    config = load_config()
    wechat_config = config.get("wechat", {})
    app_id = wechat_config.get("app_id", "")
    app_secret = wechat_config.get("app_secret", "")
    
    if not app_id or app_id == "your_app_id_here":
        print("\n[ERROR] 微信公众号未配置")
        return
    
    # 读取HTML文件内容
    html_file = "output/ai_ppt_2026.html"
    if not os.path.exists(html_file):
        print(f"[ERROR] HTML file not found: {html_file}")
        return
    
    # 使用UTF-8编码读取
    with open(html_file, "r", encoding="utf-8") as f:
        article_content = f.read()
    
    article_title = "2026 AI PPT生成工具横评 六大工具对比"
    article_author = "AI观察"
    
    print(f"\n[Title] 文章标题: {article_title}")
    print(f"[Author] 作者: {article_author}")
    print(f"[Content] 内容长度: {len(article_content)} 字符")
    
    try:
        print("\n[Step 1] 获取 access_token...")
        token = get_access_token(app_id, app_secret)
        print("[OK] access_token 获取成功")
        
        print("\n[Step 2] 使用已有封面图...")
        cover_path = "cover.png"
        
        print("\n[Step 3] 上传封面图...")
        thumb_media_id = upload_thumb(token, cover_path)
        print(f"[OK] 封面图上传成功")
        
        print("\n[Step 4] 创建草稿...")
        media_id = create_draft(
            token=token,
            title=article_title,
            content=article_content,
            thumb_media_id=thumb_media_id,
            author=article_author
        )
        print(f"[OK] 草稿创建成功！media_id: {media_id}")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] 文章已成功发布到微信公众号草稿箱！")
        print("[Action] 请登录 mp.weixin.qq.com 查看并发布文章")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n[ERROR] 发布失败: {e}")


if __name__ == "__main__":
    main()