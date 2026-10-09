import os
import re
import html
from datetime import datetime
from pathlib import Path


def html_to_text(markup: str) -> str:
    """剥掉 HTML 标签，给需要纯文本的分析用（如 AI 味打分）。

    editorial 模板产出的是全 inline style 的 HTML，标签会干扰句长/标点分析。
    """
    stripped = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", markup, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", stripped))


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()
    return name[:255]


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def format_date(date: datetime = None, fmt: str = "%Y-%m-%d") -> str:
    if date is None:
        date = datetime.now()
    return date.strftime(fmt)


def format_datetime(dt: datetime = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)
