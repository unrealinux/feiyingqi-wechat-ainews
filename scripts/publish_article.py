#!/usr/bin/env python3
"""
将AI热点文章发布到微信公众号草稿箱
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publisher import WeChatPublisher, publish_article
from src.config import load_config


# 文章内容
ARTICLE_TITLE = "AI热点速递 | 2026年3月22日"
ARTICLE_CONTENT = """# 🔥 AI热点速递 | 2026年3月22日

## 📌 今日核心事件（3句话总结）

1. **OpenAI发布GPT-5.4**，首次在通用模型中引入原生计算机操控能力，标志着AI从"对话工具"向"数字员工"的范式转变
2. **阿里巴巴成立ATH事业群并发布"悟空"平台**，将AI Agent能力内置到超2000万企业组织的钉钉中，企业级AI应用进入规模商用阶段
3. **英伟达GTC 2026大会发布Nemotron 3系列**，基于Blackwell架构的多模态模型吞吐量效率提升5倍，开源生态持续扩展

---

## 🚀 技术突破

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

## 📱 产品发布

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

## 📊 行业动态

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

## 🔮 趋势预测

**一句话预测**：2026年Q2将成为AI Agent商业化落地的关键窗口期，从"模型能力竞赛"转向"应用生态之争"，企业级AI原生平台（如阿里悟空）和原生计算机操控能力（如GPT-5.4）将重塑工作方式。

---

**数据来源**：OpenAI官方、新浪财经、网易科技、腾讯新闻、Fortune等公开报道
**编辑说明**：本文基于2026年3月公开信息整理，数据截至3月22日
"""

ARTICLE_DIGEST = "今日AI热点：OpenAI发布GPT-5.4支持计算机操控，阿里悟空平台正式亮相，英伟达Nemotron 3吞吐量提升5倍，谷歌Gemini 3数学推理达金牌水平"


def main():
    """主函数"""
    print("="*50)
    print("AI热点文章发布工具")
    print("="*50)
    
    # 检查配置
    config = load_config()
    wechat_config = config.get("wechat", {})
    app_id = wechat_config.get("app_id", "")
    app_secret = wechat_config.get("app_secret", "")
    
    if not app_id or app_id == "your_app_id_here":
        print("\n[ERROR] 微信公众号未配置")
        print("\n请先配置微信公众号凭据：")
        print("1. 编辑 config.yaml 文件")
        print("2. 填入你的 app_id 和 app_secret")
        print("3. 重新运行此脚本")
        print("\n或者，你可以使用以下命令配置：")
        print('  export WECHAT_APPID="your_app_id"')
        print('  export WECHAT_SECRET="your_app_secret"')
        
        # 保存到本地文件
        print("\n[Saving] 正在保存文章到本地文件...")
        save_to_local(ARTICLE_TITLE, ARTICLE_CONTENT)
        return
    
    # 发布到微信公众号
    print(f"\n[Title] 文章标题: {ARTICLE_TITLE}")
    print(f"[Words] 文章字数: {len(ARTICLE_CONTENT)} 字")
    print(f"[Author] 作者: {config.get('publish', {}).get('author', 'AI前沿观察')}")
    
    confirm = input("\n确认发布到微信公众号草稿箱? (y/n): ").strip().lower()
    if confirm != 'y':
        print("[Cancel] 已取消发布")
        # 保存到本地文件
        print("\n[Saving] 正在保存文章到本地文件...")
        save_to_local(ARTICLE_TITLE, ARTICLE_CONTENT)
        return
    
    print("\n[Publishing] 正在发布到微信公众号草稿箱...")
    
    result = publish_article(
        title=ARTICLE_TITLE,
        content=ARTICLE_CONTENT,
        author=config.get("publish", {}).get("author", "AI前沿观察"),
        digest=ARTICLE_DIGEST,
        auto_publish=False,  # 只创建草稿，不自动发布
        export_html=True  # 同时导出HTML文件
    )
    
    if result:
        print("\n[Success] 文章已成功发布到微信公众号草稿箱！")
        print("[Action] 请登录 mp.weixin.qq.com 查看并发布文章")
    else:
        print("\n[Error] 发布失败，请检查配置和网络连接")
        # 保存到本地文件
        print("\n[Saving] 正在保存文章到本地文件...")
        save_to_local(ARTICLE_TITLE, ARTICLE_CONTENT)


def save_to_local(title: str, content: str):
    """保存文章到本地文件"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    today = datetime.now().strftime("%Y%m%d")
    
    # 保存 Markdown 文件
    md_filename = output_dir / f"article_{today}.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] Markdown 文件已保存: {md_filename}")
    
    # 保存 HTML 文件
    publisher = WeChatPublisher()
    html_content = publisher.markdown_to_html(content)
    
    html_filename = output_dir / f"article_{today}.html"
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 677px; margin: 0 auto; padding: 20px; color: #333; }}
        h1, h2, h3 {{ margin: 20px 0; }}
        p {{ line-height: 1.8; margin: 15px 0; }}
        a {{ color: #1a73e8; }}
        blockquote {{ border-left: 3px solid #ddd; padding-left: 15px; color: #666; }}
        hr {{ border: none; border-top: 1px solid #eee; margin: 30px 0; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"  [OK] HTML 文件已保存: {html_filename}")
    
    print(f"\n[Tips] 配置好微信公众号后，可以使用以下命令发布：")
    print(f"  python publish_article.py")


if __name__ == "__main__":
    main()
