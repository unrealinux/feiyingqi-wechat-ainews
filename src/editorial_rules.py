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

# 动作/变化词：软指标，只在把打回原因写给人看时用（不单独做硬性拦截）。
# 早期版本要求"标题必须含动作词"，结果 2026-11-16 把
# 「DeepSeek 限额、GPT-6.2 延期」这种完全正常的标题也拦了两次——真实标题的动词
# 太发散（延期/限额/翻倍/改名…），白名单列不完，硬卡只会误杀。
ACTION_RE = re.compile(
    r"怎么|如何|为什么|能不能|要不要|上手|接入|配置|设置|迁移|替换|避坑|踩坑|跑通|闭环|"
    r"实操|实战|教程|指南|清单|步骤|流程|修复|救回|省下|砍掉|砍半|翻倍|反超|掉队|翻车|"
    r"凉|停|涨|降|免费|收费|放开|限制|限额|延期|推迟|提前|下线|关停|合并|改名|接管|吞|抢|"
    r"断|崩|漏|不及格|翻新|重写|重做|跑|装|测|试|换|接回|搬|迁|发布|上线|开源|开源|收费",
)

# 泛趋势/日报腔：数据上最差的一类（阅读 0–6），直接拦。
# 依据：54 篇里"三款模型…""AI工具这周换了三件事"这类标题阅读都在个位数。
ROUNDUP_RE = re.compile(
    r"日报|速递|盘点|综述|这周|本周|一周|近期|三款|三个|五种|多项|大厂|趋势|展望|研判|"
    r"观察|浅谈|漫谈|生态|格局|上半场|下半场|未来已来|可以预见",
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
    """返回标题的问题列表；空列表 = 合格。

    硬条件只有两条（都能从 54 篇数据里指出来源）：
      · 必须有具体工具/产品名（含工具词中位 35 vs 不含 11）
      · 不能是泛趋势/日报腔（这批阅读 0–6）
    另外长度卡 14–30（本号 105 阅读那篇是 18 字，21–28 会误杀）。
    动作词只作提示，不单独拦截——真实标题的动词太发散，硬卡会误杀正常标题
    （2026-11-16 08:00 就因为这条连拦两稿）。
    """
    t = (title or "").strip()
    problems = []
    if not t:
        return ["标题为空"]
    if not (TITLE_MIN <= len(t) <= TITLE_MAX):
        problems.append(f"长度 {len(t)} 字，要求 {TITLE_MIN}–{TITLE_MAX}")
    if not _has_tool_name(t):
        problems.append("没有具体工具/产品名")
    hit = ROUNDUP_RE.search(t)
    if hit:
        problems.append(f"泛趋势/日报腔（「{hit.group(0)}」），读者没有落点")
    return problems


def candidate_tools(items, limit: int = 6) -> List[str]:
    """从素材里挑出可以写进标题的具体工具/产品名（给重写提示用，不引入素材外的东西）。"""
    found: List[str] = []
    for item in items or []:
        text = f"{getattr(item, 'title', '')} {getattr(item, 'description', '')}"
        for name in KNOWN_TOOLS:
            if name in text and name not in found:
                found.append(name)
        for token in _LATIN_NAME_RE.findall(text):
            if token not in found and not token.isdigit():
                found.append(token)
    return found[:limit]


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
