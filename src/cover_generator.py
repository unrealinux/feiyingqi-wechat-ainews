"""
Cover Image Generator - 公众号封面图生成器
支持AI生成和模板合成
"""
import os
import random
from datetime import datetime
from pathlib import Path

from src.logger import get_logger


logger = get_logger(__name__)

# Try import PIL
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = ImageDraw = ImageFont = None


class CoverGenerator:
    """封面图生成器"""
    
    # 微信公众号封面尺寸
    WECHAT_COVER_WIDTH = 900
    WECHAT_COVER_HEIGHT = 383
    
    # 颜色方案
    COLOR_SCHEMES = [
        {"bg": "#1a1a2e", "accent": "#0f3460", "text": "#ffffff", "highlight": "#00d4ff"},
        {"bg": "#2d1b69", "accent": "#4731d3", "text": "#ffffff", "highlight": "#8b5cf6"},
        {"bg": "#1e1e2f", "accent": "#2d2d44", "text": "#ffffff", "highlight": "#f59e0b"},
        {"bg": "#052e16", "accent": "#14532d", "text": "#ffffff", "highlight": "#10b981"},
        {"bg": "#2e1065", "accent": "#4c1d95", "text": "#ffffff", "highlight": "#ec4899"},
        {"bg": "#0c1929", "accent": "#1e3a5f", "text": "#ffffff", "highlight": "#3b82f6"},
        {"bg": "#18181b", "accent": "#27272a", "text": "#fafafa", "highlight": "#f472b6"},
        {"bg": "#1c1917", "accent": "#292524", "text": "#fef3c7", "highlight": "#fbbf24"},
    ]
    
    def __init__(self):
        self.width = self.WECHAT_COVER_WIDTH
        self.height = self.WECHAT_COVER_HEIGHT
    
    def generate_cover(
        self,
        title: str,
        output_path: str = "output/cover.png",
        style: str = "modern"
    ) -> str:
        """生成封面图"""
        if not PIL_AVAILABLE:
            logger.error("PIL not installed. Run: pip install Pillow")
            return ""
        
        try:
            # 选择颜色方案
            color_scheme = random.choice(self.COLOR_SCHEMES)
            
            # 创建图片
            img = Image.new('RGB', (self.width, self.height), color_scheme["bg"])
            draw = ImageDraw.Draw(img)
            
            # 绘制背景
            self._draw_background(draw, color_scheme)
            
            # 添加标题文字
            self._draw_title(draw, title, color_scheme)
            
            # 添加装饰元素
            self._draw_decorations(draw, color_scheme)
            
            # 保存图片
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'PNG', quality=95)
            
            logger.info(f"Cover generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate cover: {e}")
            return ""
    
    def _draw_background(self, draw, colors: dict):
        """绘制背景"""
        accent_color = colors["accent"]
        
        for i in range(0, self.height, 20):
            draw.rectangle(
                [(0, self.height - i - 20), (self.width, self.height - i)],
                fill=accent_color
            )
    
    def _draw_title(self, draw, title: str, colors: dict):
        """绘制标题"""
        title = title.strip()
        if len(title) > 30:
            title = title[:27] + "..."
        
        text_color = colors["text"]
        
        # 尝试加载字体
        font = self._load_font(48)
        info_font = self._load_font(18)
        
        # 计算文字位置（居中）
        try:
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = len(title) * 24
            text_height = 48
        
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        
        # 绘制阴影
        shadow_color = colors["accent"]
        draw.text((x + 2, y + 2), title, font=font, fill=shadow_color)
        
        # 绘制主标题
        draw.text((x, y), title, font=font, fill=text_color)
        
        # 添加底部信息
        date_str = datetime.now().strftime("%Y.%m.%d")
        info_text = f"AI前沿观察 · {date_str}"
        
        draw.text(
            (self.width // 2 - 80, self.height - 50),
            info_text,
            font=info_font,
            fill=colors["text"]
        )
    
    def _draw_decorations(self, draw, colors: dict):
        """绘制装饰元素"""
        highlight = colors["highlight"]
        
        # 顶部线条
        draw.line([(0, 0), (self.width, 0)], fill=highlight, width=3)
        
        # 底部线条
        draw.line([(0, self.height - 1), (self.width, self.height - 1)], fill=highlight, width=3)
        
        # 左侧装饰
        draw.line([(0, 0), (0, 80)], fill=highlight, width=5)
        
        # 圆形装饰
        draw.ellipse([self.width - 100, -30, self.width - 20, 50], fill=highlight)
        draw.ellipse([20, self.height - 60, 80, self.height - 20], fill=highlight)
    
    def _load_font(self, size: int):
        """加载字体"""
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    pass
        
        return ImageFont.load_default()


def generate_cover_image(
    title: str,
    output_path: str = "output/cover.png",
    style: str = "modern"
) -> str:
    """生成封面图的便捷函数"""
    generator = CoverGenerator()
    return generator.generate_cover(title, output_path, style)


if __name__ == "__main__":
    import sys
    
    title = sys.argv[1] if len(sys.argv) > 1 else "AI News Cover"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/cover.png"
    
    result = generate_cover_image(title, output)
    print(f"Cover generated: {result}")
