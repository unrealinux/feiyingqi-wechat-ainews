"""
Cover Image Generator - 公众号封面图生成器 (优化版)
参考 FeiqingqiWechatMP 的 coverGenerator.js 实现

优化点：
1. 字体缓存、自定义配色、文本换行
2. 渐变背景 + 光晕效果 (参考JS版)
3. 暗角效果 (Vignette)
4. 多层文字叠加 + 阴影
5. AI图片生成支持 (OpenAI/GLM)
6. 智能缓存系统
7. 内容感知风格选择
"""
import os
import random
import math
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from io import BytesIO

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
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]
        
        # 缓存目录 (参考FeiqingqiWechatMP)
        self.cache_dir = Path("cache/covers")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_cover(
        self,
        title: str,
        output_path: str = "output/cover.png",
        style: str = "auto",
        bg_image_path: Optional[str] = None,
        bg_blend_alpha: float = 0.3,
        rounded_corners: int = 0,
        text_wrap_width: int = 30,
        gradient_text: bool = False,
        use_cache: bool = True,
        add_vignette: bool = True
    ) -> str:
        """生成封面图 (优化版，参考FeiqingqiWechatMP)
        
        Args:
            title: 文章标题
            output_path: 输出路径
            style: 风格 (auto, neural, circuit, binary, particles, grid)
            bg_image_path: 背景图片路径 (可选)
            bg_blend_alpha: 背景图混合透明度 (0-1)
            rounded_corners: 圆角半径 (0表示无圆角)
            text_wrap_width: 文本换行宽度（字符数）
            gradient_text: 是否使用渐变文字
            use_cache: 是否使用缓存
            add_vignette: 是否添加暗角效果
        """
        if not PIL_AVAILABLE:
            logger.error("PIL not installed. Run: pip install Pillow")
            return ""
        
        try:
            # 检查缓存
            if use_cache:
                cache_key = self._get_cache_key(title, style)
                cached_data = self._get_cached_cover(cache_key)
                if cached_data:
                    # 保存缓存的图片到输出路径
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(cached_data)
                    logger.info(f"使用缓存封面图: {output_path}")
                    return output_path
            
            # 选择颜色方案
            color_scheme = random.choice(self.color_schemes)
            
            # 如果是auto，根据内容智能选择风格
            if style == "auto":
                style = self.select_style_by_content(title)
                logger.info(f"智能选择风格: {style}")
            
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
            
            # 添加暗角效果 (参考FeiqingqiWechatMP)
            if add_vignette:
                img = self._add_vignette(img, intensity=0.3)
            
            # 保存图片
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'PNG', quality=95)
            
            # 同时保存到缓存
            if use_cache:
                with open(output_path, "rb") as f:
                    self._save_to_cache(cache_key, f.read())
            
            logger.info(f"封面图生成完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"封面图生成失败: {e}")
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
    
    def _get_cache_key(self, title: str, style: str = "auto") -> str:
        """生成缓存键 (参考FeiqingqiWechatMP)"""
        key_string = f"{title}|{style}|{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_cover(self, cache_key: str) -> Optional[bytes]:
        """获取缓存的封面图"""
        cache_path = self.cache_dir / f"{cache_key}.png"
        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    return f.read()
            except Exception:
                pass
        return None
    
    def _save_to_cache(self, cache_key: str, image_data: bytes):
        """保存封面图到缓存"""
        cache_path = self.cache_dir / f"{cache_key}.png"
        try:
            with open(cache_path, "wb") as f:
                f.write(image_data)
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")
    
    def _add_vignette(self, img: Image.Image, intensity: float = 0.4) -> Image.Image:
        """添加暗角效果 (参考FeiqingqiWechatMP的_createVignette)"""
        if not PIL_AVAILABLE:
            return img
        
        # 创建暗角遮罩
        vignette = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(vignette)
        
        # 绘制径向渐变暗角
        center_x, center_y = img.width // 2, img.height // 2
        max_radius = max(img.width, img.height)
        
        for i in range(20, 0, -1):
            radius = int(max_radius * i / 20)
            opacity = int(255 * intensity * (20 - i) / 20)
            draw.ellipse(
                [(center_x - radius, center_y - radius),
                 (center_x + radius, center_y + radius)],
                fill=(0, 0, 0, opacity)
            )
        
        # 合成图像
        img = img.convert('RGBA')
        result = Image.alpha_composite(img, vignette)
        return result.convert('RGB')
    
    def _create_gradient_with_glow(self, colors: List[str], width: int, height: int) -> Image.Image:
        """创建带光晕效果的渐变背景 (参考FeiqingqiWechatMP)"""
        if not PIL_AVAILABLE:
            return None
        
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # 转换颜色
        rgb_colors = [self._hex_to_rgb(c) for c in colors]
        
        # 创建线性渐变（从左上到右下）
        for y in range(height):
            for x in range(width):
                # 计算渐变位置（对角线方向）
                t = (x / width + y / height) / 2
                
                # 在颜色之间插值
                if len(rgb_colors) == 2:
                    r = int(rgb_colors[0][0] + (rgb_colors[1][0] - rgb_colors[0][0]) * t)
                    g = int(rgb_colors[0][1] + (rgb_colors[1][1] - rgb_colors[0][1]) * t)
                    b = int(rgb_colors[0][2] + (rgb_colors[1][2] - rgb_colors[0][2]) * t)
                else:
                    # 多色渐变
                    segment = t * (len(rgb_colors) - 1)
                    idx = int(segment)
                    if idx >= len(rgb_colors) - 1:
                        r, g, b = rgb_colors[-1]
                    else:
                        local_t = segment - idx
                        r = int(rgb_colors[idx][0] + (rgb_colors[idx+1][0] - rgb_colors[idx][0]) * local_t)
                        g = int(rgb_colors[idx][1] + (rgb_colors[idx+1][1] - rgb_colors[idx][1]) * local_t)
                        b = int(rgb_colors[idx][2] + (rgb_colors[idx+1][2] - rgb_colors[idx][2]) * local_t)
                
                img.putpixel((x, y), (r, g, b))
        
        # 添加光晕效果 (参考FeiqingqiWechatMP)
        center_x, center_y = width * 0.3, height * 0.5
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist < max_dist * 0.5:
                    intensity = 1 - (dist / (max_dist * 0.5))
                    intensity = intensity * 0.15  # 控制光晕强度
                    
                    r, g, b = img.getpixel((x, y))
                    r = min(255, int(r + (255 - r) * intensity))
                    g = min(255, int(g + (255 - g) * intensity))
                    b = min(255, int(b + (255 - b) * intensity))
                    img.putpixel((x, y), (r, g, b))
        
        return img
    
    def select_style_by_content(self, title: str) -> str:
        """根据内容智能选择风格 (参考FeiqingqiWechatMP的_selectWineElement)"""
        text = title.lower()
        
        # 关键词映射
        style_keywords = {
            "neural": ["神经", "深度学习", "模型", "训练", "neural", "deep learning", "model"],
            "circuit": ["芯片", "硬件", "处理器", "算力", "chip", "hardware", "processor"],
            "binary": ["数据", "算法", "代码", "编程", "data", "algorithm", "code"],
            "particles": ["量子", "物理", "粒子", "quantum", "physics", "particle"],
            "grid": ["网格", "架构", "系统", "网络", "architecture", "system", "network"]
        }
        
        # 计算每个风格的匹配分数
        scores = {}
        for style, keywords in style_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[style] = score
        
        # 返回得分最高的风格，如果没有匹配则随机选择
        best_style = max(scores, key=scores.get)
        if scores[best_style] == 0:
            return random.choice(list(style_keywords.keys()))
        return best_style
    
    def generate_with_ai(self, title: str, api_key: str = "", 
                        provider: str = "openai") -> Optional[bytes]:
        """使用AI生成封面图 (参考FeiqingqiWechatMP的ai-image-generator.js)"""
        if not api_key:
            logger.warning("未配置AI API密钥，跳过AI生成")
            return None
        
        try:
            import requests
            
            prompt = f"""Create a professional WeChat article cover image for AI technology news.
            
Title: {title}
Style: Modern tech, dark gradient, professional, minimalist
Requirements:
- 900x383 aspect ratio (2.35:1)
- Dark blue/purple color palette
- Abstract tech elements (neural network, circuit patterns)
- Clean, modern design suitable for tech news
- No text in image (text will be added separately)"""
            
            if provider == "openai":
                return self._generate_with_openai(title, api_key, prompt)
            elif provider == "glm":
                return self._generate_with_glm(title, api_key, prompt)
            else:
                logger.warning(f"不支持的AI提供商: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"AI封面生成失败: {e}")
            return None
    
    def _generate_with_openai(self, title: str, api_key: str, prompt: str) -> Optional[bytes]:
        """使用OpenAI DALL-E生成封面"""
        import requests
        import base64
        
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "dall-e-3",
                "prompt": prompt,
                "size": "1792x1024",
                "quality": "standard",
                "n": 1,
                "response_format": "b64_json"
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            image_data = base64.b64decode(data["data"][0]["b64_json"])
            
            # 调整大小
            img = Image.open(BytesIO(image_data))
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # 转换为bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        else:
            logger.error(f"OpenAI API错误: {response.status_code}")
            return None
    
    def _generate_with_glm(self, title: str, api_key: str, prompt: str) -> Optional[bytes]:
        """使用智谱AI GLM生成封面"""
        import requests
        
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
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            image_url = data["data"][0]["url"]
            
            # 下载图像
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                img = Image.open(BytesIO(img_response.content))
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                return buffer.getvalue()
        
        return None


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


def generate_smart_cover(
    title: str,
    output_path: str = "output/cover.png",
    ai_api_key: str = "",
    ai_provider: str = "openai",
    **kwargs
) -> str:
    """智能生成封面图 - 优先使用AI，失败则使用本地生成
    
    参考 FeiqingqiWechatMP 的 enhanced-cover-generator.js 实现
    """
    generator = CoverGenerator()
    
    # 尝试AI生成
    if ai_api_key:
        logger.info("尝试AI生成封面...")
        ai_cover = generator.generate_with_ai(title, ai_api_key, ai_provider)
        if ai_cover:
            # 保存AI生成的封面
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(ai_cover)
            logger.info(f"AI封面生成成功: {output_path}")
            return output_path
        logger.warning("AI生成失败，使用本地生成...")
    
    # 使用本地生成
    return generator.generate_cover(title, output_path, **kwargs)


if __name__ == "__main__":
    import sys
    
    title = sys.argv[1] if len(sys.argv) > 1 else "AI热点速递 | 2026年3月22日"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/cover.png"
    style = sys.argv[3] if len(sys.argv) > 3 else "auto"
    
    result = generate_cover_image(title, output, style)
    print(f"封面图生成完成: {result}")
