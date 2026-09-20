"""第三篇低频原创：AI找漏洞的速度，已经超过人类修补的速度
基于 ProPublica 2026-07-29 调查报道 + 21世纪经济报道
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, datetime

today = datetime.date.today().strftime("%Y-%m-%d")

html = f'''<section>

<div style="padding:30px;margin:20px 0;background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:16px;color:#f1f5f9;font-size:18px;line-height:2.2;word-wrap:break-word;">
<div style="font-size:15px;color:#60a5fa;margin-bottom:12px;text-transform:uppercase;letter-spacing:2px;">深度原创 · 基于 ProPublica 调查报道</div>
<div style="font-size:28px;font-weight:700;margin-bottom:16px;color:#f8fafc;line-height:1.4;">AI 找漏洞的速度，已经超过人类修补的速度</div>
<div style="font-size:18px;color:#94a3b8;">微软内部会议录音泄露：工程师们正在"疯狂冲刺"，但漏洞越补越多。</div>
</div>

<div style="padding:28px;margin:28px 0;background:#f8fafc;border-radius:14px;border:1px solid #e2e8f0;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#1e293b;margin:0 0 20px;padding-left:16px;border-left:5px solid #2563eb;">一封内部会议录音，揭开了整个行业的焦虑</div>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;">2026 年 5 月的一个下午，微软几十名工程师和经理聚集在雷德蒙德总部的一间会议室里，同时在线上开会。会议的主题是：如何应对一个叫 <b>Mythos</b> 的 AI 模型正在以史无前例的速度挖掘出微软产品中的安全漏洞。</p>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;">据 ProPublica 获得的会议录音和内部文件，一位经理在会上说：工程师们现在正处于<b>"疯狂冲刺"（a mad dash）</b>状态，试图修补 Mythos 挖出来的漏洞——但问题在于，<b>漏洞被发现的速度，已经超过了修补的速度</b>。</p>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;">Mythos 是 Anthropic 开发的前沿模型，目前以"Claude Mythos Preview"的形式，仅向少数选定机构开放。微软是其中之一。Anthropic 给微软约 50 名全职员工提供了访问权限，目标是<b>"在公开模型追上来之前，加固关键服务"</b>。</p>
</div>

<div style="padding:28px;margin:28px 0;background:#eff6ff;border-radius:14px;border:1px solid #bfdbfe;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#1e293b;margin:0 0 20px;padding-left:16px;border-left:5px solid #2563eb;">数字会说话</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0;">
<div style="padding:20px;background:#fff;border-radius:10px;border:1px solid #dbeafe;text-align:center;">
<div style="font-size:36px;font-weight:700;color:#dc2626;">90</div>
<div style="font-size:14px;color:#64748b;margin-top:4px;">critical 漏洞（仅 4 月，仅 SharePoint）</div>
</div>
<div style="padding:20px;background:#fff;border-radius:10px;border:1px solid #dbeafe;text-align:center;">
<div style="font-size:36px;font-weight:700;color:#ea580c;">141</div>
<div style="font-size:14px;color:#64748b;margin-top:4px;">important 漏洞（仅 4 月，仅 SharePoint）</div>
</div>
<div style="padding:20px;background:#fff;border-radius:10px;border:1px solid #dbeafe;text-align:center;">
<div style="font-size:36px;font-weight:700;color:#7c3aed;">600+</div>
<div style="font-size:14px;color:#64748b;margin-top:4px;">7 月 Patch Tuesday 修复数（历史新高）</div>
</div>
<div style="padding:20px;background:#fff;border-radius:10px;border:1px solid #dbeafe;text-align:center;">
<div style="font-size:36px;font-weight:700;color:#0891b2;">300+</div>
<div style="font-size:14px;color:#64748b;margin-top:4px;">中等严重度漏洞等待修补</div>
</div>
</div>

<p style="font-size:16px;line-height:2;color:#475569;margin:16px 0;text-indent:0;">微软内部文件显示，自年初使用 Mythos 以来，它在 Microsoft 365、Teams、Copilot 等产品中<b>累计发现了数百个 critical 和 important 级别漏洞</b>。截至 5 月中旬，大部分尚未修补。</p>

<p style="font-size:16px;line-height:2;color:#475569;margin:14px 0;text-indent:0;">6 月 Patch Tuesday 修了 200 多个，当时已是历史新高。7 月 14 日，微软一口气修了 <b>600 多个</b>——但其中只有 7 个是 low 或 moderate 级别。剩下的全是 important 或 critical。</p>

<p style="font-size:16px;line-height:2;color:#475569;margin:14px 0;text-indent:0;">微软对 ProPublica 表示：漏洞总量"短期内不会见顶"。</p>
</div>

<div style="padding:28px;margin:28px 0;background:#fffbeb;border-radius:14px;border:1px solid #fde68a;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#92400e;margin:0 0 20px;padding-left:16px;border-left:5px solid #f59e0b;">真正的危险不是单个漏洞，而是"串联"</div>

<p style="font-size:17px;line-height:2;color:#78350f;margin:14px 0;text-indent:0;">微软目前的策略是：先修 critical 和 important 的，moderate 的以后再说，low 的暂时不管。这听起来合理，但有一个致命盲区：<b>Mythos 能把多个低危漏洞串联成一个高危攻击链</b>。</p>

<p style="font-size:17px;line-height:2;color:#78350f;margin:14px 0;text-indent:0;">一个 low 级别的漏洞可能本身无关紧要。但当 Mythos 把三四个 low 漏洞串联起来——路径遍历 + 权限提升 + 信息泄露 + 远程执行——结果就是一个 critical 级别的完整攻击链。</p>

<p style="font-size:17px;line-height:2;color:#78350f;margin:14px 0;text-indent:0;">微软发言人回应称，漏洞串联"长期以来一直是漏洞评估和风险分析的一部分"。但内部文件显示，5 月的会议上<b>没有人提到串联风险</b>。</p>

<p style="font-size:16px;line-height:2;color:#92400e;margin:16px 0;text-indent:0;font-style:italic;">"如果低危漏洞一直不补，攻击者（或另一个 AI）只需要找到串联方式，就能发起灾难性攻击。"——ProPublica 评论</p>
</div>

<div style="padding:28px;margin:28px 0;background:#1e293b;border-radius:14px;color:#f1f5f9;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#f87171;margin:0 0 20px;padding-left:16px;border-left:5px solid #f87171;">一个窗口正在关闭</div>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">今年 4 月，Anthropic 公布了 Project Glasswing，引发了关于 AI 漏洞挖掘能力的全国性讨论。国家安全专家当时预测：美国会有一个<b>"窗口期"</b>——在对手也拥有类似模型之前，先修补漏洞。</p>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">6 月底，五眼联盟（美国、英国、加拿大、澳大利亚、新西兰）发布了一份罕见的联合声明，警告：<b>这个窗口正在以月为单位关闭</b>。</p>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">但微软内部文件显示，这一天可能已经到了。</p>

<p style="font-size:16px;line-height:2;color:#94a3b8;margin:16px 0;text-indent:0;">微软的 Microsoft Security Response Center（MSRC）长年人手不足。在 AI 漏洞潮之前，这个部门每月就要处理数百甚至上千份报告。现在，Mythos 一个模型一个月挖出来的漏洞，比过去整个团队一年处理的还多。</p>
</div>

<div style="padding:28px;margin:28px 0;background:#f0fdf4;border-radius:14px;border:1px solid #bbf7d0;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#166534;margin:0 0 20px;padding-left:16px;border-left:5px solid #22c55e;">讽刺的是：AI 既是矛，也是盾</div>

<p style="font-size:17px;line-height:2;color:#14532d;margin:14px 0;text-indent:0;">Mythos 的漏洞挖掘能力，本质上是一种<b>"矛"</b>——它能找到弱点，但修补工作仍然需要人类工程师来完成。而微软目前的修补速度，明显跟不上。</p>

<p style="font-size:17px;line-height:2;color:#14532d;margin:14px 0;text-indent:0;">同时，微软也在用 AI 做<b>"盾"</b>——AI 驱动的漏洞分类和优先级排序。微软对 ProPublica 表示，公司"在人员和 AI 驱动的分类解决方案上投入了大量资金，以快速处理不断增长的漏洞数量"。</p>

<p style="font-size:17px;line-height:2;color:#14532d;margin:14px 0;text-indent:0;">问题在于：当矛的挖掘速度指数级增长，而盾的修补速度线性增长时，交叉点在哪？</p>
</div>

<div style="padding:28px;margin:28px 0;background:#1e293b;border-radius:14px;color:#f1f5f9;word-wrap:break-word;">
<div style="font-weight:700;color:#f87171;font-size:22px;margin-bottom:16px;">写在最后</div>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">微软对 ProPublica 的回应中有一句话值得反复品味：</p>

<div style="padding:16px 20px;margin:16px 0;background:rgba(248,113,113,0.1);border-radius:8px;border-left:4px solid #f87171;">
<p style="font-size:16px;line-height:2;color:#fca5a5;margin:0;font-style:italic;">"随着这些 AI 系统的出现，让我们重新思考其中一些东西。整个行业都在关注，这将带来多大的改变。"</p>
</div>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">翻译成大白话：<b>我们还没准备好</b>。</p>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">Mythos 挖漏洞的速度，已经超过了微软——全球最大的软件公司之一——修补漏洞的速度。而 Mythos 只是一个模型。当更多类似的模型公开可用，当对手也掌握了同样的能力，我们每天使用的软件，还能安全多久？</p>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">这不是科幻。这是 2026 年 7 月 29 日的新闻。</p>
</div>

<div style="padding:20px;margin:28px 0;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;word-wrap:break-word;">
<div style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 12px;">事实来源（均可查证）</div>
<p style="font-size:14px;color:#64748b;line-height:1.9;margin:8px 0;">• ProPublica，2026-07-29，《Anthropic's Claude Mythos 'breaks' AES encryption… Microsoft Struggling With Hundreds of AI-Discovered Security Bugs》<br>
• Ars Technica，2026-07-29，《Anthropic is finding bugs faster than Microsoft can fix them》<br>
• The Verge，2026-07-29，《OpenAI's rogue AI agent didn't stop at hacking Hugging Face》<br>
• 21世纪经济报道，2026-07-29，《全球首例AI自主攻击受害方披露细节》<br>
• 五眼联盟联合声明，2026-06（cyber.gov.au 发布）</p>
</div>

</section>'''

os.makedirs("output", exist_ok=True)
out = f"output/sample_mythos_vs_msft_{today}.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("预览已生成:", out)
print("标题: AI 找漏洞的速度，已经超过人类修补的速度")
print("字数(约):", len(html)//2)
