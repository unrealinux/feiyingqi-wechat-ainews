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

# 定时运行
python main.py schedule
```

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

