import os
import re
from datetime import datetime
from pathlib import Path


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
