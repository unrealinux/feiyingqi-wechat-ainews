"""选题/标题/可复制块的硬约束。

数据来源：2026-11-16 回采的 54 篇已发文章（本号，粉丝 100）。
结论（详见 output/阅读对照_2026-11-16.md）：

  含工具词（怎么/实操/避坑/闭环）  中位阅读 35
  不含工具词                      中位阅读 11
  含冲突/风险词（漏洞/断后/反超）  均值阅读 43.6
  泛趋势标题（"三款模型…""这周换了三件事"）  阅读 0–6

所以三条线写死在这里，供生成流程调用：
  1. 素材里没有"工具级变化"就不出稿（宁缺毋滥）
  2. 标题必须含具体工具名 + 动作/变化词，长度 14–30 字
  3. 每篇至少一个可复制块（步骤或 ≥3 条清单），治"看完就走、分享 0"
"""

import re
from typing import List

# 工具级变化：版本/定价/额度/权限/用法真的变了。只写"发布了新模型"不算。
TOOL_CHANGE_RE = re.compile(
    r"发布|上线|更新|升级|改版|停|下线|下线|免费|涨价|降价|定价|调价|加价|额度|配额|限流|"
    r"权限|限制|放开|开源|接入|支持|兼容|迁移|替换|新版|版本|v\d|beta|预览版|插件|扩展|"
    r"API|接口|插件|SDK|CLI|功能|入口|合并|拆分|改名|关停|剥离|收费|订阅|套餐|席位",
)

# 动作/变化词：标题里得有一个，读者才知道"这篇能拿来干什么"
ACTION_RE = re.compile(
    r"怎么|如何|为什么|能不能|要不要|上手|接入|配置|设置|迁移|替换|避坑|踩坑|跑通|闭环|"
    r"实操|实战|教程|指南|清单|步骤|流程|修复|救回|省下|砍掉|砍半|翻倍|反超|掉队|翻车|"
    r"凉|停|涨|降|免费|收费|放开|限制|接管|吞|抢|断|崩|漏|不及格|翻新|重写|重做|"
    r"跑|装|测|试|换|接回|搬|迁",
)

# 常见具体产品名（命中即视为"有工具"）；不在表里的英文专名也认（正则兜底）
KNOWN_TOOLS = {
    "WorkBuddy",
    "豆包",
    "Cursor",
    "ChatGPT",
    "GPT",
    "Claude",
    "Gemini",
    "Copilot",
    "DeepSeek",
    "Qwen",
    "千问",
    "通义",
    "文心",
    "Kimi",
    "智谱",
    "GLM",
    "Ollama",
    "LangChain",
    "MCP",
    "n8n",
    "Dify",
    "Coze",
    "扣子",
    "飞书",
    "Notion",
    "Figma",
    "Windsurf",
    "Replit",
    "Codex",
    "Sora",
    "Midjourney",
    "Seedream",
    "即梦",
    "可灵",
    "Llama",
    "Mistral",
    "Perplexity",
    "Manus",
    "Trae",
    "Trae",
    "PyCharm",
    "VS Code",
    "Excel",
    "Word",
    "PPT",
    "Docker",
    "Linux",
    "GitHub",
    "Whisper",
    "Runway",
}

_LATIN_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9\.\-]{2,}")
# "1.7B 模型""70B 跑在本地" —— 带规模数字的也算具体对象，否则会误杀好标题
_SIZE_RE = re.compile(r"\d+(?:\.\d+)?\s*[BbMmKk](?![A-Za-z])")

TITLE_MIN, TITLE_MAX = 14, 30


def has_tool_level_change(items) -> bool:
    """素材里是否有一条真的"工具级变化"（不是"模型又发了一版"）。"""
    for item in items or []:
        text = f"{getattr(item, 'title', '')} {getattr(item, 'description', '')}"
        if TOOL_CHANGE_RE.search(text):
            return True
    return False


def _has_tool_name(title: str) -> bool:
    if any(name in title for name in KNOWN_TOOLS):
        return True
    # "当 1.7B 模型跑在本地终端" 这类没写产品名但有明确对象/规模的，也放过
    return bool(_LATIN_NAME_RE.search(title) or _SIZE_RE.search(title))


def title_problems(title: str) -> List[str]:
    """返回标题的问题列表；空列表 = 合格。"""
    t = (title or "").strip()
    problems = []
    if not t:
        return ["标题为空"]
    if not (TITLE_MIN <= len(t) <= TITLE_MAX):
        problems.append(f"长度 {len(t)} 字，要求 {TITLE_MIN}–{TITLE_MAX}")
    if not _has_tool_name(t):
        problems.append("没有具体工具/产品名")
    if not ACTION_RE.search(t):
        problems.append("没有动作或变化词（怎么/接入/更新/涨/停…）")
    return problems


def has_copyable_block(spec: dict) -> bool:
    """至少一个"能照抄"的块：编号步骤，或 ≥3 条的清单。"""
    for section in (spec or {}).get("sections") or []:
        for block in section.get("blocks") or []:
            kind = block.get("type")
            items = block.get("items") or []
            if kind == "steps" and items:
                return True
            if kind == "bullets" and len(items) >= 3:
                return True
    return False
