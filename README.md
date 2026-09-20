# AI News Publisher 2.0 🚀

全网 AI 资讯聚合自动发布到微信公众号的智能 Agent

## ✨ 全新特性

### 🚀 性能优化
- **并发获取** - 多线程并发获取多个新闻源，速度提升 5-10 倍
- **智能重试** - 自动重试失败的网络请求
- **缓存机制** - Token 缓存，减少 API 调用

### 📰 多源支持
- **搜索引擎** - Exa API 专业搜索
- **RSS 订阅** - OpenAI, 36kr, 量子位等
- **HackerNews** - AI 相关热门讨论
- **新闻网站** - 量子位，机器之心等

### 📝 内容生成
- **AI 智能摘要** - 使用 GPT-4 生成专业文章
- **自动分类** - 按公司/主题分类
- **精美排版** - Markdown + HTML 双格式

### 💬 微信发布
- **草稿箱** - 自动创建微信草稿
- **HTML 转换** - 微信公众号兼容格式
- **本地备份** - MD 和 HTML 双格式保存

---

## 📦 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml`：

```yaml
wechat:
  app_id: "你的微信公众号 AppID"
  app_secret: "你的微信公众号 AppSecret"

openai:
  api_key: "你的 OpenAI API Key"
  model: "gpt-4o-mini"

news:
  search_keywords:
    - "AI 人工智能"
    - "OpenAI GPT"
    - "LLM 大语言模型"
  max_news: 15
  
  sources:
    search: true
    rss: false
    hackernews: false
    websites: false

scheduler:
  enabled: false
  time: "08:00"
```

### 3. 运行

```bash
# 测试模式
python main.py test

# 手动运行
python main.py run

# 定时运行（常驻进程，需一直挂着）
python main.py schedule

# 单次定时流程（供 Windows 任务计划调用：仅建草稿，不群发）
python main.py daily
```

### 4. 定时任务（Windows 任务计划）

生产环境用 Windows 任务计划拉起 `python main.py daily`，**每 2 天 08:00 跑一次，只创建草稿不群发**（`create_draft`；`publish_draft` 群发必须人工授权）。

```powershell
# 注册/更新任务（幂等，可重复执行）
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\win\register-task.ps1
```

- 任务名：`FeiqingqiWechatAINews-Draft`
- 入口：`scripts\win\run-daily.cmd`（由 `run-hidden.vbs` 隐藏窗口调用）
- 日志：`logs\daily-publish.log`（超过 1MB 自动轮转）
- 退出码：`0` 成功 / `1` 流水线失败 / `127` 环境错误（找不到 python 或 main.py）
- 提醒：微信 API 有 IP 白名单，换网络后需先在公众号后台加白名单，否则草稿创建会失败
- 发布前先看本地预览：`python main.py daily --dry-run`（跑完整流程但不建草稿）

### 5. 文章排版（深读体）

正文由 `src/editorial_template.py` 按固定母版渲染（取自 2026-09-10 《OpenAI 秀出来的 99.9%…》那篇）：米白底 + 砖红/墨绿双色，报头 → 主副标题 → 开头 → 壹～陆 章节（数据卡/条形图/要点列表）→ 双线红框收束 → 编号来源清单 → 落款。

**LLM 只产出内容字段（JSON），HTML 由本地拼装**，避免模型手写 CSS 导致各篇观感漂移。

三道质量闸门（均对齐 AGENTS.md 的“禁编造、可溯源”）：

| 闸门 | 行为 |
|---|---|
| `ground_numeric_blocks` | 图表/数据卡里的数字必须在新闻素材里真实存在，否则**直接删掉**（模型很爱为了图表好看自编百分比） |
| `find_blacklisted_terms` | 译名雷区（如 mouse 被误译为“鼠标”）命中则整篇重生成 |
| `find_ungrounded_numbers` | 正文里素材未出现的数字 → **日志告警**，供人工复核（不阻断，不篡改行文） |

报头日期由 `normalize_meta_date()` 本地强行改成当天，不依赖模型配合。

### 5. 封面图

定时任务生成的封面是**纯图，不叠任何文字**（标题/署名/日期一律不上图，图下标题由微信自己显示）。

- 背景用 Agnes 文生图生成 AI 相关实拍质感画面（数据中心 / 芯片 / 机械臂 / 实验室 / 神经网络 / 工作台），输出 1440×810。
- 主题按标题关键词自动挑选，未命中时按日期轮换，避免每期同一张图造成模板化观感。
- 出图提示词里显式排除了文字、水印、人脸。
- 出图或合成失败会**自动降级**回本地渐变背景（同样无文字，`generate_gradient_cover(..., with_text=False)`），不会中断发布。
- 手动生成一张：`python -c "import sys;sys.path.insert(0,'.');from src.ai_photo_cover import generate_ai_photo_cover;print(generate_ai_photo_cover('标题'))"`
  - 需要带标题的文字版：追加 `with_text=True`

---

## 📂 输出文件

```
output/
├── article_20240124.md
└── article_20240124.html
```

---

## 🔧 高级配置

### 使用 Exa 搜索

```bash
export EXA_API_KEY="your_exa_api_key"
```

---

## 🆚 2.0 vs 1.0

| 功能 | v1.0 | v2.0 |
|------|------|------|
| 并发获取 | ❌ | ✅ |
| 错误重试 | ❌ | ✅ |
| 日志系统 | ❌ | ✅ |
| HTML 导出 | ❌ | ✅ |
| 运行时间 | ~60s | ~5-10s |

---

## 🔍 故障排除

**微信公众号发布失败**
1. 检查 AppID 和 AppSecret
2. 确认服务器 IP 已加入白名单

**获取不到新闻**
1. 检查网络连接
2. 配置 Exa API Key

