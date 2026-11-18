"""素材相关性筛选：把与 AI 无关的热搜条去掉，再喂给模型。

问题很具体：百度热搜是通用榜，早上八点的素材里会混进
"养老金要崩盘""伊朗最高领袖"这类条目，20 条里真正跟 AI 沾边的可能只有一半。
这些噪声有两个坏处：
  1. 稀释选题——模型容易写成"三款模型并列"这种没主线的综述；
  2. 白烧 prompt token。
所以送进模型前先按 AI 相关词过一遍，并且限制条数上限。
"""

import re
from typing import List

# AI 领域词：命中任意一个即视为相关。宁可宽一点，别把真素材干掉。
AI_TERMS = [
    # 通用
    "AI",
    "AIGC",
    "人工智能",
    "大模型",
    "模型",
    "算法",
    "算力",
    "芯片",
    "GPU",
    "推理",
    "训练",
    "微调",
    "蒸馏",
    "多模态",
    "智能体",
    "Agent",
    "机器人",
    "自动驾驶",
    "生成式",
    "提示词",
    "向量",
    "开源",
    "API",
    "MCP",
    "Skill",
    "数据集",
    # 产品 / 公司
    "OpenAI",
    "GPT",
    "Claude",
    "Gemini",
    "Llama",
    "Mistral",
    "DeepSeek",
    "Qwen",
    "通义",
    "千问",
    "文心",
    "豆包",
    "Kimi",
    "智谱",
    "GLM",
    "混元",
    "星火",
    "Cursor",
    "Copilot",
    "Midjourney",
    "Sora",
    "可灵",
    "即梦",
    "Seedream",
    "英伟达",
    "Nvidia",
    "AMD",
    "台积电",
    "寒武纪",
    "商汤",
    "讯飞",
    "月之暗面",
    "具身",
    "Transformer",
    "AGI",
    "LLM",
    "NLP",
]

# 补漏（2026-11-17 实测漏掉的：「绿电进Token出」「Anthropic 上市」都是 AI 新闻）
AI_TERMS += ["Anthropic", "Token", "词元", "智算", "数据中心", "开源模型", "光模块"]

_AI_RE = re.compile("|".join(re.escape(t) for t in AI_TERMS), re.IGNORECASE)


def is_ai_related(item) -> bool:
    """标题或摘要里出现 AI 领域词就算相关。"""
    text = f"{getattr(item, 'title', '')} {getattr(item, 'description', '')}"
    return bool(_AI_RE.search(text))


def select_relevant(items: List, limit: int = 8) -> List:
    """筛出相关素材并截断到 limit 条。

    兜底：一条都匹配不上时返回原素材（不能因为词表漏了就让当天彻底没素材）。
    """
    items = list(items or [])
    kept = [x for x in items if is_ai_related(x)]
    if not kept:
        return items[:limit]
    return kept[:limit]
