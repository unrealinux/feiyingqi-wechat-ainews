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
        add_vignette: bool = True,
        use_realistic_photo: bool = True  # 新增：使用写实照片背景
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
            
            # 优先使用真实照片背景（方案A）
            if use_realistic_photo:
                photo_bg = self._select_realistic_photo(title)
                if photo_bg and os.path.exists(photo_bg):
                    logger.info(f"使用真实照片背景: {photo_bg}")
                    return self._create_photo_cover(title, photo_bg, output_path)
            
            # 如果没有真实照片，尝试baoyu-image-gen生成
            try:
                import subprocess
                script_path = "C:/Users/Administrator/.claude/skills/baoyu-image-gen/scripts/main.ts"
                prompt = self._build_baoyu_prompt(title)
                
                cmd = [
                    "bun", script_path,
                    "--prompt", prompt,
                    "--image", output_path,
                    "--provider", "dashscope",
                    "--ar", "16:9"
                ]
                
                result = subprocess.run(
                    cmd,
                    cwd="E:/Project/feiyingqi-wechat-ainews",
                    capture_output=True,
                    text=True,
                    timeout=120,
                    env={**os.environ, "DASHSCOPE_API_KEY": "sk-092377b24cf842dc991142ae908e5ecb"}
                )
                
                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"baoyu封面生成成功: {output_path}")
                    return output_path
                else:
                    logger.warning(f"baoyu封面生成失败，使用本地生成...")
            except Exception as e:
                logger.warning(f"baoyu调用失败: {e}，使用本地生成...")
            
            # 最后使用本地生成
            logger.info("使用本地生成封面...")
            
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
    """生成封面图 - 优先使用baoyu-image-gen生成写实AI行业封面"""
    
    # 优先使用baoyu-image-gen生成写实封面
    try:
        import os
        import subprocess
        
        # baoyu-image-gen脚本路径
        script_path = "C:/Users/Administrator/.claude/skills/baoyu-image-gen/scripts/main.ts"
        
        # 根据标题构建专业提示词
        prompt = _build_baoyu_prompt(title)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 使用bun运行baoyu-image-gen
        cmd = [
            "bun", script_path,
            "--prompt", prompt,
            "--image", output_path,
            "--provider", "dashscope",
            "--ar", "16:9"
        ]
        
        result = subprocess.run(
            cmd,
            cwd="E:/Project/feiyingqi-wechat-ainews",
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "DASHSCOPE_API_KEY": "sk-092377b24cf842dc991142ae908e5ecb"}
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"baoyu封面生成成功: {output_path}")
            return output_path
        else:
            logger.warning(f"baoyu封面生成失败: {result.stderr}")
            
    except Exception as e:
        logger.warning(f"baoyu封面生成异常: {e}")
    
    # 失败则使用本地生成
    logger.info("使用本地生成封面...")
    generator = CoverGenerator()
    return generator.generate_cover(title, output_path, style, **kwargs)


def _build_baoyu_prompt(title: str) -> str:
    """根据标题构建专业的baoyu-image-gen提示词 - 写实照片风格"""
    # 明确要求写实照片风格
    base = "Professional photography, RAW photo, DSLR camera, "
    
    # 根据文章类型添加特定写实元素
    if "笔记" in title or "note" in title.lower():
        elements = "realistic modern workspace with actual paper notebooks, real laptops showing AI software, tablet computers on wooden desk, neural network visualization on monitors in background, natural window lighting, shallow depth of field"
    elif "搜索" in title or "search" in title.lower():
        elements = "realistic futuristic control room with large screens showing AI search interface, server racks in background, blue LED lighting, professional photography, cinematic lighting"
    elif "编程" in title or "code" in title.lower():
        elements = "realistic programmer's desk with multiple real monitors displaying code with AI autocomplete, mechanical keyboard, coffee cup, dark room with RGB LED strips, bokeh effect"
    elif "视频" in title or "video" in title.lower():
        elements = "realistic video editing suite with large high-res monitors showing AI video tools, professional cameras on tripods, studio lighting equipment, wooden floor reflection"
    elif "音频" in title or "audio" in title.lower():
        elements = "realistic audio production studio with mixing console, studio monitors, microphones, computer screen showing AI audio waveform, moody purple and blue lighting, shallow depth of field"
    elif "设计" in title or "design" in title.lower():
        elements = "realistic modern design studio with iMacs displaying AI graphic tools, drawing tablets, color palettes on wall, plants in corner, natural lighting from large windows"
    elif "营销" in title or "marketing" in title.lower():
        elements = "realistic modern marketing office with analytics dashboards on screens, people working on laptops (blurred), whiteboard with AI strategy, bright professional lighting"
    elif "医疗" in title or "medical" in title.lower():
        elements = "realistic modern medical office with AI diagnostics interface on computer, stethoscope on desk, medical charts, clean white and blue decor, soft clinical lighting"
    elif "金融" in title or "finance" in title.lower():
        elements = "realistic trading floor with multiple monitors showing AI market predictions, stock tickers in background, professional suit jacket (blurred), New York skyline through windows"
    elif "法律" in title or "legal" in title.lower():
        elements = "realistic modern law office with leather chairs, law books, computer showing AI legal analysis, mahogany desk, professional warm lighting, wood paneling"
    elif "会议" in title or "meeting" in title.lower():
        elements = "realistic smart conference room with large screen showing AI transcription, glass table with laptops, modern office chairs, city skyline through glass wall"
    elif "图像" in title or "image" in title.lower():
        elements = "realistic digital art studio with Wacom tablets, dual monitors showing AI art generation, color calibration tools, creative lighting with LED strips"
    elif "办公" in title or "office" in title.lower():
        elements = "realistic smart office environment with AI productivity tools on screens, ergonomic furniture, plants, modern decor, bright natural lighting"
    elif "数据" in title or "data" in title.lower():
        elements = "realistic data science workspace with multiple monitors showing AI analytics dashboards, whiteboard with neural network diagrams, coffee and notebooks, modern tech office"
    elif "教育" in title or "education" in title.lower():
        elements = "realistic modern classroom with interactive whiteboard showing AI tutoring interface, tablets on desks, bright cheerful lighting, educational posters on walls"
    else:
        elements = "realistic modern AI workspace with neural network visualizations on screens, multiple monitors, professional tech environment, cinematic lighting"
    
    # 强化写实风格关键词
    style = "photorealistic, ultra-detailed, 8K resolution, professional photography, bokeh, shallow depth of field, natural lighting, no cartoon, no vector, no illustration, no 3D render"
    
    return f"{base}{elements}, {style}. 16:9 aspect ratio, high quality, detailed"


    def _select_realistic_photo(self, title: str) -> Optional[str]:
        """根据标题智能选择真实照片背景"""
        import os
        
        # 照片目录
        photo_dir = "assets/covers"
        if not os.path.exists(photo_dir):
            return None
        
        # 根据文章类型选择对应照片
        photo_map = {
            "笔记": ["workspace", "note", "desk"],
            "note": ["workspace", "note", "desk"],
            "搜索": ["search", "tech", "monitor"],
            "search": ["search", "tech", "monitor"],
            "编程": ["code", "programming", "developer"],
            "code": ["code", "programming", "developer"],
            "视频": ["video", "studio", "camera"],
            "video": ["video", "studio", "camera"],
            "音频": ["audio", "music", "studio"],
            "audio": ["audio", "music", "studio"],
            "设计": ["design", "creative", "art"],
            "design": ["design", "creative", "art"],
            "营销": ["marketing", "business", "office"],
            "marketing": ["marketing", "business", "office"],
            "医疗": ["medical", "hospital", "health"],
            "medical": ["medical", "hospital", "health"],
            "金融": ["finance", "trading", "business"],
            "finance": ["finance", "trading", "business"],
            "法律": ["law", "legal", "office"],
            "legal": ["law", "legal", "office"],
            "会议": ["meeting", "conference", "room"],
            "meeting": ["meeting", "conference", "room"],
            "图像": ["image", "art", "creative"],
            "image": ["image", "art", "creative"],
            "办公": ["office", "workspace", "desk"],
            "office": ["office", "workspace", "desk"],
            "数据": ["data", "analytics", "dashboard"],
            "data": ["data", "analytics", "dashboard"],
            "教育": ["education", "classroom", "learning"],
            "education": ["education", "classroom", "learning"],
        }
        
        # 查找匹配的照片
        import glob
        photos = glob.glob(os.path.join(photo_dir, "*.jpg")) + \
                 glob.glob(os.path.join(photo_dir, "*.png")) + \
                 glob.glob(os.path.join(photo_dir, "*.jpeg"))
        
        if not photos:
            return None
        
        # 根据标题关键词匹配
        title_lower = title.lower()
        for key, keywords in photo_map.items():
            if key in title or key in title_lower:
                for photo in photos:
                    photo_name = os.path.basename(photo).lower()
                    if any(kw in photo_name for kw in keywords):
                        return photo
        
        # 如果没有匹配，随机选一张
        import random
        return random.choice(photos) if photos else None
    
    def _create_photo_cover(self, title: str, photo_path: str, output_path: str) -> str:
        """使用真实照片创建封面（叠加标题文字）"""
        if not PIL_AVAILABLE:
            logger.error("PIL not installed")
            return ""
        
        try:
            # 打开照片
            img = Image.open(photo_path).convert('RGB')
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # 添加半透明渐变叠加层（让文字更清晰）
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # 从底部向上的渐变（黑色半透明）
            for i in range(self.height // 2):
                alpha = int(255 * (i / (self.height // 2)) * 0.7)
                draw.rectangle([(0, self.height - i), (self.width, self.height - i - 1)], 
                              fill=(0, 0, 0, alpha))
            
            # 合并叠加层
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # 绘制标题文字（白色，带阴影）
            font = self._load_font(40)  # 大号字体
            if not font:
                font = ImageFont.load_default()
            
            # 文字换行处理
            max_width = self.width - 100
            lines = []
            words = title.split()
            current_line = []
            current_width = 0
            
            for word in words:
                word_width = draw.textlength(word + ' ', font=font)
                if current_width + word_width <= max_width:
                    current_line.append(word)
                    current_width += word_width
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = draw.textlength(word + ' ', font=font)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # 绘制文字（从底部向上）
            line_height = 50
            total_height = len(lines) * line_height
            y_start = self.height - total_height - 50
            
            for i, line in enumerate(lines[:3]):  # 最多3行
                x = 50
                y = y_start + i * line_height
                
                # 文字阴影
                draw.text((x+2, y+2), line, font=font, fill=(0, 0, 0, 128))
                # 主文字
                draw.text((x, y), line, font=font, fill=(255, 255, 255))
            
            # 保存
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'PNG', quality=95)
            
            logger.info(f"真实照片封面创建成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"创建照片封面失败: {e}")
            return ""

def generate_cover_image(
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


def generate_gradient_cover(title: str, output_path: str = "output/cover.png",
                            width: int = 1440, height: int = 810, style: str = "auto"):
    """生成高设计感 AI 封面（深色渐变 + 科技装饰 + 白色标题，公众号 1440x810）。

    优化点：
    - 背景：深色垂直渐变 + AI 科技装饰（神经网络节点连线/粒子光点/科技网格）
    - 层次：顶部主题标签 + 主标题（自动换行，最大3行）+ 底部日期/署名
    - 质感：暗角效果 + 强调色光晕，避免单调
    - 配色：多套高对比配色（深底亮字），确保文字清晰可见
    """
    from PIL import Image, ImageDraw, ImageFont
    import os, random, math

    try:
        # 多套高对比配色：深色背景 + 亮色文字 + 强调色
        schemes = [
            # 深蓝 + 青色高亮
            dict(bg_top=(8, 12, 28), bg_bot=(16, 42, 80), accent=(34, 211, 238),
                 text=(255, 255, 255), sub=(190, 220, 255), deco=(0, 229, 255)),
            # 深紫 + 紫色高亮
            dict(bg_top=(18, 8, 40), bg_bot=(60, 20, 90), accent=(168, 85, 247),
                 text=(255, 255, 255), sub=(220, 200, 255), deco=(190, 120, 255)),
            # 深绿 + 翠绿高亮
            dict(bg_top=(4, 24, 20), bg_bot=(16, 70, 55), accent=(16, 185, 129),
                 text=(255, 255, 255), sub=(200, 245, 230), deco=(52, 211, 153)),
            # 深红棕 + 橙高亮
            dict(bg_top=(30, 10, 8), bg_bot=(90, 30, 20), accent=(249, 115, 22),
                 text=(255, 255, 255), sub=(255, 220, 200), deco=(251, 146, 60)),
        ]
        scheme = schemes[random.randrange(len(schemes))]

        # 风格：auto 按标题关键词选，否则用指定
        style_keywords = {
            "neural": ["智能", "AI", "模型", "学习", "大脑", "意识"],
            "circuit": ["芯片", "硬件", "算力", "服务器"],
        }
        if style == "auto":
            style = "neural" if any(k in title for k in style_keywords["neural"]) else \
                    "circuit" if any(k in title for k in style_keywords["circuit"]) else "grid"

        img = Image.new('RGB', (width, height), scheme["bg_top"])
        # 垂直渐变背景
        for y in range(height):
            t = y / height
            r = int(scheme["bg_top"][0] + (scheme["bg_bot"][0] - scheme["bg_top"][0]) * t)
            g = int(scheme["bg_top"][1] + (scheme["bg_bot"][1] - scheme["bg_top"][1]) * t)
            b = int(scheme["bg_top"][2] + (scheme["bg_bot"][2] - scheme["bg_top"][2]) * t)
            ImageDraw.Draw(img).line([(0, y), (width, y)], fill=(r, g, b))

        draw = ImageDraw.Draw(img, "RGBA")

        def load_font(size):
            for p in ["C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc",
                      "C:/Windows/Fonts/simhei.ttf"]:
                if os.path.exists(p):
                    return ImageFont.truetype(p, size)
            return ImageFont.load_default()

        # 科技装饰：神经网络节点连线 + 粒子光点
        random.seed(len(title))  # 同一标题生成一致的装饰
        deco_alpha = 60
        if style in ("neural", "grid"):
            # 神经网络节点连线
            nodes = []
            for _ in range(12):
                n = (random.randint(0, width), random.randint(int(height*0.08), int(height*0.5)))
                r = random.randint(3, 7)
                draw.ellipse([n[0]-r, n[1]-r, n[0]+r, n[1]+r],
                             fill=scheme["deco"] + (deco_alpha,))
                nodes.append(n)
            for i, n1 in enumerate(nodes):
                for n2 in nodes[i+1:]:
                    dist = math.hypot(n1[0]-n2[0], n1[1]-n2[1])
                    if dist < 420:
                        draw.line([n1, n2], fill=scheme["deco"] + (deco_alpha//2,), width=1)
        else:
            # 电路板网格
            for gx in range(0, width, 60):
                draw.line([(gx, 0), (gx, int(height*0.5))], fill=scheme["deco"] + (20,), width=1)
            for gy in range(0, int(height*0.5), 60):
                draw.line([(0, gy), (width, gy)], fill=scheme["deco"] + (20,), width=1)

        # 底部渐隐（to 深色，增强层次）
        for y in range(int(height*0.75), height):
            alpha = int(120 * (y - height*0.75) / (height*0.25))
            ImageDraw.Draw(img, "RGBA").line(
                [(0, y), (width, y)], fill=(0, 0, 0) + (alpha,))

        # 顶部强调条 + 主题标签
        bar_y = int(height * 0.20)
        draw.rectangle([0, bar_y, int(width*0.14), bar_y + 6], fill=scheme["accent"] + (255,))
        label = "AI 前沿观察"
        label_font = load_font(int(height * 0.028))
        draw.text((int(width*0.14) + 18, bar_y - 6), label,
                  font=label_font, fill=scheme["sub"] + (220,))

        # 主标题（自动换行，最大3行，居中）
        max_width = int(width * 0.84)
        font = load_font(int(height * 0.068))
        title_y = int(height * 0.30)
        lines, current = [], ""
        for ch in title:
            if draw.textlength(current + ch, font=font) <= max_width:
                current += ch
            else:
                lines.append(current)
                current = ch
        if current:
            lines.append(current)
        lines = lines[:3]

        # 标题带柔和投影，增强可读性
        for ln in lines:
            tw = draw.textlength(ln, font=font)
            x = (width - tw) / 2
            draw.text((x + 3, title_y + 3), ln, font=font, fill=(0, 0, 0) + (90,))
            draw.text((x, title_y), ln, font=font, fill=scheme["text"] + (255,))
            title_y += int(height * 0.095)

        # 底部日期 + 作者
        small = load_font(int(height * 0.026))
        footer = "AI前沿观察 · " + (__import__("datetime").datetime.now().strftime("%Y年%m月%d日"))
        fw = draw.textlength(footer, font=small)
        draw.text(((width - fw) / 2, height - int(height * 0.09)), footer,
                  font=small, fill=scheme["sub"] + (200,))

        # 暗角效果
        for i in range(int(width*0.08)):
            a = int(60 * (1 - i / (width*0.08)))
            draw.rectangle([i, i, width-i, height-i], outline=(0, 0, 0) + (a,))

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        img.save(output_path, quality=95)
        return output_path
    except Exception as e:
        logger.error(f"渐变封面生成失败: {e}")
        return ""


if __name__ == "__main__":
    import sys
    
    title = sys.argv[1] if len(sys.argv) > 1 else "AI热点速递 | 2026年3月22日"
    output = sys.argv[2] if len(sys.argv) > 2 else "output/cover.png"
    style = sys.argv[3] if len(sys.argv) > 3 else "auto"
    
    result = generate_cover_image(title, output, style)
    print(f"封面图生成完成: {result}")
