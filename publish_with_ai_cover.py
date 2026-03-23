#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布AI热点文章到微信公众号草稿箱 - 最终版
支持阿里Z-Image生成写实风格封面图
"""
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from src.config import load_config


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
    """创建草稿 - 修复Unicode编码问题"""
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


def generate_ai_cover_zimage(title, api_key):
    """
    使用阿里Z-Image生成写实风格封面图
    
    参考 FeiqingqiWechatMP 的实现
    """
    print("[AI Cover] 使用阿里Z-Image生成写实风格封面图...")
    
    # 写实风格的AI科技提示词
    prompt = f"""Professional photorealistic photograph of a modern AI data center interior.
Rows of glowing blue server racks with LED lights, dramatic lighting from above.
Holographic neural network visualization floating between the racks.
Cinematic lighting, 8K resolution, commercial photography style.
Blue and purple color scheme, high-tech atmosphere.
Article topic: {title}
No text overlay needed."""
    
    try:
        response = requests.post(
            "https://api.modelscope.cn/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "z-image-turbo",
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, cartoon, text, watermark, deformed, ugly",
                "steps": 8,
                "width": 1024,
                "height": 1024
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("data") and data["data"][0].get("image"):
                # 解码base64图片
                import base64
                image_data = base64.b64decode(data["data"][0]["image"])
                
                # 保存原始图片
                os.makedirs("output", exist_ok=True)
                original_path = "output/ai_cover_zimage_original.png"
                with open(original_path, "wb") as f:
                    f.write(image_data)
                print(f"[OK] AI原始图片已保存: {original_path}")
                
                # 调整大小为微信封面尺寸
                return resize_to_wechat_cover(original_path)
            else:
                print(f"[Error] 响应格式不正确: {data}")
        else:
            print(f"[Error] Z-Image API错误: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"[Error] Z-Image生成失败: {e}")
    
    return None


def resize_to_wechat_cover(input_path, output_path="cover.png"):
    """调整图片为微信封面尺寸 (900x383)"""
    try:
        from PIL import Image
        
        img = Image.open(input_path)
        
        # 裁剪为16:9比例，然后调整大小
        target_ratio = 900 / 383  # 约2.35:1
        img_ratio = img.width / img.height
        
        if img_ratio > target_ratio:
            # 图片太宽，按高度裁剪
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # 图片太高，按宽度裁剪
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # 调整大小
        img = img.resize((900, 383), Image.Resampling.LANCZOS)
        img.save(output_path, "PNG")
        print(f"[OK] 封面图已调整大小: {output_path}")
        return output_path
        
    except ImportError:
        # 如果没有PIL，直接复制
        import shutil
        shutil.copy(input_path, output_path)
        print(f"[Warning] PIL未安装，使用原图: {output_path}")
        return output_path


def generate_default_cover():
    """生成默认渐变封面图"""
    from create_cover_v2 import generate_cover
    return generate_cover("AI热点速递 | 2026年3月22日", "cover.png", "gradient_blue")


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
    print("AI热点文章发布工具 (Z-Image版)")
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
    
    # 检查Z-Image API配置
    zimage_api_key = config.get("zimage", {}).get("api_key", "")
    
    if zimage_api_key:
        print(f"\n[Config] 检测到阿里Z-Image API已配置")
        use_ai = input("是否使用AI生成写实风格封面图? (y/n, 默认y): ").strip().lower()
        use_ai_cover = use_ai != 'n'
    else:
        print("\n[Config] 未配置阿里Z-Image API，使用默认封面图")
        use_ai_cover = False
    
    try:
        print("\n[Step 1] 获取 access_token...")
        token = get_access_token(app_id, app_secret)
        print("[OK] access_token 获取成功")
        
        print("\n[Step 2] 生成封面图...")
        cover_path = "cover.png"
        
        if use_ai_cover and zimage_api_key:
            # 使用Z-Image生成写实风格封面
            ai_cover = generate_ai_cover_zimage(article_title, zimage_api_key)
            if not ai_cover:
                print("[Warning] AI生成失败，使用默认封面图")
                generate_default_cover()
        else:
            # 使用默认渐变封面
            generate_default_cover()
        
        print("[OK] 封面图准备完成")
        
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
