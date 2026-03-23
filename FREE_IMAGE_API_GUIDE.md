# 免费图片API配置指南

## API对比

| API | 注册地址 | 免费额度 | 特点 |
|-----|---------|---------|------|
| **Unsplash** | https://unsplash.com/developers | 50次/小时 | 高质量摄影图片 |
| **Pexels** | https://www.pexels.com/api/ | 200次/小时 | 免费商用图片 |
| **Pixabay** | https://pixabay.com/api/docs/ | 100次/分钟 | 免费图片库 |

## 推荐：Unsplash（最简单）

### 注册步骤

1. 访问 https://unsplash.com/developers
2. 点击 "Register as a Developer"
3. 填写应用信息：
   - Application name: AI News Cover Generator
   - Description: Generate cover images for AI news articles
4. 同意条款并注册
5. 创建应用后，复制 **Access Key**

### 配置

在 `config.yaml` 中添加：

```yaml
# 免费图片API配置
free_image:
  unsplash: "your_access_key_here"
```

## 备选：Pexels

### 注册步骤

1. 访问 https://www.pexels.com/api/
2. 点击 "Sign up for free"
3. 注册账号并验证邮箱
4. 进入 API 页面，获取 API Key
5. 复制 API Key

### 配置

```yaml
free_image:
  pexels: "your_api_key_here"
```

## 备选：Pixabay

### 注册步骤

1. 访问 https://pixabay.com/api/docs/
2. 点击 "Get Started"
3. 注册账号
4. 在 API 文档页面获取 API Key
5. 复制 API Key

### 配置

```yaml
free_image:
  pixabay: "your_api_key_here"
```

## 使用示例

```python
from src.free_image_api import generate_cover_from_free_api
from src.config import load_config

config = load_config()
free_image_config = config.get("free_image", {})

# 生成封面图
generate_cover_from_free_api(
    title="AI热点速递 | 2026年3月22日",
    style="datacenter",  # datacenter, chip, robot, neural, office
    output_path="cover.png",
    config=free_image_config,
    proxy="socks5://127.0.0.1:10808"  # 可选
)
```

## 支持的图片风格

| 风格 | 搜索关键词 | 适用场景 |
|------|-----------|---------|
| `datacenter` | server room data center technology | AI基础设施 |
| `chip` | processor chip circuit board technology | 芯片硬件 |
| `robot` | artificial intelligence robot futuristic | 机器人 |
| `neural` | neural network abstract technology | 神经网络 |
| `office` | modern tech office digital transformation | 科技办公 |

## 注意事项

1. **Unsplash** 需要代理访问（api.unsplash.com）
2. **Pexels** 和 **Pixabay** 国内可直接访问
3. 所有API的图片都可免费商用
4. 建议配置代理以获得更好的访问速度
