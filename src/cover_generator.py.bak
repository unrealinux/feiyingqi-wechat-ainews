"""
Cover Image Generator - 公众号封面图生成器 (优化版)
优化点：字体缓存、自定义配色、文本换行、圆角背景、渐变文字等
"""
import os
import random
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from src.logger import get_logger


logger = get_logger(__name__)

# Try import PIL
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = ImageDraw = ImageFont = ImageFilter = None


class CoverGenerator:
    """封面图生成器 - 优化版"""
    
    # 微信公众号封面尺寸
    WECHAT_COVER_WIDTH = 900
    WECHAT_COVER_HEIGHT = 383
    
    # 默认AI风格颜色方案 (赛博朋克/科技感)
    DEFAULT_COLOR_SCHEMES = [
        # 赛博蓝
        {"bg": "#0a0a1a", "accent": "#0d1b2a", "text": "#e0e0ff", "highlight": "#00f5ff", "secondary": "#0066ff"},
        # 神经网络紫
        {"bg": "#120a1f", "accent": "#1a0a2e", "text": "#f0e0ff", "highlight": "#bf00ff", "secondary": "#8000ff"},
        # 数据流青
        {"bg": "#0a1520", "accent": "#0f2027", "text": "#d0fff0", "highlight": "#00ffa3", "secondary": "#00cc88"},
        # 机械橙
        {"bg": "#1a1008", "accent": "#2d1810", "text": "#fff0d0", "highlight": "#ff6600", "secondary": "#ff9933"},
        # 量子粉
        {"bg": "#1a0a1a", "accent": "#2d0f2d", "text": "#ffd0f0", "highlight": "#ff00aa", "secondary": "#ff66cc"},
        # 深空蓝
        {"bg": "#0a0f1a", "accent": "#0f1a2d", "text": "#d0e0ff", "highlight": "#4d79ff", "secondary": "#3366ff"},
        # 生态绿
        {"bg": "#0a1a10", "accent": "#0f2d1a", "text": "#d0ffd0", "highlight": "#00ff66", "secondary": "#66ff00"},
        # 极光白
        {"bg": "#151520", "accent": "#1f1f2d", "text": "#ffffff", "highlight": "#aaddff", "secondary": "#6699cc"},
    ]
    
    # 风格类型
    STYLE_NEURAL = "neural"      # 神经网络
    STYLE_CIRCUIT = "circuit"   # 电路板
    STYLE_BINARY = "binary"     # 二进制流
    STYLE_PARTICLES = "particles"  # 粒子效果
    STYLE_GRID = "grid"         # 科技网格
    
    def __init__(self, custom_color_schemes: Optional[List[Dict]] = None):
        self.width = self.WECHAT_COVER_WIDTH
        self.height = self.WECHAT_COVER_HEIGHT
        
        # 合并默认和自定义配色方案
        self.color_schemes = self.DEFAULT_COLOR_SCHEMES.copy()
        if custom_color_schemes:
            self.color_schemes.extend(custom_color_schemes)
        
        # 字体缓存
        self._font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
        
        # 预加载常用字体路径
        self._font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]
    
    def generate_cover(
        self,
        title: str,
        output_path: str = "output/cover.png",
        style: str = "auto",
        bg_image_path: Optional[str] = None,
        bg_blend_alpha: float = 0.3,
        rounded_corners: int = 0,
        text_wrap_width: int = 30,
        gradient_text: bool = False
    ) -> str:
        """生成封面图
        
        Args:
            title: 文章标题
            output_path: 输出路径
            style: 风格 (auto, neural, circuit, binary, particles, grid)
            bg_image_path: 背景图片路径 (可选)
            bg_blend_alpha: 背景图混合透明度 (0-1)
            rounded_corners: 圆角半径 (0表示无圆角)
            text_wrap_width: 文本换行宽度（字符数）
            gradient_text: 是否使用渐变文字
        """
        if not PIL_AVAILABLE:
            logger.error("PIL not installed. Run: pip install Pillow")
            return ""
        
        try:
            # 选择颜色方案
            color_scheme = random.choice(self.color_schemes)
            
            # 如果是auto，随机选择风格
            if style == "auto":
                style = random.choice([
                    self.STYLE_NEURAL, 
                    self.STYLE_CIRCUIT, 
                    self.STYLE_BINARY,
                    self.STYLE_PARTICLES,
                    self.STYLE_GRID
                ])
            
            # 创建基础图片
            if bg_image_path and os.path.exists(bg_image_path):
                # 如果有背景图片，先加载它
                bg_img = Image.open(bg_image_path).convert('RGB')
                bg_img = bg_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                img = Image.new('RGB', (self.width, self.height), color_scheme["bg"])
                # 混合背景图和纯色背景
                img = Image.blend(img, bg_img, bg_blend_alpha)
            else:
                img = Image.new('RGB', (self.width, self.height), color_scheme["bg"])
            
            draw = ImageDraw.Draw(img)
            
            # 绘制AI风格背景
            self._draw_ai_background(draw, color_scheme, style)
            
            # 添加标题文字（支持换行）
            self._draw_title(draw, title, color_scheme, text_wrap_width, gradient_text)
            
            # 添加AI装饰元素
            self._draw_ai_decorations(draw, color_scheme, style)
            
            # 应用圆角（如果需要）
            if rounded_corners > 0:
                img = self._apply_rounded_corners(img, rounded_corners, color_scheme["bg"])
            
            # 保存图片
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'PNG', quality=95)
            
            logger.info(f"Cover generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate cover: {e}")
            return ""
    
    def _draw_ai_background(self, draw, colors: dict, style: str):
        """绘制AI风格背景"""
        if style == self.STYLE_NEURAL:
            self._draw_neural_background(draw, colors)
        elif style == self.STYLE_CIRCUIT:
            self._draw_circuit_background(draw, colors)
        elif style == self.STYLE_BINARY:
            self._draw_binary_background(draw, colors)
        elif style == self.STYLE_PARTICLES:
            self._draw_particles_background(draw, colors)
        else:
            self._draw_grid_background(draw, colors)
    
    def _draw_neural_background(self, draw, colors: dict):
        """神经网络背景"""
        bg_color = colors["bg"]
        accent = colors["accent"]
        highlight = colors["highlight"]
        
        # 基础渐变
        for i in range(0, self.height, 4):
            alpha = int(255 * (1 - i / self.height) * 0.15)
            draw.line([(0, i), (self.width, i)], fill=accent)
        
        # 神经网络节点和连线
        nodes = []
        for _ in range(15):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            nodes.append((x, y))
            # 绘制节点（发光点）
            radius = random.randint(2, 6)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=highlight)
        
        # 绘制节点间的连线
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:i+4]:  # 每个节点连接2-3个
                dist = math.sqrt((n1[0]-n2[0])**2 + (n1[1]-n2[1])**2)
                if dist < 300:  # 只连接近的点
                    draw.line([n1, n2], fill=highlight, width=1)
    
    def _draw_circuit_background(self, draw, colors: dict):
        """电路板背景"""
        bg_color = colors["bg"]
        accent = colors["accent"]
        highlight = colors["highlight"]
        
        # 基础背景
        draw.rectangle([(0, 0), (self.width, self.height)], fill=bg_color)
        
        # 绘制电路走线
        for _ in range(20):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            direction = random.choice(['h', 'v'])
            length = random.randint(50, 200)
            
            if direction == 'h':
                draw.line([(x, y), (x+length, y)], fill=accent, width=2)
                # 添加焊点
                draw.ellipse([x-2, y-2, x+2, y+2], fill=highlight)
                draw.ellipse([x+length-2, y-2, x+length+2, y+2], fill=highlight)
            else:
                draw.line([(x, y), (x, y+length)], fill=accent, width=2)
                draw.ellipse([x-2, y-2, x+2, y+2], fill=highlight)
                draw.ellipse([x-2, y+length-2, x+2, y+length+2], fill=highlight)
    
    def _draw_binary_background(self, draw, colors: dict):
        """二进制流背景"""
        highlight = colors["highlight"]
        secondary = colors["secondary"]
        
        # 随机生成二进制数字流
        for _ in range(30):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            binary = ''.join(random.choice(['0', '1']) for _ in range(random.randint(5, 15)))
            font = self._load_font(10)
            
            # 随机选择颜色
            color = random.choice([highlight, secondary, colors["accent"]])
            draw.text((x, y), binary, font=font, fill=color)
    
    def _draw_particles_background(self, draw, colors: dict):
        """粒子效果背景"""
        highlight = colors["highlight"]
        secondary = colors["secondary"]
        
        # 随机绘制发光粒子
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 4)
            
            # 主粒子
            draw.ellipse([x-size, y-size, x+size, y+size], fill=highlight)
            
            # 随机添加光晕
            if random.random() > 0.7:
                glow_size = size * 3
                draw.ellipse([x-glow_size, y-glow_size, x+glow_size, y+glow_size], 
                           fill=secondary)
    
    def _draw_grid_background(self, draw, colors: dict):
        """科技网格背景"""
        accent = colors["accent"]
        highlight = colors["highlight"]
        
        # 绘制网格线
        spacing = 40
        
        # 垂直线
        for x in range(0, self.width, spacing):
            draw.line([(x, 0), (x, self.height)], fill=accent, width=1)
        
        # 水平线
        for y in range(0, self.height, spacing):
            draw.line([(0, y), (self.width, y)], fill=accent, width=1)
        
        # 添加一些随机亮点
        for _ in range(20):
            x = random.randint(0, self.width) // spacing * spacing
            y = random.randint(0, self.height) // spacing * spacing
            draw.ellipse([x-2, y-2, x+2, y+2], fill=highlight)
    
    def _draw_title(self, draw, title: str, colors: dict, wrap_width: int, gradient_text: bool):
        """绘制标题（支持换行和渐变）"""
        title = title.strip()
        
        # 文本换行处理
        if len(title) > wrap_width:
            # 按空格分割单词，然后根据宽度换行
            words = title.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + len(current_line) <= wrap_width:
                    current_line.append(word)
                    current_length += len(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            title = '\n'.join(lines[:3])  # 最多显示3行
        elif len(title) > 30:
            # 如果不换行但太长，截断
            title = title[:27] + "..."
        
        text_color = colors["text"]
        
        # 加载字体
        font = self._load_font(48)  # 稍微减小字体以适应换行
        
        # 计算文字位置（居中对齐多行文本）
        lines = title.split('\n')
        line_heights = []
        max_line_width = 0
        
        for line in lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
            except:
                line_width = len(line) * 24
                line_height = 24
            
            line_heights.append(line_height)
            max_line_width = max(max_line_width, line_width)
        
        total_height = sum(line_heights) + (len(lines) - 1) * 8  # 行间距8像素
        
        # 垂直居中
        y_start = (self.height - total_height) // 2
        
        # 绘制每一行
        for i, line in enumerate(lines):
            # 计算当前行的x位置（水平居中）
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
            except:
                line_width = len(line) * 24
            
            x = (self.width - line_width) // 2
            y = y_start + sum(line_heights[:i]) + i * 8
            
            if gradient_text and len(line) > 0:
                self._draw_gradient_text(draw, line, x, y, font, colors)
            else:
                # 绘制发光效果（多层阴影）
                shadow_colors = [
                    colors["accent"],
                    colors.get("secondary", colors["accent"]),
                    colors["bg"]
                ]
                
                for i, shadow in enumerate(shadow_colors):
                    offset = (i + 1) * 2
                    draw.text((x + offset, y + offset), line, font=font, fill=shadow)
                
                # 绘制主标题
                draw.text((x, y), line, font=font, fill=text_color)
    
    def _draw_gradient_text(self, draw, text: str, x: int, y: int, font: ImageFont.FreeTypeFont, colors: dict):
        """绘制渐变文字"""
        # 创建渐变遮罩
        text_width, text_height = draw.textsize(text, font=font)
        
        # 创建临时图片用于渐变
        temp_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        temp_draw.text((0, 0), text, font=font, fill=(255, 255, 255, 255))
        
        # 创建渐变（从highlight到secondary）
        gradient_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        for i in range(text_height):
            ratio = i / text_height if text_height > 0 else 0
            # 从highlight颜色过渡到secondary颜色
            r1, g1, b1 = self._hex_to_rgb(colors["highlight"])
            r2, g2, b2 = self._hex_to_rgb(colors["secondary"])
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            for j in range(text_width):
                gradient_img.putpixel((j, i), (r, g, b, 255))
        
        # 应用渐变到文字
        gradient_text_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        gradient_text_img.paste(gradient_img, (0, 0))
        gradient_text_img.putalpha(temp_img)
        
        # 绘制阴影效果
        shadow_offset = 2
        shadow_img = Image.new('RGBA', (text_width + shadow_offset*2, text_height + shadow_offset*2), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        
        # 创建阴影渐变（使用accent色）
        for i in range(text_height + shadow_offset*2):
            ratio = i / (text_height + shadow_offset*2) if (text_height + shadow_offset*2) > 0 else 0
            r, g, b = self._hex_to_rgb(colors["accent"])
            alpha = int(100 * (1 - ratio))  # 逐渐淡出的阴影
            for j in range(text_width + shadow_offset*2):
                shadow_img.putpixel((j, i), (r, g, b, alpha))
        
        # 应用文字遮罩到阴影
        shadow_img.putalpha(temp_img)
        
        # 粘贴阴影和渐变文字
        draw.bitmap((x - shadow_offset, y - shadow_offset), shadow_img, fill=(255, 255, 255))
        draw.bitmap((x, y), gradient_text_img, fill=(255, 255, 255))
    
    def _draw_ai_decorations(self, draw, colors: dict, style: str):
        """绘制AI装饰元素"""
        highlight = colors["highlight"]
        secondary = colors["secondary"]
        
        # 顶部装饰条
        draw.rectangle([(0, 0), (self.width, 4)], fill=highlight)
        
        # 底部装饰条
        draw.rectangle([(0, self.height-4), (self.width, self.height)], fill=highlight)
        
        # 左侧AI图标
        self._draw_ai_icon(draw, 30, self.height//2, highlight, size=25)
        
        # 右侧装饰
        self._draw_ai_icon(draw, self.width - 55, self.height//2, secondary, size=25)
        
        # 角落装饰
        draw.ellipse([self.width - 80, 10, self.width - 40, 50], fill=highlight)
        draw.ellipse([40, self.height - 60, 70, self.height - 20], fill=secondary)
    
    def _draw_ai_icon(self, draw, x: int, y: int, color: str, size: int = 20):
        """绘制简单的AI图标（脑神经/芯片图案）"""
        # 外圈
        draw.ellipse([x-size, y-size, x+size, y+size], outline=color, width=2)
        
        # 内部节点
        center_size = size // 3
        draw.ellipse([x-center_size, y-center_size, x+center_size, y+center_size], fill=color)
        
        # 外部连接点
        for angle in [0, 90, 180, 270]:
            rad = math.radians(angle)
            nx = int(x + size * 0.7 * math.cos(rad))
            ny = int(y + size * 0.7 * math.sin(rad))
            draw.ellipse([nx-2, ny-2, nx+2, ny+2], fill=color)
            draw.line([x, y, nx, ny], fill=color, width=1)
    
    def _apply_rounded_corners(self, img: Image.Image, radius: int, bg_color: str) -> Image.Image:
        """应用圆角效果"""
        # 创建圆角遮罩
        mask = Image.new('L', (self.width, self.height), 0)
        draw = ImageDraw.Draw(mask)
        
        # 绘制圆角矩形
        draw.rounded_rectangle([(0, 0), (self.width, self.height)], radius=radius, fill=255)
        
        # 创建背景图片
        background = Image.new('RGB', (self.width, self.height), bg_color)
        
        # 将原图和背景图通过遮罩混合
        result = Image.composite(img, background, mask)
        return result
    
    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """加载字体（带缓存）"""
        # 查找第一个可用的字体路径
        font_path = None
        for path in self._font_paths:
            if os.path.exists(path):
                font_path = path
                break
        
        if font_path is None:
            # 如果没有找到任何字体，使用默认字体
            return ImageFont.load_default()
        
        # 使用缓存
        cache_key = (font_path, size)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        try:
            font = ImageFont.truetype(font_path, size)
            self._font_cache[cache_key] = font
            return font
        except:
            # 如果加载失败，返回默认字体
            return ImageFont.load_default()
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# 便捷函数
def generate_cover_image(
    title: str,
    output_path: str = "output/cover.png",
    style: str = "auto",
    **kwargs
) -> str:
    """生成封面图"""
    generator = CoverGenerator()
    return generator.generate_cover(title, output_path, style, **kwargs)


if __name__ == "__main__":
    import sys
    
    title = sys.argv[1] if len(sys.argv) > 1 else "AI News Cover"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/cover.png"
    style = sys.argv[3] if len(sys.argv) > 3 else "auto"
    
    result = generate_cover_image(title, output, style)
    print(f"Cover generated: {result}")
