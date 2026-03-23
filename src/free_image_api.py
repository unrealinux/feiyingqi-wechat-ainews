#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
免费图片API模块 - 用于获取科技风格的封面图

支持的API：
1. Unsplash - 高质量免费图片（50次/小时免费）
2. Pexels - 免费商用图片（200次/小时免费）
3. Pixabay - 免费图片（100次/分钟免费）
"""
import os
import requests
from typing import Optional, List, Dict
from pathlib import Path


class FreeImageAPI:
    """免费图片API - 获取科技风格封面图"""
    
    # AI科技相关的搜索关键词（更精准，按优先级排序）
    AI_KEYWORDS = {
        "datacenter": [
            "AI neural network visualization",  # 神经网络可视化
            "deep learning technology",          # 深度学习技术
            "artificial intelligence brain",     # AI大脑
            "machine learning data flow",        # 机器学习数据流
            "AI data center blue lights"         # AI数据中心
        ],
        "chip": [
            "AI chip processor technology",
            "artificial intelligence microchip",
            "neural network circuit board",
            "deep learning GPU"
        ],
        "robot": [
            "artificial intelligence robot",
            "AI humanoid robot",
            "machine learning automation",
            "intelligent robot technology"
        ],
        "neural": [
            "neural network visualization",
            "deep learning artificial brain",
            "AI neural connections",
            "machine learning data flow"
        ],
        "office": [
            "AI technology office",
            "artificial intelligence workspace",
            "smart office technology",
            "digital transformation office"
        ]
    }
    
    # 通用AI关键词（兜底）
    GENERAL_AI_KEYWORDS = [
        "artificial intelligence technology",
        "AI machine learning",
        "deep learning neural network",
        "futuristic AI technology",
        "blue technology abstract AI"
    ]
    
    # 不需要代理的API
    NO_PROXY_APIS = ["pexels", "pixabay"]
    
    def __init__(self, config: Dict = None, proxy: str = None):
        """
        初始化免费图片API
        
        Args:
            config: API配置字典
                {
                    "unsplash": "your_access_key",
                    "pexels": "your_api_key",
                    "pixabay": "your_api_key"
                }
            proxy: 代理地址
        """
        self.config = config or {}
        self.proxy = proxy
        self.output_dir = Path("output/covers")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def search_image(self, 
                     query: str = "artificial intelligence",
                     provider: str = "auto",
                     use_proxy: bool = False) -> Optional[bytes]:
        """
        搜索并下载图片
        
        Args:
            query: 搜索关键词
            provider: API提供商 (auto, unsplash, pexels, pixabay)
            use_proxy: 是否使用代理（Pexels/Pixabay国内可直接访问，无需代理）
        
        Returns:
            图片字节数据，失败返回None
        """
        # 自动选择可用的API
        if provider == "auto":
            provider = self._select_available_provider()
            if not provider:
                print("[Error] 未配置任何免费图片API")
                return None
        
        print(f"[Free Image] 使用 {provider} 搜索图片: {query}")
        
        # 调用对应的API
        providers = {
            "unsplash": self._search_unsplash,
            "pexels": self._search_pexels,
            "pixabay": self._search_pixabay,
        }
        
        search_func = providers.get(provider)
        if not search_func:
            print(f"[Error] 不支持的API: {provider}")
            return None
        
        return search_func(query, use_proxy)
    
    def search_tech_image(self, style: str = "datacenter", use_proxy: bool = False) -> Optional[bytes]:
        """
        搜索AI科技风格图片（优化版）
        
        Args:
            style: 风格 (datacenter, chip, robot, neural, office)
            use_proxy: 是否使用代理
        
        Returns:
            图片字节数据
        """
        # 获取该风格的关键词列表
        keywords_list = self.AI_KEYWORDS.get(style, self.AI_KEYWORDS["datacenter"])
        
        # 尝试每个关键词，直到找到合适的图片
        for query in keywords_list:
            print(f"[Search] 尝试关键词: {query}")
            image_data = self.search_image(query, use_proxy=use_proxy)
            if image_data:
                return image_data
        
        # 如果都失败，尝试通用AI关键词
        print("[Search] 尝试通用AI关键词...")
        for query in self.GENERAL_AI_KEYWORDS:
            image_data = self.search_image(query, use_proxy=use_proxy)
            if image_data:
                return image_data
        
        return None
    
    def _select_available_provider(self) -> Optional[str]:
        """选择可用的API提供商"""
        providers = [
            "unsplash",
            "pexels",
            "pixabay"
        ]
        
        for provider in providers:
            if self.config.get(provider):
                return provider
        
        return None
    
    # ==================== Unsplash API ====================
    def _search_unsplash(self, query: str, use_proxy: bool = False) -> Optional[bytes]:
        """
        使用Unsplash搜索图片
        
        注册地址: https://unsplash.com/developers
        免费额度: 50次/小时
        注意: Unsplash需要代理访问
        """
        access_key = self.config.get("unsplash")
        if not access_key:
            print("[Error] 未配置Unsplash API密钥")
            return None
        
        proxies = {"http": self.proxy, "https": self.proxy} if use_proxy and self.proxy else None
        
        try:
            # 搜索图片
            response = requests.get(
                "https://api.unsplash.com/search/photos",
                headers={
                    "Authorization": f"Client-ID {access_key}",
                    "Accept-Version": "v1"
                },
                params={
                    "query": query,
                    "per_page": 5,
                    "orientation": "landscape"
                },
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    # 获取图片URL
                    result = data["results"][0]
                    image_url = result["urls"]["regular"]
                    
                    print(f"[Info] 找到图片: {result.get('description', 'N/A')}")
                    print(f"[Info] 摄影师: {result.get('user', {}).get('name', 'N/A')}")
                    
                    # 下载图片
                    img_response = requests.get(
                        image_url,
                        proxies=proxies,
                        timeout=60
                    )
                    
                    if img_response.status_code == 200:
                        print("[OK] Unsplash 图片下载成功")
                        return img_response.content
            else:
                print(f"[Error] Unsplash API错误: {response.status_code}")
                
        except Exception as e:
            print(f"[Error] Unsplash搜索失败: {e}")
        
        return None
    
    # ==================== Pexels API ====================
    def _search_pexels(self, query: str, use_proxy: bool = False) -> Optional[bytes]:
        """
        使用Pexels搜索图片
        
        注册地址: https://www.pexels.com/api/
        免费额度: 200次/小时
        注意: Pexels国内可直接访问，无需代理
        """
        api_key = self.config.get("pexels")
        if not api_key:
            print("[Error] 未配置Pexels API密钥")
            return None
        
        try:
            # 搜索图片 - Pexels国内可直接访问，不使用代理
            response = requests.get(
                "https://api.pexels.com/v1/search",
                headers={
                    "Authorization": api_key
                },
                params={
                    "query": query,
                    "per_page": 5,  # 获取更多结果以选择最佳图片
                    "orientation": "landscape"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("photos") and len(data["photos"]) > 0:
                    # 选择第一张图片（通常是最佳匹配）
                    photo = data["photos"][0]
                    image_url = photo["src"]["large"]
                    
                    print(f"[Info] 找到图片: {photo.get('alt', 'N/A')}")
                    print(f"[Info] 摄影师: {photo.get('photographer', 'N/A')}")
                    
                    # 下载图片 - 也不使用代理
                    img_response = requests.get(
                        image_url,
                        timeout=60
                    )
                    
                    if img_response.status_code == 200:
                        print("[OK] Pexels 图片下载成功")
                        return img_response.content
            else:
                print(f"[Error] Pexels API错误: {response.status_code}")
                
        except Exception as e:
            print(f"[Error] Pexels搜索失败: {e}")
        
        return None
    
    # ==================== Pixabay API ====================
    def _search_pixabay(self, query: str, use_proxy: bool = False) -> Optional[bytes]:
        """
        使用Pixabay搜索图片
        
        注册地址: https://pixabay.com/api/docs/
        免费额度: 100次/分钟
        注意: Pixabay国内可直接访问，无需代理
        """
        api_key = self.config.get("pixabay")
        if not api_key:
            print("[Error] 未配置Pixabay API密钥")
            return None
        
        try:
            # 搜索图片 - Pixabay国内可直接访问，不使用代理
            response = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": api_key,
                    "q": query,
                    "per_page": 5,
                    "orientation": "horizontal",
                    "image_type": "photo",
                    "min_width": 1920,
                    "safesearch": "true"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("hits") and len(data["hits"]) > 0:
                    # 获取图片URL
                    hit = data["hits"][0]
                    image_url = hit["largeImageURL"]
                    
                    print(f"[Info] 找到图片: {hit.get('tags', 'N/A')}")
                    
                    # 下载图片 - 也不使用代理
                    img_response = requests.get(
                        image_url,
                        timeout=60
                    )
                    
                    if img_response.status_code == 200:
                        print("[OK] Pixabay 图片下载成功")
                        return img_response.content
            else:
                print(f"[Error] Pixabay API错误: {response.status_code}")
                
        except Exception as e:
            print(f"[Error] Pixabay搜索失败: {e}")
        
        return None


def generate_cover_from_free_api(
    title: str,
    style: str = "datacenter",
    output_path: str = "cover.png",
    config: Dict = None,
    proxy: str = None
) -> Optional[str]:
    """
    使用免费图片API生成封面图
    
    Args:
        title: 文章标题
        style: 风格
        output_path: 输出路径
        config: API配置
        proxy: 代理地址
    
    Returns:
        封面图路径，失败返回None
    """
    api = FreeImageAPI(config, proxy)
    
    # 搜索科技风格图片
    image_data = api.search_tech_image(style)
    
    if not image_data:
        print("[Warning] 未找到合适的图片，尝试其他关键词...")
        # 尝试通用关键词
        image_data = api.search_image("technology abstract blue")
    
    if image_data:
        # 保存原始图片
        original_path = "output/free_image_original.png"
        os.makedirs("output", exist_ok=True)
        with open(original_path, "wb") as f:
            f.write(image_data)
        
        # 调整大小为微信封面尺寸
        resized_path = resize_to_wechat_cover(original_path, output_path)
        
        # 添加文字叠加
        add_text_overlay(resized_path, title)
        
        return output_path
    
    return None


def resize_to_wechat_cover(input_path: str, output_path: str = "cover.png") -> str:
    """调整图片为微信封面尺寸 (900x383)"""
    try:
        from PIL import Image
        
        img = Image.open(input_path)
        
        # 计算裁剪比例
        target_ratio = 900 / 383  # 约2.35:1
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
        img = img.resize((900, 383), Image.Resampling.LANCZOS)
        img.save(output_path, "PNG")
        print(f"[OK] 封面图已调整大小: {output_path}")
        return output_path
        
    except ImportError:
        # 如果没有PIL，直接复制
        import shutil
        shutil.copy(input_path, output_path)
        return output_path


def add_text_overlay(image_path: str, title: str, date: str = None):
    """添加文字叠加层"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.open(image_path)
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
        
        # 创建半透明遮罩
        from PIL import ImageFilter
        
        # 添加底部渐变遮罩
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # 渐变遮罩
        for y in range(250, img.height):
            alpha = int(180 * (y - 250) / (img.height - 250))
            overlay_draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))
        
        # 合成遮罩
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
            # 主文字（白色）
            draw.text((30, y_start + i * 38), line, fill=(255, 255, 255, 240), font=font_title)
        
        # 绘制日期
        if date:
            draw.text(
                (img.width - 30, img.height - 25),
                date,
                fill=(255, 255, 255, 200),
                font=font_date,
                anchor="rs"
            )
        
        # 转换为RGB并保存
        img = img.convert('RGB')
        img.save(image_path, "PNG")
        print(f"[OK] 文字叠加完成: {image_path}")
        
    except ImportError:
        print("[Warning] PIL未安装，跳过文字叠加")


if __name__ == "__main__":
    # 测试
    print("=" * 50)
    print("免费图片API测试")
    print("=" * 50)
    
    # 测试配置（需要用户自行配置API密钥）
    config = {
        # "unsplash": "your_access_key",
        # "pexels": "your_api_key",
        # "pixabay": "your_api_key"
    }
    
    proxy = "socks5://127.0.0.1:10808"
    
    api = FreeImageAPI(config, proxy)
    
    # 测试搜索
    print("\n可用的API配置:")
    for provider in ["unsplash", "pexels", "pixabay"]:
        status = "已配置" if config.get(provider) else "未配置"
        print(f"  - {provider}: {status}")
