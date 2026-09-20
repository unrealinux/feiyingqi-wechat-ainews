"""
AI Photo Cover - 写实风格封面生成

用 Agnes 文生图生成「AI 相关写实元素」背景（数据中心 / 芯片 / 机械臂 / 实验室…），
再本地叠加标题、署名与日期，输出公众号封面标准尺寸 1440×810。

设计要点（对齐 AGENTS.md）：
- 主题按标题关键词挑选 + 按日期轮换，避免每天同一张图造成模板化观感。
- 图片一律先落地 output/ 再上传，绝不把远端 URL 直接塞给微信。
- 任何一步失败都返回 None，由调用方降级回本地渐变封面，绝不中断发布链路。
"""

import io
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests

from src.config import load_config, get_agnes_config

logger = logging.getLogger(__name__)

COVER_WIDTH = 1440
COVER_HEIGHT = 810  # 16:9，公众号封面标准尺寸
AGNES_IMAGE_ENDPOINT = "https://apihub.agnes-ai.com/v1/images/generations"

# 写实风格主题池：key -> (关键词, 英文出图提示词)
# 提示词统一要求 photo / photorealistic，并显式排除文字与水印，
# 因为标题是本地叠加的，图上再出现文字就会打架。
_NO_TEXT = "no text, no letters, no watermark, no logo, no people's faces"
_THEMES = {
    "datacenter": {
        "keywords": ["数据中心", "算力", "服务器", "集群", "训练", "推理", "云", "能耗", "电力"],
        "prompt": (
            "Ultra-realistic photograph of a modern AI data center aisle at night. "
            "Rows of GPU server racks with dense blue and green indicator LEDs, "
            "visible fiber optic cabling, brushed metal panels, cold aisle containment, "
            "shallow depth of field, moody cinematic lighting, teal and deep blue color grading, "
            "shot on 35mm lens, commercial photography quality. " + _NO_TEXT
        ),
    },
    "chip": {
        "keywords": ["芯片", "半导体", "制程", "晶圆", "硅", "封装", "光刻", "材料", "铜", "硬件",
                     "物质", "沙子", "晶体管", "摩尔定律"],
        "prompt": (
            "Extreme macro photograph of an advanced AI processor die on a dark PCB. "
            "Golden and copper micro traces catching raking light, silicon surface reflections, "
            "tiny capacitors and solder bumps in sharp focus, extremely shallow depth of field, "
            "thin film interference colors, dark background, studio macro lighting. " + _NO_TEXT
        ),
    },
    "robot": {
        "keywords": ["机器人", "具身", "机械", "自动化", "工厂", "制造", "无人", "驾驶", "汽车"],
        "prompt": (
            "Photorealistic close-up of an industrial robotic arm in a clean modern factory, "
            "precision joint actuators and cabling, motion-blurred movement, "
            "cool white and blue industrial lighting, polished floor reflections, "
            "shallow depth of field, editorial technology photography. " + _NO_TEXT
        ),
    },
    "lab": {
        "keywords": ["医疗", "生物", "药物", "科研", "实验", "基因", "蛋白", "材料", "科学", "物理"],
        "prompt": (
            "Realistic laboratory photograph: glassware with glowing cyan liquid, "
            "an electron microscope in the background, precise scientific instruments, "
            "clean stainless steel surfaces, dark room lit by instrument glow, "
            "shallow depth of field, editorial science photography. " + _NO_TEXT
        ),
    },
    "network": {
        "keywords": ["模型", "大模型", "神经网络", "开源", "安全", "对齐", "伦理", "监管", "广告", "商业", "资本", "投资"],
        "prompt": (
            "Abstract photorealistic render of a neural network: thousands of luminous nodes "
            "connected by glowing fiber strands in dark space, depth haze, bokeh particles, "
            "teal blue and violet palette with warm amber accents, ultra-detailed, "
            "long exposure light trails, 3D render cinematic quality. " + _NO_TEXT
        ),
    },
    "office": {
        "keywords": ["产品", "发布", "公司", "团队", "办公", "创业", "会议", "生态", "合作", "大会"],
        "prompt": (
            "Photorealistic modern tech workspace at dusk: ultrawide curved monitors showing "
            "abstract data visualizations, mechanical keyboard, code reflections on a desk, "
            "city skyline through floor-to-ceiling windows, warm desk lamp against cool ambient light, "
            "shallow depth of field, editorial photography. " + _NO_TEXT
        ),
    },
}

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def pick_theme(title: str, seed: Optional[int] = None) -> str:
    """按标题关键词选主题；没有关键词命中时按日期轮换，保证封面不重样。"""
    scores = {}
    for name, spec in _THEMES.items():
        scores[name] = sum(1 for kw in spec["keywords"] if kw in title)

    best = max(scores.values())
    if best > 0:
        winners = sorted([n for n, v in scores.items() if v == best])
        # 同分时用日期做确定性选择，避免同一天多次调用得到不同主题
        return winners[(seed if seed is not None else datetime.now().toordinal()) % len(winners)]

    names = sorted(_THEMES.keys())
    return names[(seed if seed is not None else datetime.now().toordinal()) % len(names)]


def _load_font(size: int):
    from PIL import ImageFont

    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _fetch_agnes_image(api_key: str, prompt: str, size: str = "1024x1024",
                       timeout: int = 180) -> Optional[bytes]:
    """调 Agnes 文生图并下载图片字节；失败返回 None（不抛异常）。"""
    try:
        resp = requests.post(
            AGNES_IMAGE_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "agnes-image-2.5-flash", "prompt": prompt, "size": size},
            timeout=timeout,
        )
        if resp.status_code != 200:
            logger.warning(f"[封面] Agnes 返回 {resp.status_code}: {resp.text[:200]}")
            return None
        payload = resp.json()
        data = payload.get("data") or []
        url = data[0].get("url") if data else None
        if not url:
            logger.warning(f"[封面] Agnes 响应缺少图片 URL: {str(payload)[:200]}")
            return None
        img = requests.get(url, timeout=timeout)
        if img.status_code != 200:
            logger.warning(f"[封面] 下载 Agnes 图片失败: {img.status_code}")
            return None
        return img.content
    except Exception as e:
        logger.warning(f"[封面] Agnes 出图异常: {e}")
        return None


def _compose(img_bytes: bytes, title: str, date_text: str, author: str,
             with_text: bool = False) -> bytes:
    """把写实底图裁成 16:9，输出干净封面。

    默认 **不叠加任何文字**：标题/署名/日期一律不上图。
    仅做必要的剪裁 + 轻微四角压暗（让画面更聚焦）。
    with_text=True 时才画标题（保留给需要文字版的场景）。
    """
    from PIL import Image, ImageDraw

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # --- 等比裁剪到 16:9（居中，尽量保留主体） ---
    target_ratio = COVER_WIDTH / COVER_HEIGHT
    ratio = img.width / img.height
    if ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        top = int((img.height - new_h) * 0.35)  # 略偏上，避免裁掉主体
        img = img.crop((0, top, img.width, top + new_h))
    img = img.resize((COVER_WIDTH, COVER_HEIGHT), Image.Resampling.LANCZOS)

    if with_text:
        # --- 压暗：左侧横向渐变（放标题）+ 底部渐晕，保证白字可读 ---
        # 左侧约 30% 宽保持高不透明度，之后衰减到 0，避免标题落在亮部（如金色走线）上发虚
        scrim = Image.new("L", (COVER_WIDTH, 1))
        for x in range(COVER_WIDTH):
            pos = x / COVER_WIDTH
            if pos <= 0.30:
                alpha = 232
            else:
                alpha = int(232 * max(0.0, 1.0 - (pos - 0.30) / 0.52))
            scrim.putpixel((x, 0), alpha)
        scrim = scrim.resize((COVER_WIDTH, COVER_HEIGHT))
        img = Image.composite(Image.new("RGB", img.size, (4, 12, 14)), img, scrim)

        bottom = Image.new("L", (1, COVER_HEIGHT))
        for y in range(COVER_HEIGHT):
            t = y / COVER_HEIGHT
            bottom.putpixel((0, y), int(150 * max(0.0, (t - 0.55) / 0.45) ** 1.4))
        bottom = bottom.resize((COVER_WIDTH, COVER_HEIGHT))
        img = Image.composite(Image.new("RGB", img.size, (3, 10, 12)), img, bottom)

        draw = ImageDraw.Draw(img)

        # --- 顶部品牌标识 ---
        accent = (46, 214, 168)
        draw.rectangle([(88, 96), (88 + 120, 96 + 7)], fill=accent)
        draw.text((236, 92), author, font=_load_font(30), fill=(232, 240, 238))

        # --- 标题：自动折行，最多 3 行 ---
        font_title = _load_font(76)
        max_width = COVER_WIDTH - 220
        lines, current = [], ""
        for ch in title:
            probe = current + ch
            if draw.textlength(probe, font=font_title) > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = probe
        if current:
            lines.append(current)
        lines = lines[:3]

        y = 300 if len(lines) <= 2 else 250
        for line in lines:
            draw.text((90 + 3, y + 3), line, font=font_title, fill=(0, 0, 0))
            draw.text((90, y), line, font=font_title, fill=(255, 255, 255))
            y += 100

        # --- 底部日期 ---
        draw.text((COVER_WIDTH - 90, COVER_HEIGHT - 76), f"{author} · {date_text}",
                  font=_load_font(28), fill=(198, 214, 210), anchor="ra")
    else:
        pass  # 纯图模式：不叠字、不压暗，保留照片原貌

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=92, optimize=True)
    return out.getvalue()


def generate_ai_photo_cover(title: str,
                            output_path: str = "output/cover_ai.jpg",
                            author: str = "AI前沿观察",
                            date_text: Optional[str] = None,
                            theme: Optional[str] = None,
                            with_text: bool = False) -> Tuple[Optional[str], Optional[str]]:
    """生成写实风封面。

    Args:
        with_text: 默认 False —— 只出纯图，不叠加标题/署名/日期。

    Returns:
        (图片路径, 主题名)；失败时返回 (None, None)，调用方应降级到渐变封面。
    """
    config = load_config()
    api_key = get_agnes_config(config).get("api_key", "")
    if not api_key:
        logger.warning("[封面] 未配置 AGNES_API_KEY，跳过写实封面")
        return None, None

    theme = theme or pick_theme(title)
    prompt = _THEMES.get(theme, _THEMES["datacenter"])["prompt"]
    date_text = date_text or datetime.now().strftime("%Y年%m月%d日")

    logger.info(f"[封面] 主题={theme}，调用 Agnes 出图…")
    raw = _fetch_agnes_image(api_key, prompt)
    if not raw:
        return None, None

    try:
        composed = _compose(raw, title, date_text, author, with_text=with_text)
    except Exception as e:
        logger.warning(f"[封面] 合成失败: {e}")
        return None, None

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(composed)
    logger.info(f"[封面] 写实封面已生成: {out} ({len(composed)//1024} KB, 主题={theme})")
    return str(out), theme


if __name__ == "__main__":
    import sys

    t = sys.argv[1] if len(sys.argv) > 1 else "AI 军备竞赛的隐形维度"
    p, th = generate_ai_photo_cover(t, output_path="output/_cover_preview.jpg")
    print("结果:", p, "| 主题:", th or "（生成失败）")
