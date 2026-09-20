"""热点文章：GLM-5.3 追上"危险能力"，然后选择暂扣权重
OpenAI 暂停 Astra 一周后，中国开源模型在漏洞发现上追平前沿
基于 SiliconANGLE / Decrypt / Marc Pope 分析 / Infosecurity Magazine 等 2026-08-14~08-20 报道
全文字体统一深色，浅色背景，便于阅读
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, datetime

today = datetime.date.today().strftime("%Y-%m-%d")

html = f'''<section>

<div style="padding:30px;margin:20px 0;background:linear-gradient(135deg,#f0fdfa,#e0f2fe);border-radius:16px;color:#1f2937;font-size:18px;line-height:2.2;word-wrap:break-word;">
<div style="font-size:15px;color:#0f766e;margin-bottom:12px;text-transform:uppercase;letter-spacing:2px;">刹车的另一面</div>
<div style="font-size:27px;font-weight:700;margin-bottom:16px;color:#0f172a;line-height:1.4;">它找到了2436个漏洞，然后决定先不发</div>
<div style="font-size:19px;color:#334155;">OpenAI 因为"可能具备危险能力"暂停训练一周后，中国开源模型 GLM-5.3 公开交出了成绩单。</div>
</div>

<div style="padding:28px;margin:28px 0;background:#f0fdfa;border-radius:14px;border:1px solid #99f6e4;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#0f766e;margin:0 0 20px;padding-left:16px;border-left:5px solid #0d9488;">一个40年前写的漏洞</div>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">8 月 14 日，中国 AI 实验室 Z.ai 发布了开源模型 <b>GLM-5.3</b>。它在新闻稿里列了一串数字：<b>在 269 个软件项目中发现了超过 2400 个漏洞，其中约一半是中高危</b>。最引人注目的一个，藏在<b>一段 40 年前编写的代码</b>里。</p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">同一周，大洋彼岸的 OpenAI 刚刚因为另一件事上了头条：8 月 7 日，它宣布暂停下一代模型 Astra 的强化学习训练，原因是内部评估认为 Astra 的能力触及了公司安全框架里定义的<b>"关键级网络安全"门槛</b>——一个模型能自主发现并利用真实系统中的漏洞，甚至自主设计完整的攻击策略。</p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">把两件事放在一起看，结论很直接：<b>OpenAI 因为"可能做到"而按下暂停的能力，一家中国开源实验室已经公开宣布"做到了"。</b></p>
</div>

<div style="padding:28px;margin:28px 0;background:#ecfdf5;border-radius:14px;border:1px solid #a7f3d0;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#047857;margin:0 0 20px;padding-left:16px;border-left:5px solid #059669;">分数不会说谎：三家追平了</div>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">CyberGym 是测试 AI 自主漏洞发现能力的基准。8 月 14 日之后的数据是这样的：</p>

<div style="padding:16px 20px;margin:16px 0;background:#ffffff;border-radius:10px;border:1px solid #059669;">
<p style="font-size:17px;line-height:2;color:#1f2937;margin:8px 0;">• <b>GLM-5.3（Z.ai，开源）: 84.5%</b><br>
• Claude Mythos 5（Anthropic）: 83.8%<br>
• GPT-5.6 Sol（OpenAI）: 83.6%</p>
</div>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">三个数字在统计上几乎没有差异。也就是说，在"自主找漏洞"这条最关键的攻击能力维度上，<b>前沿模型的差距已经被抹平，而其中跑分最高的那个，是开源的</b>。</p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">更值得注意的是 Z.ai 怎么做到的：他们建了一堆模拟开发者工作站的沙箱，让 GLM-5.3 在里面完成复杂的编码任务——有些练习<b>要连续跑好几天</b>。用这种"长周期训练"换来的，是模型对代码结构的理解深度：它不是靠模式匹配去碰低垂的 CVE，而是能在一个从未见过的代码库里，自主定位全新的漏洞模式。</p>
</div>

<div style="padding:28px;margin:28px 0;background:#fffbeb;border-radius:14px;border:1px solid #fcd34d;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#b45309;margin:0 0 20px;padding-left:16px;border-left:5px solid #f59e0b;">反常的选择：最强的模型，先不发布</div>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">Z.ai 接下来的决定，才是这件事真正值得写的地方。<b>它宣布暂缓开放 GLM-5.3 的模型权重，先进行约两周的安全评估和加固。</b></p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">对开源社区来说，这是一个"反常"动作。开源模型的惯例是发布即下载——权重放上网，任何人都能拿走去微调、去系统提示、绕过一切护栏。一家实验室主动扣住自己最强模型的权重，等于是自己承认：<b>这东西放出去，我控制不了它被拿去做什么。</b></p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">但两周后呢？两周不是永远。一旦权重公开，<b>实验室在发布前做的所有安全审查，在下载完成的那一刻全部失效</b>。你没法给一个 7000 亿参数的模型装上"出厂锁"——硬件认证、模型水印、能力分级沙箱，这些在今天都还是研究课题，不是部署好的基础设施。</p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">所以 Z.ai 的"暂扣"买来的是时间，不是答案。真正的难题在它身后：<b>当一个能自主扫出上千个高危漏洞的模型成为公开下载物，安全界要面对的不再是"模型会不会失控"，而是"任何一个人，都能让它精准出击"。</b></p>
</div>

<div style="padding:28px;margin:28px 0;background:#eff6ff;border-radius:14px;border:1px solid #bfdbfe;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#1d4ed8;margin:0 0 20px;padding-left:16px;border-left:5px solid #2563eb;">防守方的同一把枪</div>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">这件事不全是坏消息。能找漏洞的模型，同样能扫自己的系统。一个安全团队今天就能用这类能力，在攻击者之前把自己代码库里同样的漏洞类别清一遍。<b>攻击方只需要找到一个你漏掉的口子，防守方却要把所有的口子都堵上——不对称，但模型让防守方第一次有了"全量扫描"的可能。</b></p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">问题在于，这把枪在谁手里。Infosecurity Magazine 采访的安全专家们对此态度分裂：有人欢迎前沿实验室主动放慢脚步，也有人指出——<b>市场上早就有一堆"去审查"（abliterated）的开源模型，恶意行为者已经在用这些能力了</b>。自管是好事，但"只对守规矩的客户限制访问"，并不会让整个安全环境变好。</p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">Black Hills Information Security 的负责人说得更直接：别指望前沿公司自律。他说，一年前正是这些公司提醒所有人需要护栏，而他们自己当时并没有做。所以真正缺的，是"有意义的监督和问责"——<b>不是靠公司自觉，而是靠机制兜底。</b></p>
</div>

<div style="padding:28px;margin:28px 0;background:#fef2f2;border-radius:14px;border:1px solid #fecaca;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#b91c1c;margin:0 0 20px;padding-left:16px;border-left:5px solid #dc2626;">这条线的下一个拐点</div>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">OpenAI 按下暂停一周后，GLM-5.3 给出了一半答案——<b>刹车本身无法改变能力的扩散。</b>能力不在 OpenAI 的服务器里，它已经在开源权重里复制、在基准分数里公开、在每一个能下载模型的人手里。</p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">接下来的两周是真正的观察窗口：Z.ai 的权重会不会按期放出？OpenAI 的监控系统能不能在 Astra 复产前接住新的能力尖峰？如果开源权重如期上线，安全社区将第一次面对"前沿攻击能力人人可得"的现实——那时候，监管讨论的焦点会从"要不要管"，直接变成"管什么、怎么管才来得及"。</p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">一个 40 年前的漏洞被今天的模型翻出来，这个细节本身就是隐喻：<b>代码会老，漏洞不会。而找出它们的速度，第一次超过了修补它们的速度。</b></p>
</div>

<div style="padding:28px;margin:28px 0;background:#f8fafc;border-radius:14px;border:1px solid #e2e8f0;word-wrap:break-word;">
<div style="font-weight:700;color:#0f172a;font-size:22px;margin-bottom:16px;">写在最后</div>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">当一家头部实验室在犹豫要不要慢下来的时候，世界上的其他地方没有在等。<b>能力的扩散不因一家公司的暂停而暂停——它只是换了一条路，继续往前走。</b></p>

<p style="font-size:17px;line-height:2;color:#1f2937;margin:14px 0;text-indent:0;">Z.ai 选择先扣住权重，是这轮扩散里少见的克制。但两周后，克制到期。到时候我们会知道，<b>这份能力到底是进了安全工程师的工具箱，还是进了攻击者的弹药库——或者，两者同时。</b></p>
</div>

<div style="padding:20px;margin:28px 0;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;word-wrap:break-word;">
<div style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 12px;">事实来源（均为 2026-08 公开报道，可查证）</div>
<p style="font-size:14px;color:#334155;line-height:1.9;margin:8px 0;">• SiliconANGLE，2026-08-14，《Z.ai debuts GLM-5.3 with long-horizon coding, cybersecurity upgrades》（GLM-5.3 发布、2400+ 漏洞/269 项目、约半数中高危、40 年前代码、两周后开放权重、沙箱长周期训练）<br>
• Decrypt，2026-08-14，《China's Z.AI Ships GLM-5.3, Calling It the Top Open-Weight Coding Model》<br>
• Marc Pope，2026-08-20，《When the Safety Framework Actually Fires》（CyberGym 分数 84.5/83.8/83.6、OpenAI 8/7 暂停 Astra、20% 监控算力开销、暂扣权重两周）<br>
• Infosecurity Magazine，2026-08-11，《OpenAI Pauses Some Development of Astra Model on Security Concerns》（Preparedness Framework 关键级网络安全门槛定义、专家观点）</p>
</div>

</section>'''

os.makedirs("output", exist_ok=True)
out = f"output/sample_glm53_{today}.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("预览已生成:", out)
print("标题: 它找到了2436个漏洞，然后决定先不发")
print("字数(约):", len(html)//2)
