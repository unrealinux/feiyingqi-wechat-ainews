#!/usr/bin/env python3
"""
生成默认封面图并发布文章到微信公众号草稿箱
"""
import os
import sys
import requests
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config


def create_default_cover():
    """创建默认封面图"""
    # 检查是否已存在封面图
    if os.path.exists("cover.png"):
        print(f"[OK] 使用现有封面图: cover.png")
        return "cover.png"
    
    # 如果不存在，尝试使用PIL创建
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建一个 900x383 的图片（微信推荐尺寸）
        width, height = 900, 383
        img = Image.new('RGB', (width, height), color='#1a73e8')
        draw = ImageDraw.Draw(img)
        
        # 添加文字
        text = "AI热点速递"
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("arial.ttf", 80)
        except:
            # 如果没有找到字体，使用默认字体
            font = ImageFont.load_default()
        
        # 计算文字位置使其居中
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # 绘制文字
        draw.text((x, y), text, fill='white', font=font)
        
        # 保存图片
        cover_path = "cover.png"
        img.save(cover_path)
        print(f"[OK] 封面图已创建: {cover_path}")
        return cover_path
    except ImportError:
        print("[ERROR] PIL库未安装，请先运行: python create_cover.py")
        return None
    except Exception as e:
        print(f"[ERROR] 创建封面图失败: {e}")
        return None


def download_default_cover():
    """下载默认封面图"""
    try:
        # 使用一个简单的蓝色背景图片作为默认封面
        url = "https://via.placeholder.com/900x383/1a73e8/ffffff?text=AI+News"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            cover_path = "cover.png"
            with open(cover_path, "wb") as f:
                f.write(response.content)
            print(f"[OK] 封面图已下载: {cover_path}")
            return cover_path
        else:
            print(f"[ERROR] 下载封面图失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] 下载封面图失败: {e}")
        return None


def get_access_token(app_id: str, app_secret: str) -> str:
    """获取 access_token"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": app_id,
        "secret": app_secret
    }
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if "access_token" in data:
        return data["access_token"]
    else:
        raise Exception(f"获取 access_token 失败: {data}")


def upload_thumb(token: str, image_path: str) -> str:
    """上传封面图"""
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    params = {"access_token": token, "type": "thumb"}
    
    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, params=params, files=files, timeout=60)
        result = response.json()
    
    if result.get("media_id"):
        return result["media_id"]
    else:
        raise Exception(f"上传封面图失败: {result}")


def create_draft(token: str, title: str, content: str, thumb_media_id: str, author: str = "", digest: str = "") -> str:
    """创建草稿"""
    url = "https://api.weixin.qq.com/cgi-bin/draft/add"
    params = {"access_token": token}
    
    article = {
        "title": title,
        "author": author or "AI观察",
        "content": content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }
    
    # 只有在摘要不为空且长度不超过120个字符时才添加摘要
    if digest and len(digest) <= 120:
        article["digest"] = digest
    
    data = {"articles": [article]}
    
    response = requests.post(url, params=params, json=data, timeout=30)
    result = response.json()
    
    # 检查是否有 media_id 返回
    if result.get("media_id"):
        return result.get("media_id")
    else:
        raise Exception(f"创建草稿失败: {result}")


def markdown_to_html(markdown_text: str) -> str:
    """Markdown 转 HTML（微信公众号兼容）"""
    import re
    
    html = markdown_text
    
    # 标题
    html = re.sub(r'^### (.*?)$', r'<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2 style="font-size: 20px; color: #1a73e8; margin: 25px 0 15px; border-left: 4px solid #1a73e8; padding-left: 12px;">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1 style="font-size: 24px; color: #333; margin: 30px 0 20px; text-align: center;">\1</h1>', html, flags=re.MULTILINE)
    
    # 粗体和斜体
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong style="font-weight: bold;">\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # 链接
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" style="color: #1a73e8; text-decoration: underline;">\1</a>', html)
    
    # 引用
    html = re.sub(r'^> (.*?)$', r'<blockquote style="border-left: 3px solid #ddd; padding-left: 15px; margin: 15px 0; color: #666; font-style: italic;">\1</blockquote>', html, flags=re.MULTILINE)
    
    # 分隔线
    html = re.sub(r'^---$', r'<hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">', html, flags=re.MULTILINE)
    
    # 段落
    html = re.sub(r'\n\n', r'</p><p style="margin: 15px 0; line-height: 1.8;">', html)
    html = '<p style="margin: 15px 0; line-height: 1.8;">' + html + '</p>'
    
    # 清理空段落
    html = re.sub(r'<p style="margin: 15px 0; line-height: 1.8;"></p>', r'', html)
    html = re.sub(r'<p style="margin: 15px 0; line-height: 1.8;">(<h[123])', r'\1', html)
    html = re.sub(r'(</h[123]>)</p>', r'\1', html)
    html = re.sub(r'<p style="margin: 15px 0; line-height: 1.8;">(<hr)', r'\1', html)
    html = re.sub(r'(</hr>)</p>', r'\1', html)
    
    return html


# 文章内容
ARTICLE_TITLE = "AI热点速递 | 2026年3月22日"
ARTICLE_CONTENT = """# AI热点速递 | 2026年3月22日

## 今日核心事件（3句话总结）

1. **OpenAI发布GPT-5.4**，首次在通用模型中引入原生计算机操控能力，标志着AI从"对话工具"向"数字员工"的范式转变
2. **阿里巴巴成立ATH事业群并发布"悟空"平台**，将AI Agent能力内置到超2000万企业组织的钉钉中，企业级AI应用进入规模商用阶段
3. **英伟达GTC 2026大会发布Nemotron 3系列**，基于Blackwell架构的多模态模型吞吐量效率提升5倍，开源生态持续扩展

---

## 技术突破

### 1. OpenAI GPT-5.4：首个具备原生计算机操控能力的通用模型

**事件描述**：3月5日，OpenAI正式发布GPT-5.4，同步推出Thinking和Pro两个版本。该模型首次在通用大模型中引入原生计算机操控能力，支持百万Token上下文窗口，在GDPval知识工作评估中达到83.0%的得分率，较GPT-5.2提升12个百分点。

**影响分析**：
- **企业办公场景革新**：GPT-5.4可直接操作Excel、浏览器等软件，实现"对话即执行"的自动化工作流
- **Agent生态加速**：OSWorld计算机操控测试得分75.0%（GPT-5.2仅47.3%），为AI Agent大规模落地奠定基础
- **定价策略调整**：GPT-5.4输入价格$2.50/M tokens，较GPT-5.2上涨，但更高效率可降低总成本

**相关链接**：[OpenAI官方公告](http://openai.com/index/introducing-gpt-5-4/)

### 2. 英伟达Nemotron 3 Ultra：Blackwell架构加持的开源多模态模型

**事件描述**：3月17日GTC大会上，英伟达发布Nemotron 3系列全理解多模态模型。其中Nemotron 3 Ultra基于Blackwell架构，吞吐量效率较上代提升5倍，专为代码辅助和复杂工作流设计。同步推出的还有Nemotron 3 Omni（多模态整合）和Nemotron 3 VoiceChat（实时语音对话）。

**影响分析**：
- **开源生态强化**：上述模型已登陆GitHub和Hugging Face，开发者可通过NVIDIA NIM微服务部署
- **物理AI布局**：同步发布Cosmos 3世界基础模型、Isaac GR00T N1.7人形机器人模型，加速自主系统研发
- **算力效率提升**：5倍吞吐量提升将显著降低企业AI推理成本

**相关链接**：[GTC 2026发布详情](https://finance.sina.com.cn/tech/digi/2026-03-17/doc-inhrfshc8386407.shtml)

---

## 产品发布

### 3. 阿里"悟空"：企业级AI原生工作平台

**事件描述**：3月17日，阿里巴巴在成立Alibaba Token Hub（ATH）事业群次日，正式发布由钉钉团队打造的企业级AI原生工作平台"悟空"。该平台将直接内嵌到覆盖超2000万企业组织的钉钉体系中，同步推出AI能力市场，目标打造"全球最大的ToB Skill市场"。

**影响分析**：
- **B端AI应用提速**：悟空可自动继承企业权限规则，在安全沙箱中运行，解决企业AI落地的安全顾虑
- **生态整合效应**：淘宝、天猫、支付宝、阿里云等阿里系B端能力将以Skill形式逐步接入
- **竞争格局变化**：与腾讯QClaw、WorkBuddy等产品形成直接竞争，企业级Agent市场进入巨头混战阶段

**相关链接**：[悟空发布详情](https://www.163.com/dy/article/KO866PPO0519JFL1.html)

### 4. 谷歌Gemini 3 Deep Think：数学推理达到金牌水平

**事件描述**：3月18日，谷歌宣布对Gemini 3 Deep Think推理模型进行重大升级。在Humanity's Last Exam基准测试中达到48.4%准确率，ARC-AGI-2测试取得84.6%高分，数学奥林匹克达到金牌水平。新增草图转3D模型能力。

**影响分析**：
- **科学计算领域突破**：罗格斯大学数学家已利用该模型发现论文逻辑漏洞，杜克大学成功优化晶体生长方法
- **工程设计效率提升**：手绘草图直接生成3D打印文件，大幅缩短概念到原型的转化时间
- **API开放**：首次向部分研究人员、工程师及企业提供API早期访问权限

**相关链接**：[Gemini 3 Deep Think升级公告](https://k.sina.com.cn/article_7879848900_1d5acf3c401902sbo8.html)

### 5. 微软自研大模型MAI系列正式亮相

**事件描述**：3月20日，微软AI掌门人Mustafa Suleyman宣布推出两款自研大模型：语音模型MAI-Voice-1和通用模型MAI-1-preview。MAI-1-preview采用MoE架构，训练规模适中但更关注指令遵循和响应效率。

**影响分析**：
- **去OpenAI化信号**：长期以来微软主要依赖OpenAI模型，此次自研模型发布释放出降低依赖的明确信号
- **语音交互成为新战场**：MAI-Voice-1有望推动语音助手从"工具"升级为"数字伙伴"
- **生态开放**：微软表示将在Copilot及第三方测试平台开放模型

**相关链接**：[微软AI模型发布详情](https://k.sina.com.cn/article_7879848900_1d5acf3c401902tnd6.html)

---

## 行业动态

### 6. 腾讯混元3.0即将发布，全力押注AI Agent

**事件描述**：3月18日腾讯财报会议透露，混元HY 3.0正在内部业务测试中，计划4月对外推出。相比HY 2.0（406B参数、32B激活参数），新版本推理和Agent能力有显著提升。腾讯近期密集推出QClaw、WorkBuddy等"龙虾"产品矩阵。

**影响分析**：
- **国内大模型竞争加剧**：阿里悟空、腾讯混元3.0、百度文心一言等形成多方混战
- **Agent成为竞争焦点**：各大厂均将AI Agent作为核心战略方向
- **企业市场争夺**：腾讯侧重轻量化和便捷性，阿里强调安全和深度集成

**相关链接**：[腾讯混元3.0发布计划](https://finance.sina.com.cn/tech/roll/2026-03-18/doc-inhrmihr9284562.shtml)

### 7. Anthropic Claude Opus 4.5：编程能力超越人类候选人

**事件描述**：3月15日，Anthropic发布Claude Opus 4.5，在软件工程工作方面能力更强，成为首款在带回家工程任务上得分超过公司任何人类候选者的模型。同步推出Excel集成，企业客户可直接在电子表格中使用Claude。

**影响分析**：
- **编程助手市场洗牌**：Claude在代码生成和调试领域的领先地位进一步巩固
- **办公场景渗透**：Excel集成标志着AI从开发工具向通用办公软件扩展
- **安全争议**：Anthropic因拒绝军用AI被五角大楼列入黑名单，引发行业伦理讨论

**相关链接**：[Claude Opus 4.5发布详情](https://k.sina.com.cn/article_7879848900_1d5acf3c401902rvke.html)

---

## 趋势预测

**一句话预测**：2026年Q2将成为AI Agent商业化落地的关键窗口期，从"模型能力竞赛"转向"应用生态之争"，企业级AI原生平台（如阿里悟空）和原生计算机操控能力（如GPT-5.4）将重塑工作方式。

---

**数据来源**：OpenAI官方、新浪财经、网易科技、腾讯新闻、Fortune等公开报道
**编辑说明**：本文基于2026年3月公开信息整理，数据截至3月22日
"""

ARTICLE_DIGEST = "AI热点速递：OpenAI GPT-5.4、阿里悟空、英伟达Nemotron 3、谷歌Gemini 3"


def main():
    """主函数"""
    print("="*50)
    print("AI热点文章发布工具 (完整版)")
    print("="*50)
    
    # 获取配置
    config = load_config()
    wechat_config = config.get("wechat", {})
    app_id = wechat_config.get("app_id", "")
    app_secret = wechat_config.get("app_secret", "")
    
    if not app_id or app_id == "your_app_id_here":
        print("\n[ERROR] 微信公众号未配置")
        return
    
    print(f"\n[Title] 文章标题: {ARTICLE_TITLE}")
    print(f"[Words] 文章字数: {len(ARTICLE_CONTENT)} 字")
    print(f"[Author] 作者: {config.get('publish', {}).get('author', 'AI前沿观察')}")
    
    try:
        # 获取 access_token
        print("\n[Step 1] 获取 access_token...")
        token = get_access_token(app_id, app_secret)
        print("[OK] access_token 获取成功")
        
        # 创建或下载封面图
        print("\n[Step 2] 准备封面图...")
        cover_path = create_default_cover()
        if not cover_path:
            print("[ERROR] 无法创建封面图")
            return
        
        # 上传封面图
        print("\n[Step 3] 上传封面图...")
        thumb_media_id = upload_thumb(token, cover_path)
        print(f"[OK] 封面图上传成功，media_id: {thumb_media_id}")
        
        # 转换 Markdown 为 HTML
        print("\n[Step 4] 转换 Markdown 为 HTML...")
        html_content = markdown_to_html(ARTICLE_CONTENT)
        print("[OK] HTML 转换完成")
        
        # 创建草稿
        print("\n[Step 5] 创建草稿...")
        media_id = create_draft(
            token=token,
            title=ARTICLE_TITLE,
            content=html_content,
            thumb_media_id=thumb_media_id,
            author="AI观察"
        )
        print(f"[OK] 草稿创建成功！media_id: {media_id}")
        
        # 保存到本地
        print("\n[Step 6] 保存到本地文件...")
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        
        # 保存 Markdown
        md_filename = output_dir / f"article_{today}.md"
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(ARTICLE_CONTENT)
        print(f"[OK] Markdown 文件已保存: {md_filename}")
        
        # 保存 HTML
        html_filename = output_dir / f"article_{today}.html"
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[OK] HTML 文件已保存: {html_filename}")
        
        print("\n" + "="*50)
        print("[SUCCESS] 文章已成功发布到微信公众号草稿箱！")
        print("[Action] 请登录 mp.weixin.qq.com 查看并发布文章")
        print("="*50)
        
    except Exception as e:
        print(f"\n[ERROR] 发布失败: {e}")


if __name__ == "__main__":
    main()
