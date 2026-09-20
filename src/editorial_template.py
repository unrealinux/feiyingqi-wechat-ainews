"""
Editorial Template - 「深读」排版渲染器

把 LLM 产出的**结构化内容**渲染成固定的杂志式排版（母版取自 2026-09-10
《OpenAI 秀出来的 99.9%，和它藏起来的 41.4%》那篇的样式）。

为什么不让 LLM 直接写 HTML：
- 微信只认 inline style，模型手写 CSS 极易漂移（字号/间距/配色各篇不同）；
- 排版是品牌资产，应当稳定可控；内容才是每篇要变的东西。
所以：LLM 只产出内容字段，HTML 由本模块确定性拼装。

内容规格（JSON）见 EDITORIAL_SCHEMA_DOC。任何必填项缺失 → 抛 EditorialSpecError，
由调用方按 fail-closed 处理（AGENTS.md：宁可不产出，不塞低质稿）。
"""

import html
import re
from typing import Any, Dict, List

# 颜色（取自母版，勿随意改，改了整站观感就不统一了）
BG = "#F7F4EE"
INK = "#1C1B18"
ACCENT_PRIMARY = "#C8401F"   # 砖红：本方/重点
ACCENT_SECOND = "#1F6F5B"    # 墨绿：对手/次级
MUTED = "#6E6A5E"
HAIRLINE = "#D8D2C4"
FAINT = "#B9B2A0"
CARD_BG = "#FFFFFF"

_ACCENTS = {"red": ACCENT_PRIMARY, "green": ACCENT_SECOND, "primary": ACCENT_PRIMARY,
            "secondary": ACCENT_SECOND}
_BAR_COLORS = {
    "red": (ACCENT_PRIMARY, "1"),
    "primary": (ACCENT_PRIMARY, "1"),
    "green": (ACCENT_SECOND, "0.75"),
    "secondary": (ACCENT_SECOND, "0.75"),
    "grey": (FAINT, "1"),
    "gray": (FAINT, "1"),
}

SECTION_NUMERALS = ["壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌"]

EDITORIAL_SCHEMA_DOC = """
{
  "kicker": "AI 前沿观察 · 深读",              // 报头左，可省略
  "meta_line": "2026年9月16日 ｜ 一句话说明本篇看什么",
  "title": "主标题",                            // 可用 \\n 手工断行，≤ 30 字
  "subtitle": "一句话副标题",
  "lead": ["开头段1", "开头段2"],
  "sections": [
    {
      "heading": "章节标题",
      "accent": "red",                          // red | green，交替使用
      "blocks": [
        {"type": "p", "text": "正文段落，可用 **加粗**"},
        {"type": "bullets", "items": ["**要点**：说明", "**要点**：说明"]},
        {"type": "datacard", "accent": "red", "caption": "可选小标题",
         "lines": [{"label": "指标名", "note": "可选注释", "value": "97.6%"}]},
        {"type": "bars", "accent": "green", "caption": "图表标题",
         "rows": [{"label": "GPT-6 Astra", "value": 41.4, "color": "red"},
                  {"label": "对手模型", "value": 31.4, "color": "green"}]},
        {"type": "quote", "text": "需要单独拎出来的一句判断"}
      ]
    }
  ],
  "closing": ["收束段1", "收束段2"],
  "sources": ["1. 机构《标题》链接或可查标识", "2. ..."],
  "signature": "— AI 前沿观察 · 只做有出处的判断 —"
}
"""


class EditorialSpecError(ValueError):
    """结构化内容不合法（缺字段 / 无来源 / 章节过少）。"""


def _inline(text: str) -> str:
    """转义 HTML，然后把 **加粗** 还原成 <strong>（唯一允许的行内标记）。"""
    escaped = html.escape(str(text or ""), quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def _p(text: str, margin_bottom: int = 16) -> str:
    return (f'<p style="text-indent:2em; margin:0 0 {margin_bottom}px;">{_inline(text)}</p>')


def _section_heading(numeral: str, heading: str, accent: str) -> str:
    color = _ACCENTS.get(accent, ACCENT_PRIMARY)
    return (
        f'<p style="font-size:20px; font-weight:700; margin:0 0 12px; color:{INK};">'
        f'<span style="color:{color}; margin-right:8px;">{numeral}</span>{_inline(heading)}</p>'
    )


def _datacard(block: Dict[str, Any]) -> str:
    color = _ACCENTS.get(block.get("accent", "red"), ACCENT_PRIMARY)
    parts = [f'<div style="margin:0 0 16px; padding:14px; background:{CARD_BG}; border-left:4px solid {color};">']
    caption = block.get("caption")
    if caption:
        parts.append(f'<p style="margin:0 0 10px; font-size:14px; color:{MUTED};">{_inline(caption)}</p>')
    for i, line in enumerate(block.get("lines") or []):
        margin = "0" if i == len(block["lines"]) - 1 else "6px 0"
        note = f'（{html.escape(str(line["note"]))}）' if line.get("note") else ""
        raw_value = str(line.get("value", ""))
        # 纯文字值（如「材料基础」）不做大号强调，避免把名词排成关键指标
        if re.search(r"\d", raw_value):
            value_html = (f'<span style="color:{color}; font-weight:700; font-size:18px;">'
                          f'{html.escape(raw_value)}</span>')
        else:
            value_html = f'<strong>{_inline(raw_value)}</strong>'
        parts.append(
            f'<p style="margin:{margin}; font-size:15px;">'
            f'<strong>{_inline(line.get("label", ""))}</strong>{note}：{value_html}</p>'
        )
    parts.append("</div>")
    return "".join(parts)


def _bars(block: Dict[str, Any]) -> str:
    color = _ACCENTS.get(block.get("accent", "green"), ACCENT_SECOND)
    rows = block.get("rows") or []
    parts = [f'<div style="background:{CARD_BG}; padding:16px; margin:0 0 14px; border-left:4px solid {color};">']
    caption = block.get("caption")
    if caption:
        parts.append(f'<p style="margin:0 0 10px; font-size:14px; color:{MUTED};">{_inline(caption)}</p>')
    for i, row in enumerate(rows):
        bar_color, opacity = _BAR_COLORS.get(row.get("color", "green"), (ACCENT_SECOND, "0.75"))
        try:
            value = float(row.get("value", 0))
        except (TypeError, ValueError):
            value = 0.0
        width = max(1.0, min(100.0, value))  # 条宽直接用数值本身（百分比）
        label = _inline(row.get("label", ""))
        bold_open, bold_close = ("<strong>", "</strong>") if row.get("color") in ("red", "primary") else ("", "")
        value_style = f'color:{bar_color}; font-weight:700;' if row.get("color") in ("red", "primary") else ""
        last = i == len(rows) - 1
        parts.append(
            f'<p style="margin:0 0 4px; font-size:14px;">{bold_open}{label}{bold_close} '
            f'<span style="{value_style}">{html.escape(str(row.get("value", "")))}%</span></p>'
        )
        parts.append(
            f'<div style="width:{width:.1f}%; background:{bar_color}; height:8px; '
            f'margin:0 0 {"0" if last else "12px"}; opacity:{opacity};"></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def _quote(text: str) -> str:
    return (
        f'<div style="background:{CARD_BG}; padding:16px; margin:0 0 16px; '
        f'border-left:4px solid {ACCENT_PRIMARY};">'
        f'<p style="margin:0; font-size:15px;">{_inline(text)}</p></div>'
    )


def _render_blocks(blocks: List[Dict[str, Any]]) -> str:
    out = []
    blocks = [b for b in blocks if b]
    for i, block in enumerate(blocks):
        kind = block.get("type")
        last = i == len(blocks) - 1
        if kind == "p":
            out.append(_p(block.get("text", ""), 24 if last else 16))
        elif kind == "bullets":
            items = block.get("items") or []
            for j, item in enumerate(items):
                tail = 24 if (last and j == len(items) - 1) else 8
                out.append(
                    f'<p style="text-indent:2em; margin:0 0 {tail}px;">'
                    f'· {_inline(item)}</p>'
                )
        elif kind == "datacard":
            out.append(_datacard(block))
        elif kind == "bars":
            out.append(_bars(block))
        elif kind == "quote":
            out.append(_quote(block.get("text", "")))
        else:
            raise EditorialSpecError(f"未知的内容块类型: {kind!r}")
    return "".join(out)


def validate_spec(spec: Dict[str, Any]) -> None:
    """必填项校验。宁缺毋滥：缺来源直接判不合法。"""
    if not isinstance(spec, dict):
        raise EditorialSpecError("内容规格必须是 JSON 对象")
    for key in ("title", "subtitle", "lead", "sections", "closing", "sources"):
        if not spec.get(key):
            raise EditorialSpecError(f"缺少必填字段: {key}")
    if len(spec["sections"]) < 3:
        raise EditorialSpecError(f"章节过少（{len(spec['sections'])}），至少 3 节")
    if len(spec["sections"]) > len(SECTION_NUMERALS):
        raise EditorialSpecError(f"章节过多（{len(spec['sections'])}），最多 {len(SECTION_NUMERALS)} 节")
    if len(spec["sources"]) < 2:
        raise EditorialSpecError("数据来源至少需要 2 条（AGENTS.md：内容必须可溯源）")


def normalize_meta_date(spec: Dict[str, Any], date_text: Optional[str] = None) -> None:
    """把报头日期强行改成今天（在本地做，不依赖模型配合）。

    模型总倾向于用新闻发生日，导致报头日期与发布日不符；这里去掉开头的日期碎片
    后重新拼接，后面的“ ｜ 一句话说明”原样保留。
    """
    from datetime import datetime as _dt

    date_text = date_text or _dt.now().strftime("%Y年%m月%d日")
    meta = str(spec.get("meta_line", "") or "")
    rest = re.sub(
        r"^\s*\d{4}\s*[年\-/. ]\s*\d{1,2}\s*[月\-/. ]\s*\d{1,2}\s*日?\s*",
        "", meta,
    ).lstrip("｜| 　")
    spec["meta_line"] = f"{date_text} ｜ {rest}" if rest else date_text


def draft_title(spec: Dict[str, Any]) -> str:
    """草稿标题：把手工断行合成一行（微信标题不支持换行），并压到 64 字以内。"""
    title = re.sub(r"[ \t]*\n[ \t]*", " ", str(spec.get("title", "")))
    return re.sub(r"\s{2,}", " ", title).strip()[:64]


def render(spec: Dict[str, Any]) -> str:
    """把结构化内容渲染成微信公众号可用的 HTML（全 inline style）。"""
    validate_spec(spec)

    kicker = spec.get("kicker") or "AI 前沿观察 · 深读"
    meta_line = spec.get("meta_line", "")
    title_html = "<br>".join(html.escape(p, quote=False).strip()
                             for p in re.split(r"\n", str(spec["title"])) if p.strip())

    parts = [
        f'<section style="background-color:{BG}; padding:24px 18px; max-width:677px; margin:0 auto; '
        f"font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Microsoft YaHei',sans-serif; "
        f'color:{INK}; font-size:16px; line-height:1.9;">',
        # 报头
        f'<p style="margin:0 0 6px; font-size:13px; letter-spacing:3px; color:{ACCENT_PRIMARY}; '
        f'text-align:center;">{_inline(kicker)}</p>',
        f'<p style="margin:0 0 18px; font-size:12px; letter-spacing:1px; color:{MUTED}; text-align:center; '
        f'border-bottom:1px solid {HAIRLINE}; padding-bottom:14px;">{_inline(meta_line)}</p>',
        # 标题 + 副标题
        f'<p style="font-size:26px; font-weight:700; line-height:1.5; margin:0 0 8px; '
        f'text-align:center;">{title_html}</p>',
        f'<p style="font-size:14px; color:{MUTED}; text-align:center; margin:0 0 26px;">'
        f'{_inline(spec["subtitle"])}</p>',
    ]

    # 开头
    lead = list(spec["lead"])
    for i, para in enumerate(lead):
        parts.append(_p(para, 26 if i == len(lead) - 1 else 16))

    # 章节：序号自动分配，配色按 accent 交替
    for i, section in enumerate(spec["sections"]):
        accent = section.get("accent") or ("red" if i % 2 == 0 else "green")
        parts.append(_section_heading(SECTION_NUMERALS[i], section.get("heading", ""), accent))
        parts.append(_render_blocks(section.get("blocks") or []))

    # 金句收束（双线红框）
    closing = list(spec["closing"])
    box = [f'<div style="background:{CARD_BG}; padding:18px; margin:0 0 18px; '
           f'border-top:3px double {ACCENT_PRIMARY}; border-bottom:3px double {ACCENT_PRIMARY};">']
    for i, para in enumerate(closing):
        margin = "0" if i == len(closing) - 1 else "0 0 8px"
        box.append(f'<p style="margin:{margin}; font-size:15px;">{_inline(para)}</p>')
    box.append("</div>")
    parts.append("".join(box))

    # 数据来源
    sources_html = "<br>".join(_inline(s) for s in spec["sources"])
    parts.append(
        f'<p style="font-size:12px; color:{MUTED}; line-height:1.8; margin:0;">'
        f'<strong style="color:{INK};">数据来源（均真实可查）</strong><br>{sources_html}</p>'
    )

    # 落款
    signature = spec.get("signature") or "— AI 前沿观察 · 只做有出处的判断 —"
    parts.append(f'<p style="margin:22px 0 0; text-align:center; color:{FAINT}; '
                 f'font-size:12px;">{_inline(signature)}</p>')
    parts.append("</section>")
    return "".join(parts)


_NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# 译名雷区：模型把英文专有名词直译错的高频词，命中则整篇重生成。
# 例：mouse（小鼠）被误译为“鼠标”。
TERM_BLACKLIST = ("鼠标",)


def _numbers(text: str) -> set:
    return set(_NUM_RE.findall(str(text or "")))


def ground_numeric_blocks(spec: Dict[str, Any], material_text: str) -> List[str]:
    """数字溯源：图表/数据卡里的数字必须在素材里真实存在，否则删掉。

    AGENTS.md 要求数据可溯源、禁止编造。模型很爱为了图表好看自己凑百分比，
    所以这里做一道硬闸：素材里找不到的数字一律不得上图。

    Returns:
        被剔除项的说明列表（便于日志审计）。
    """
    allowed = _numbers(material_text)
    dropped: List[str] = []

    kept_sections = []
    for section in spec.get("sections") or []:
        kept_blocks = []
        for block in section.get("blocks") or []:
            if block.get("type") == "bars":
                rows = block.get("rows") or []
                keep_rows = [r for r in rows if _numbers(r.get("value")) <= allowed]
                for r in rows:
                    if r not in keep_rows:
                        dropped.append(f"图表行「{r.get('label')}={r.get('value')}%」（素材无此数据）")
                if len(keep_rows) < 2:
                    dropped.append(f"图表「{block.get('caption') or '未命名'}」（可溯源数据不足 2 行）")
                    continue
                block = {**block, "rows": keep_rows}
            elif block.get("type") == "datacard":
                lines = block.get("lines") or []
                keep_lines = [ln for ln in lines if _numbers(ln.get("value")) <= allowed]
                for ln in lines:
                    if ln not in keep_lines:
                        dropped.append(f"数据卡行「{ln.get('label')}={ln.get('value')}」（素材无此数据）")
                if not keep_lines:
                    dropped.append(f"数据卡「{block.get('caption') or '未命名'}」（无可溯源数据）")
                    continue
                block = {**block, "lines": keep_lines}
            kept_blocks.append(block)
        if kept_blocks:
            kept_sections.append({**section, "blocks": kept_blocks})

    spec["sections"] = kept_sections
    return dropped


def find_blacklisted_terms(spec: Dict[str, Any], terms=TERM_BLACKLIST) -> List[str]:
    """扫全文（含标题/章节/正文）里的译名错误。"""
    blob = " ".join(_walk_text(spec))
    return [t for t in terms if t in blob]


_IGNORABLE_NUMBERS = {"1", "2", "3", "4", "5", "6", "2025", "2026", "2027"}


def find_ungrounded_numbers(spec: Dict[str, Any], material_text: str,
                            limit: int = 12) -> List[str]:
    """正文里“素材中找不到”的数字，仅用于审计告警（不阻断发布）。

    图表/数据卡的数字是硬闸（ground_numeric_blocks 直接删）；正文里的数字
    则记入日志供人工复核——自动删句子会破坏行文，自动放行又不透明，
    所以选择“写日志、留痕迹”。
    """
    allowed = _numbers(material_text)
    found: List[str] = []
    for section in spec.get("sections") or []:
        for block in section.get("blocks") or []:
            texts = []
            if block.get("type") == "p":
                texts = [block.get("text", "")]
            elif block.get("type") == "bullets":
                texts = list(block.get("items") or [])
            for text in texts:
                for num in sorted(_numbers(text)):
                    if num in allowed or num in _IGNORABLE_NUMBERS:
                        continue
                    if len(num) < 2:  # 单个数字大概率是行文用字，不是数据
                        continue
                    if num not in found:
                        found.append(num)
    return found[:limit]


def _walk_text(node: Any):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _walk_text(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_text(v)


def extract_json(raw: str) -> Dict[str, Any]:
    """从模型输出里取出 JSON 对象（容忍 ```json 围栏与前后废话）。"""
    import json

    text = (raw or "").strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise EditorialSpecError("模型输出里找不到 JSON 对象")
        text = text[start:end + 1]
    try:
        spec = json.loads(text)
    except json.JSONDecodeError as e:
        raise EditorialSpecError(f"JSON 解析失败: {e}") from e
    return spec


if __name__ == "__main__":
    import json
    import sys

    demo = json.load(open(sys.argv[1], encoding="utf-8"))
    print(render(demo))
