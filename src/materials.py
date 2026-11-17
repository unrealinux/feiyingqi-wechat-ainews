"""本地技能素材（社区整理的实战指南章节）的登记表与加载器。

素材不是模型凭记忆写的产品参数，而是本机两个社区仓库里的章节原文，
每章自带 H1 标题与上游地址，写进 sources 就是可溯源出处（AGENTS.md §3）。

    ~/文档/workbuddy-guide-skill/skills/workbuddy-playbook/references
    ~/文档/doubaowork-guide-skill/skills/doubaowork-guide/references

两个都是社区项目，**不是腾讯/字节官方文档**：成稿署名必须写清，
界面、价格、额度以官方渠道为准（各仓库 SKILL.md 的三层区分）。
"""

import re
from pathlib import Path
from typing import Dict, Optional

_HOME = Path.home()

# 上游仓库会调整目录（2026-11-17 workbuddy-guide-skill 就把 references/chapters
# 改成了 skills/<playbook>/workbuddy/*.md），所以每个素材源登记「候选目录」，
# 按顺序找第一个真的有章节文件的，硬编码单个路径必然会在某天突然抓不到。
MATERIALS: Dict[str, dict] = {
    "workbuddy": {
        "name": "WorkBuddy",
        "candidates": [
            "文档/workbuddy-guide-skill/skills/*/workbuddy",
            "文档/workbuddy-guide-skill/skills/*/references/chapters",
            "文档/workbuddy-guide-skill/skills/*/references",
        ],
        "source_label": "《WorkBuddy 实战蓝皮书》（社区整理，非官方文档）",
        "site": "https://workbuddy.homes",
    },
    "doubaowork": {
        "name": "豆包工作",
        "candidates": [
            "文档/doubaowork-guide-skill/skills/*/references/chapters",
            "文档/doubaowork-guide-skill/skills/*/references",
            "文档/workbuddy-guide-skill/skills/*/doubao",
        ],
        "source_label": "《豆包工作实战指南》（社区整理，非官方文档）",
        "site": "https://doubaowork.homes",
    },
}


def _has_chapters(path: Path) -> bool:
    return path.is_dir() and any(
        p.suffix == ".md" and p.name.upper() != "INDEX.MD" for p in path.glob("*.md")
    )


def references_dir(key: str) -> Path:
    """素材目录：按候选 glob 找第一个真有章节 .md 的目录；都找不到返回第一个候选。"""
    if key not in MATERIALS:
        raise KeyError(f"未知素材源 {key!r}，可选：{sorted(MATERIALS)}")
    first = None
    for pattern in MATERIALS[key].get("candidates", []):
        # 绝对路径直接当目录（测试和"素材放在外面"的场景）；相对路径按 _HOME 展开
        candidate = Path(pattern).expanduser()
        paths = [candidate] if candidate.is_absolute() else sorted(_HOME.glob(pattern))
        for path in paths:
            if first is None:
                first = path
            if _has_chapters(path):
                return path
    return first or (_HOME / "文档")


def chapter_path(key: str, rel: str) -> Path:
    """章节文件路径：上游可能把 chapters/ 这层去掉，两种布局都试一次。"""
    base = references_dir(key)
    direct = base / rel
    if direct.exists():
        return direct
    return base / Path(rel).name
    return MATERIALS[key]["references"]


def source_label(key: str) -> str:
    return MATERIALS[key]["source_label"]


def chapter_title(text: str) -> str:
    """章节正文的第一个 H1，作为 sources 里的条目名。"""
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def chapter_url(text: str) -> Optional[str]:
    """章节头部的在线地址（豆包工作有；WorkBuddy 只有站点首页，返回 None）。"""
    m = re.search(r"在线:\s*\[[^\]]*\]\((https?://[^)]+)\)", text)
    return m.group(1) if m else None


def load_chapters(key: str, rel_paths) -> list:
    """按顺序读章节，返回 [(标题, 正文)]；文件缺失直接跳过（不抛异常）。"""
    out = []
    for rel in rel_paths:
        path = chapter_path(key, rel)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        out.append((chapter_title(text) or Path(rel).stem, text))
    return out
