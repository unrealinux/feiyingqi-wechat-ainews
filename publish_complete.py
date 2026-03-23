#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布AI热点文章到微信公众号草稿箱 - 完整版
支持多种封面图生成方式：
1. 免费图片API (Unsplash/Pexels/Pixabay)
2. AI生成 (智谱AI/Z-Image)
3. 渐变降级
"""
import os
import sys
import json
import base64
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.config import load_config

# 代理配置
PROXY_SOCKS5 = "socks5://127.0.0.1:10808"


def get_access_token(app_id, app_secret):
    """获取access_token"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {"grant_type": "client_credential", "appid": app_id, "secret": app_secret}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    if "access_token" in data:
        return data["access_token"]
    raise Exception(f"获取access_token失败: {data}")


def upload_thumb(token, image_path):
    """上传封面图"""
    url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
    params = {"access_token": token, "type": "thumb"}
    with open(image_path, "rb") as f:
        files = {"media": f}
        response = requests.post(url, params=params, files=files, timeout=60)
        result = response.json()
    if result.get("media_id"):
        return result["media_id"]
    raise Exception(f"上传封面图失败: {result}")


def create_draft(token, title, content, thumb_media_id, author):
    """创建草稿"""
    url = "https://api.weixin.qq.com/cgi-bin/draft/add"
    
    article = {
        "title": title,
        "author": author,
        "content": content,
        "content_source_url": "",
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 0,
        "only_fans_can_comment": 0
    }
    
    data = {"articles": [article]}
    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    headers = {"Content-Type": "application/json; charset=utf-8"}
    
    response = requests.post(
        url, 
        params={"access_token": token},
        data=json_data,
        headers=headers,
        timeout=30
    )
    result = response.json()
    
    if result.get("media_id"):
        return result["media_id"]
    raise Exception(f"创建草稿失败: {result}")


def generate_cover_free_image(title, config, proxy=None):
    """
    使用免费图片API生成封面图
    
    支持：Unsplash、Pexels、Pixabay
    """
    from src.free_image_api import FreeImageAPI, resize_to_wechat_cover, add_text_overlay
    
    free_image_config = config.get("free_image", {})
    
    if not any(free_image_config.get(k) for k in ["unsplash", "pexels", "pixabay"]):
        print("[Info] 未配置免费图片API")
        return None
    
    print("[Cover] 使用免费图片API生成封面图...")
    
    api = FreeImageAPI(free_image_config, proxy)
    
    # 搜索科技风格图片
    image_data = api.search_tech_image("datacenter")
    
    if image_data:
        # 保存原始图片
        original_path = "output/free_image_original.png"
        os.makedirs("output", exist_ok=True)
        with open(original_path, "wb") as f:
            f.write(image_data)
        
        # 调整大小
        resize_to_wechat_cover(original_path, "cover.png")
        
        # 添加文字叠加
        add_text_overlay("cover.png", title)
        
        return "cover.png"
    
    return None


def generate_cover_ai(title, config, proxy=None):
    """
    使用AI生成封面图
    
    支持：智谱AI、阿里Z-Image
    """
    zhipu_key = config.get("zhipu", {}).get("api_key", "")
    zimage_key = config.get("zimage", {}).get("api_key", "")
    
    if not zhipu_key and not zimage_key:
        print("[Info] 未配置AI图片生成API")
        return None
    
    # 尝试智谱AI（国内，无需代理）
    if zhipu_key and zhipu_key.startswith("sk-"):
        print("[Cover] 尝试智谱AI CogView...")
        try:
            from src.ai_cover_generator import generate_ai_cover
            path, provider = generate_ai_cover(
                title=title,
                element="datacenter",
                output_path="cover.png",
                config=config,
                proxy=None  # 智谱AI无需代理
            )
            if path:
                return path
        except Exception as e:
            print(f"[Warning] 智谱AI失败: {e}")
    
    # 尝试阿里Z-Image（需要代理）
    if zimage_key and proxy:
        print("[Cover] 尝试阿里Z-Image...")
        try:
            import socks
            import socket
            
            # 设置SOCKS5代理
            socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 10808)
            socket.socket = socks.socksocket
            
            # 生成封面图
            from src.ai_cover_generator import generate_ai_cover
            path, provider = generate_ai_cover(
                title=title,
                element="datacenter",
                output_path="cover.png",
                config=config,
                proxy=None
            )
            if path:
                return path
        except Exception as e:
            print(f"[Warning] 阿里Z-Image失败: {e}")
    
    return None


def generate_cover_gradient(title):
    """生成渐变封面图（降级方案）"""
    from create_cover_v2 import generate_cover
    return generate_cover(title, "cover.png", "gradient_blue")


def generate_cover(title, config, proxy=None):
    """
    智能生成封面图
    
    优先级：免费图片API > AI生成 > 渐变降级
    """
    # 1. 尝试免费图片API
    cover = generate_cover_free_image(title, config, proxy)
    if cover:
        return cover
    
    # 2. 尝试AI生成
    cover = generate_cover_ai(title, config, proxy)
    if cover:
        return cover
    
    # 3. 渐变降级
    print("[Cover] 使用渐变降级方案")
    return generate_cover_gradient(title)


# 文章HTML内容
ARTICLE_HTML = '''<section style="margin: 15px 0; line-height: 1.8;">
<h1 style="font-size: 24px; color: #333; margin: 30px 0 20px; text-align: center;">AI热点速递 | 2026年3月22日</h1>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h2 style="font-size: 20px; color: #1a73e8; margin: 25px 0 15px; border-left: 4px solid #1a73e8; padding-left: 12px;">今日核心事件</h2>
<p style="margin: 15px 0; line-height: 1.8;">1. <strong style="font-weight: bold;">OpenAI发布GPT-5.4</strong>，首次在通用模型中引入原生计算机操控能力，标志着AI从"对话工具"向"数字员工"的范式转变</p>
<p style="margin: 15px 0; line-height: 1.8;">2. <strong style="font-weight: bold;">阿里巴巴成立ATH事业群并发布"悟空"平台</strong>，将AI Agent能力内置到超2000万企业组织的钉钉中，企业级AI应用进入规模商用阶段</p>
<p style="margin: 15px 0; line-height: 1.8;">3. <strong style="font-weight: bold;">英伟达GTC 2026大会发布Nemotron 3系列</strong>，基于Blackwell架构的多模态模型吞吐量效率提升5倍，开源生态持续扩展</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h2 style="font-size: 20px; color: #1a73e8; margin: 25px 0 15px; border-left: 4px solid #1a73e8; padding-left: 12px;">技术突破</h2>
<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">1. OpenAI GPT-5.4：首个具备原生计算机操控能力的通用模型</h3>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">事件描述：</strong>3月5日，OpenAI正式发布GPT-5.4，同步推出Thinking和Pro两个版本。该模型首次在通用大模型中引入原生计算机操控能力，支持百万Token上下文窗口，在GDPval知识工作评估中达到83.0%的得分率，较GPT-5.2提升12个百分点。</p>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">影响分析：</strong></p>
<p style="margin: 15px 0; line-height: 1.8;">- 企业办公场景革新：GPT-5.4可直接操作Excel、浏览器等软件，实现"对话即执行"的自动化工作流</p>
<p style="margin: 15px 0; line-height: 1.8;">- Agent生态加速：OSWorld计算机操控测试得分75.0%（GPT-5.2仅47.3%），为AI Agent大规模落地奠定基础</p>
<p style="margin: 15px 0; line-height: 1.8;">- 定价策略调整：GPT-5.4输入价格$2.50/M tokens，较GPT-5.2上涨，但更高效率可降低总成本</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">2. 英伟达Nemotron 3 Ultra：Blackwell架构加持的开源多模态模型</h3>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">事件描述：</strong>3月17日GTC大会上，英伟达发布Nemotron 3系列全理解多模态模型。其中Nemotron 3 Ultra基于Blackwell架构，吞吐量效率较上代提升5倍，专为代码辅助和复杂工作流设计。</p>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">影响分析：</strong></p>
<p style="margin: 15px 0; line-height: 1.8;">- 开源生态强化：上述模型已登陆GitHub和Hugging Face，开发者可通过NVIDIA NIM微服务部署</p>
<p style="margin: 15px 0; line-height: 1.8;">- 物理AI布局：同步发布Cosmos 3世界基础模型、Isaac GR00T N1.7人形机器人模型，加速自主系统研发</p>
<p style="margin: 15px 0; line-height: 1.8;">- 算力效率提升：5倍吞吐量提升将显著降低企业AI推理成本</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h2 style="font-size: 20px; color: #1a73e8; margin: 25px 0 15px; border-left: 4px solid #1a73e8; padding-left: 12px;">产品发布</h2>
<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">3. 阿里"悟空"：企业级AI原生工作平台</h3>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">事件描述：</strong>3月17日，阿里巴巴在成立Alibaba Token Hub（ATH）事业群次日，正式发布由钉钉团队打造的企业级AI原生工作平台"悟空"。该平台将直接内嵌到覆盖超2000万企业组织的钉钉体系中，同步推出AI能力市场，目标打造"全球最大的ToB Skill市场"。</p>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">影响分析：</strong></p>
<p style="margin: 15px 0; line-height: 1.8;">- B端AI应用提速：悟空可自动继承企业权限规则，在安全沙箱中运行，解决企业AI落地的安全顾虑</p>
<p style="margin: 15px 0; line-height: 1.8;">- 生态整合效应：淘宝、天猫、支付宝、阿里云等阿里系B端能力将以Skill形式逐步接入</p>
<p style="margin: 15px 0; line-height: 1.8;">- 竞争格局变化：与腾讯QClaw、WorkBuddy等产品形成直接竞争，企业级Agent市场进入巨头混战阶段</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">4. 谷歌Gemini 3 Deep Think：数学推理达到金牌水平</h3>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">事件描述：</strong>3月18日，谷歌宣布对Gemini 3 Deep Think推理模型进行重大升级。在Humanity's Last Exam基准测试中达到48.4%准确率，ARC-AGI-2测试取得84.6%高分，数学奥林匹克达到金牌水平。新增草图转3D模型能力。</p>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">影响分析：</strong></p>
<p style="margin: 15px 0; line-height: 1.8;">- 科学计算领域突破：罗格斯大学数学家已利用该模型发现论文逻辑漏洞，杜克大学成功优化晶体生长方法</p>
<p style="margin: 15px 0; line-height: 1.8;">- 工程设计效率提升：手绘草图直接生成3D打印文件，大幅缩短概念到原型的转化时间</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h2 style="font-size: 20px; color: #1a73e8; margin: 25px 0 15px; border-left: 4px solid #1a73e8; padding-left: 12px;">行业动态</h2>
<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">5. 腾讯混元3.0即将发布，全力押注AI Agent</h3>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">事件描述：</strong>3月18日腾讯财报会议透露，混元HY 3.0正在内部业务测试中，计划4月对外推出。相比HY 2.0（406B参数、32B激活参数），新版本推理和Agent能力有显著提升。</p>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">影响分析：</strong></p>
<p style="margin: 15px 0; line-height: 1.8;">- 国内大模型竞争加剧：阿里悟空、腾讯混元3.0、百度文心一言等形成多方混战</p>
<p style="margin: 15px 0; line-height: 1.8;">- Agent成为竞争焦点：各大厂均将AI Agent作为核心战略方向</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h3 style="font-size: 18px; color: #333; margin: 20px 0 10px;">6. Anthropic Claude Opus 4.5：编程能力超越人类候选人</h3>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">事件描述：</strong>3月15日，Anthropic发布Claude Opus 4.5，在软件工程工作方面能力更强，成为首款在带回家工程任务上得分超过公司任何人类候选者的模型。</p>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">影响分析：</strong></p>
<p style="margin: 15px 0; line-height: 1.8;">- 编程助手市场洗牌：Claude在代码生成和调试领域的领先地位进一步巩固</p>
<p style="margin: 15px 0; line-height: 1.8;">- 办公场景渗透：Excel集成标志着AI从开发工具向通用办公软件扩展</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<h2 style="font-size: 20px; color: #1a73e8; margin: 25px 0 15px; border-left: 4px solid #1a73e8; padding-left: 12px;">趋势预测</h2>
<p style="margin: 15px 0; line-height: 1.8;"><strong style="font-weight: bold;">一句话预测：</strong>2026年Q2将成为AI Agent商业化落地的关键窗口期，从"模型能力竞赛"转向"应用生态之争"，企业级AI原生平台和原生计算机操控能力将重塑工作方式。</p>
</section>

<section style="margin: 15px 0; line-height: 1.8;">
<p style="margin: 15px 0; line-height: 1.8; color: #999; font-size: 12px;">数据来源：OpenAI官方、新浪财经、网易科技、腾讯新闻、Fortune等公开报道</p>
<p style="margin: 15px 0; line-height: 1.8; color: #999; font-size: 12px;">编辑说明：本文基于2026年3月公开信息整理，数据截至3月22日</p>
</section>'''


def main():
    print("=" * 50)
    print("AI热点文章发布工具 (完整版)")
    print("=" * 50)
    
    config = load_config()
    wechat_config = config.get("wechat", {})
    app_id = wechat_config.get("app_id", "")
    app_secret = wechat_config.get("app_secret", "")
    
    if not app_id or app_id == "your_app_id_here":
        print("\n[ERROR] 微信公众号未配置")
        return
    
    article_title = "AI热点速递 | 2026年3月22日"
    article_author = "AI观察"
    
    print(f"\n[Title] 文章标题: {article_title}")
    print(f"[Author] 作者: {article_author}")
    
    # 检查可用的封面图生成方式
    free_image_config = config.get("free_image", {})
    has_free_image = any(free_image_config.get(k) for k in ["unsplash", "pexels", "pixabay"])
    has_ai = config.get("zhipu", {}).get("api_key", "").startswith("sk-") or config.get("zimage", {}).get("api_key")
    
    print(f"\n[Cover] 可用的封面图生成方式:")
    print(f"  - 免费图片API: {'已配置' if has_free_image else '未配置'}")
    print(f"  - AI生成: {'已配置' if has_ai else '未配置'}")
    print(f"  - 渐变降级: 可用")
    
    try:
        print("\n[Step 1] 获取 access_token...")
        token = get_access_token(app_id, app_secret)
        print("[OK] access_token 获取成功")
        
        print("\n[Step 2] 生成封面图...")
        cover_path = generate_cover(article_title, config, PROXY_SOCKS5)
        print(f"[OK] 封面图生成完成: {cover_path}")
        
        print("\n[Step 3] 上传封面图...")
        thumb_media_id = upload_thumb(token, cover_path)
        print("[OK] 封面图上传成功")
        
        print("\n[Step 4] 创建草稿...")
        media_id = create_draft(
            token=token,
            title=article_title,
            content=ARTICLE_HTML,
            thumb_media_id=thumb_media_id,
            author=article_author
        )
        print(f"[OK] 草稿创建成功！media_id: {media_id}")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] 文章已成功发布到微信公众号草稿箱！")
        print("[Action] 请登录 mp.weixin.qq.com 查看并发布文章")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n[ERROR] 发布失败: {e}")


if __name__ == "__main__":
    main()
