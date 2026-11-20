"""从文章 spec / 素材里提取封面出图线索。

背景（2026-11-20）：封面只用标题 pick_theme() 选一个固定英文 prompt，
正文写了什么、素材里有什么具体产品/数字，跟画面完全无关。
Agnes 出图接口只吃 prompt（image_url 字段被明确拒绝），所以只能走语义层：
把"这篇文章到底在讲什么"压缩成一句出图线索，喂进 prompt。

不引入素材外的新事实（AGENTS.md 禁编造）：线索只从 spec 的 subtitle/lead/
heading 与素材标题/摘要里取，且只取文本片段，不改写数字。
"""

import re
from typing import List, Optional

# 这些词出现时说明标题/正文在讲具体产品，直接作为画面主体线索
_SCENE_HINTS = [
    "数据中心",
    "服务器",
    "芯片",
    "半导体",
    "机器人",
    "具身",
    "工厂",
    "自动驾驶",
    "办公",
    "文档",
    "表格",
    "会议",
    "代码",
    "编辑器",
    "终端",
    "命令行",
    "连接器",
    "接口",
    "工作台",
    "知识库",
    "搜索",
    "浏览器",
    "手机",
    "客户",
    "实验室",
    "湿实验",
    "基准",
    "论文",
    "工厂",
    "流水线",
    "产线",
]

_PRODUCT_RE = re.compile(
    r"[A-Z][A-Za-z0-9\.\-]{2,}|"
    r"[\u4e00-\u9fa5]{2,6}(?:大模型|智能体|工作台|处理器|芯片|机器人|编辑器|浏览器)",
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def cover_context(
    spec: Optional[dict] = None, news_items: Optional[List] = None
) -> str:
    """生成一句出图线索（中文，直接拼进英文 prompt 也可读）。

    优先级：spec 的 subtitle + 各节 heading + 素材标题；最多 6 个片段，总长 ≤ 400。
    """
    parts: List[str] = []
    if spec:
        for key in ("subtitle",):
            v = _clean(spec.get(key))
            if v:
                parts.append(v)
        for sec in spec.get("sections") or []:
            v = _clean(sec.get("heading"))
            if v:
                parts.append(v)
    for item in (news_items or [])[:6]:
        v = _clean(getattr(item, "title", ""))
        if v:
            parts.append(v)

    # 去重保序
    seen, unique = set(), []
    for p in parts:
        if p and p not in seen:
            seen.add(p)
            unique.append(p)

    text = "；".join(unique[:6])
    return text[:400]


def product_names(
    spec: Optional[dict] = None, news_items: Optional[List] = None
) -> List[str]:
    """从 spec / 素材里抽产品名，最多 4 个（用于"画面里要有这类东西"）。"""
    found: List[str] = []
    for text in (
        [str(spec.get(k, "")) for k in ("title", "subtitle")]
        + [_clean(x.get("heading")) for x in (spec or {}).get("sections") or []]
        + [_clean(getattr(x, "title", "")) for x in (news_items or [])[:6]]
        if spec
        else [_clean(getattr(x, "title", "")) for x in (news_items or [])[:6]]
    ):
        for m in _PRODUCT_RE.findall(text):
            if len(m) >= 3 and m not in found:
                found.append(m)
    return found[:4]


def scene_hints(text: str) -> List[str]:
    """正文/素材里出现的场景词（用于定构图）。"""
    t = str(text or "")
    return [h for h in _SCENE_HINTS if h in t][:5]
