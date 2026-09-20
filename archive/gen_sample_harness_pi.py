"""第五篇低频原创：DeepSeek Harness vs Pi —— 两个都喊 Model+Harness=Agent，路线却完全相反
基于 DeepSeek 官方（deepseek.com/harness）、Pi 官方文档、Composio 实测、Harrison Kinsley 复测、36Kr、BestHub 等
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, datetime

today = datetime.date.today().strftime("%Y-%m-%d")

html = f'''<section>

<div style="padding:30px;margin:20px 0;background:linear-gradient(135deg,#0f172a,#164e63);border-radius:16px;color:#f1f5f9;font-size:18px;line-height:2.2;word-wrap:break-word;">
<div style="font-size:15px;color:#22d3ee;margin-bottom:12px;text-transform:uppercase;letter-spacing:2px;">深度原创 · 技术评测向</div>
<div style="font-size:27px;font-weight:700;margin-bottom:16px;color:#f8fafc;line-height:1.4;">DeepSeek Harness vs Pi：同一个公式，两条相反的路线</div>
<div style="font-size:17px;color:#a5f3fc;">一个刚发布、要"装下全世界"；一个老练、只留 200 个 token。谁更接近"Agent = Model + Harness"的真相？</div>
</div>

<div style="padding:28px;margin:28px 0;background:#f0f9ff;border-radius:14px;border:1px solid #bae6fd;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#0c4a6e;margin:0 0 20px;padding-left:16px;border-left:5px solid #0ea5e9;">先说结论</div>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;">过去一周，AI 编程工具圈发生了一件值得记住的事：<b>DeepSeek 官方 Harness 于 8 月 14 日放出开发者预览</b>（开源，MIT 协议，代码在 GitHub），而几乎同时，一堆第三方实测数据指向一个相反的名字——<b>Pi</b>（pi-mono）。</p>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;">两边的官方说法都用同一个公式：<b>Agent = Model + Harness</b>。但 DeepSeek 选择"把所有能力都做成插件"，Pi 选择"把系统提示词砍到 200 个 token、只剩四个核心工具"。<b>同一个信念，两种截然相反的工程实现。</b></p>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;">有意思的是：在近期的公开实测里，赢的往往是那个"更小"的。</p>
</div>

<div style="padding:28px;margin:28px 0;background:#f8fafc;border-radius:14px;border:1px solid #e2e8f0;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#1e293b;margin:0 0 20px;padding-left:16px;border-left:5px solid #2563eb;">一分钟认识两位主角</div>

<div style="padding:18px;margin:16px 0;background:#eef2ff;border-radius:10px;border:1px solid #c7d2fe;">
<p style="font-size:17px;font-weight:700;color:#3730a3;margin:0 0 8px;">DeepSeek Harness（官方 · 刚出生）</p>
<p style="font-size:16px;line-height:2;color:#334155;margin:8px 0;text-indent:0;">DeepSeek 围绕自家模型的官方 Agent 框架，核心公式"Model + Harness = Agent"。2026 年 5 月组建 Harness 团队，7 月 31 日首次在 changelog 中出现，8 月 14 日开发者预览上线。<b>最大卖点：一切皆插件（Everything is a plugin）</b>——模型、工具、技能、会话、沙箱、存储、循环、调度、UI，全部可插拔可替换，基于 Cordis 插件系统。</p>
</div>

<div style="padding:18px;margin:16px 0;background:#f0fdfa;border-radius:10px;border:1px solid #99f6e4;">
<p style="font-size:17px;font-weight:700;color:#134e4a;margin:0 0 8px;">Pi（pi-mono · 社区老炮）</p>
<p style="font-size:16px;line-height:2;color:#334155;margin:8px 0;text-indent:0;">极简、可扩展的终端编程 harness，TypeScript 编写。<b>只有四个核心工具：read、write、edit、bash</b>，没有引导向导、没有登录墙。系统提示词只有几百个 token，其他全留给 TypeScript 扩展、技能、提示词模板。支持 15+ 模型提供商，会话用"树"组织，可以随时分支回到错误前的节点。</p>
</div>

<p style="font-size:16px;line-height:2;color:#64748b;margin:14px 0;text-indent:0;">补充说明：社区里还有一个 Oh My Pi（OMP），是开发者 Can Boluk 在 Pi 基础上加料的分支，下面的实测数据会同时出现两者，读者需区分。</p>
</div>

<div style="padding:28px;margin:28px 0;background:#fff;border-radius:14px;border:1px solid #e2e8f0;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#1e293b;margin:0 0 16px;padding-left:16px;border-left:5px solid #7c3aed;">核心差异对照表</div>

<table style="width:100%;border-collapse:collapse;font-size:15px;line-height:1.8;">
<thead>
<tr style="background:#f1f5f9;">
<th style="padding:10px;border:1px solid #e2e8f0;color:#334155;font-weight:700;width:18%;">维度</th>
<th style="padding:10px;border:1px solid #e2e8f0;color:#3730a3;font-weight:700;width:41%;">DeepSeek Harness</th>
<th style="padding:10px;border:1px solid #e2e8f0;color:#134e4a;font-weight:700;width:41%;">Pi (pi-mono)</th>
</tr>
</thead>
<tbody>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">出身</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">DeepSeek 官方，模型+harness 协同设计</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">社区开源，与模型厂商无关</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">成熟度</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">8/14 开发者预览，作者自认"还有不少坑"</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">长期迭代，已被多轮第三方实测验证</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">设计哲学</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">一切皆插件，全量可组合（Full-featured）</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">极简，系统提示词仅几百 token，默认出厂</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">界面</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">Web UI + 桌面 Agent（Tauri），跨平台</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">纯终端（CLI）</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">运行模式</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">Standard / Code / Minimal / Creator 四模式</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">单一模式，四个核心工具 + 扩展</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">可追溯性</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">Trajectory 全量会话日志（追加式），可回放/分叉/搜索</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">会话树，可分支回到错误前节点</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">思维链</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">配套模型提供 CoT 轨迹（DeepSeek 是少数不隐藏思考过程的厂商）</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">只能记录模型暴露出来的内容</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">成本优化</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">官方原生，与训练团队协同，可复用非公开信息</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">靠生态（DeepPi、pi-deepseek-cache 等）实现对 DeepSeek 前缀缓存的极致利用</td></tr>
<tr><td style="padding:10px;border:1px solid #e2e8f0;color:#475569;font-weight:700;">安装</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;"><code style="font-size:13px;color:#0c4a6e;">npx @deepseek-ai/dsh web</code> 或 clone GitHub</td><td style="padding:10px;border:1px solid #e2e8f0;color:#334155;">npm 安装，TypeScript 扩展即插即用</td></tr>
</tbody>
</table>
</div>

<div style="padding:28px;margin:28px 0;background:#eff6ff;border-radius:14px;border:1px solid #bfdbfe;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#1e293b;margin:0 0 20px;padding-left:16px;border-left:5px solid #2563eb;">实测数据：为什么"小"反而赢</div>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;"><b>第一组：Composio 的 8 harness 横向测试</b>（2026-08 发布）。同一个模型 DeepSeek V4 Flash，跑同一个 30 个任务集合，只换 harness：</p>

<table style="width:100%;border-collapse:collapse;font-size:14px;line-height:1.7;margin:14px 0;">
<thead>
<tr style="background:#f1f5f9;">
<th style="padding:8px;border:1px solid #e2e8f0;color:#334155;">Harness</th>
<th style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">通过率</th>
<th style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">中位耗时</th>
<th style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">每成功成本</th>
</tr>
</thead>
<tbody>
<tr><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;font-weight:700;">Pi Agent</td><td style="padding:8px;border:1px solid #e2e8f0;color:#dc2626;text-align:center;font-weight:700;">66.7%</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">132.2s</td><td style="padding:8px;border:1px solid #e2e8f0;color:#dc2626;text-align:center;font-weight:700;">$0.028</td></tr>
<tr><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;">Prime Agent</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">62.5%</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">242.1s</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">$0.131</td></tr>
<tr><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;">Oh My Pi</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">56.7%</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">272.4s</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">$0.103</td></tr>
<tr><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;">Claude Code</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">53.3%</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">122.7s</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">$0.195</td></tr>
<tr><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;">OpenCode</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">46.7%</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">129.7s</td><td style="padding:8px;border:1px solid #e2e8f0;color:#334155;text-align:center;">$0.073</td></tr>
</tbody>
</table>

<p style="font-size:16px;line-height:2;color:#475569;margin:14px 0;text-indent:0;">Pi 是全场唯一一个"默认出厂、零额外配置"的 harness——只加载测试必需的 MCP 插件，没有任何微调，却通过了最多任务。它的单任务成功成本约 $0.028，是 Claude Code（$0.195）的 <b>1/7</b>。测试方也坦诚：Pi 用的是不同的推理设置和两家模型供应商，直接对比要打折。</p>

<p style="font-size:17px;line-height:2;color:#334155;margin:14px 0;text-indent:0;"><b>第二组：独立开发者 Harrison Kinsley（sentdex）的复测</b>（2026-08-10）。他自己写了个极简 harness（minion）跑 DeepSeek V4 Flash 0731，得分 44/89；换到 Oh My Pi，同一个模型、同一个 89 任务基准，得分变成 <b>64/89——整整 20 个任务的差距</b>，模型一个字都没改。他原话：</p>

<div style="padding:16px 20px;margin:16px 0;background:#eff6ff;border-radius:8px;border-left:4px solid #2563eb;">
<p style="font-size:16px;line-height:2;color:#1e3a8a;margin:0;font-style:italic;">"我本来以为 DeepSeek 在基准分数上很不诚实，直到我用 OMP 两边公平地跑了一遍，发现——嗯，它确实能一样好。""给好厨师一个单灶头加钝刀，端出来的菜反映的更多是厨房，而不是厨师。"</p>
</div>

<p style="font-size:16px;line-height:2;color:#475569;margin:14px 0;text-indent:0;">代价是 token：harness 把一个任务的成本从约 3 万 token 拉到约 15.4 万 token（约 5.3 倍）。<b>脚手架是在用钱和延迟换能力——但换算成"每成功任务成本"，Pi 依然是全场最低。</b></p>
</div>

<div style="padding:28px;margin:28px 0;background:#fef2f2;border-radius:14px;border:1px solid #fecaca;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#7f1d1d;margin:0 0 20px;padding-left:16px;border-left:5px solid #dc2626;">别忘了成本账：前缀缓存是隐藏赢家</div>

<p style="font-size:17px;line-height:2;color:#450a0a;margin:14px 0;text-indent:0;">Pi 赢的另一个维度是钱。DeepSeek 的 API 有<b>前缀缓存</b>机制：请求的开头 token 序列和上次一致，就直接从缓存读，价格低一个数量级（缓存命中约 $0.003/百万 token，未命中 $0.14/百万）。</p>

<p style="font-size:17px;line-height:2;color:#450a0a;margin:14px 0;text-indent:0;">开发者 0xEvan 用 Pi 调 DeepSeek V4 Flash，处理近 10 亿输入 token，<b>缓存命中率 99.93%，总共只花了 $2.65</b>。同样用量不命中缓存，官方估算是 $132——<b>差距约 50 倍</b>。另一位开发者 Shantanu Goel 的观察是：DeepSeek V4 Flash 在其他 harness 里命中率通常 94%~97%，在 Pi 里能稳定超过 99%。</p>

<p style="font-size:17px;line-height:2;color:#450a0a;margin:14px 0;text-indent:0;">这也是为什么 Pi 生态专门长出了一批为 DeepSeek 缓存优化的扩展：pi-deepseek-cache 冻结系统提示词里的日期/工作目录（消除动态内容导致的缓存失效）、对摘要做哈希缓存（保证字节级一致）。<b>这套玩法 DeepSeek Harness 官方也能做，而且理论上能做更深——因为模型和 harness 是同一个团队。</b></p>
</div>

<div style="padding:28px;margin:28px 0;background:#f0fdf4;border-radius:14px;border:1px solid #bbf7d0;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#166534;margin:0 0 20px;padding-left:16px;border-left:5px solid #22c55e;">DeepSeek Harness 的三个潜在杀手锏</div>

<p style="font-size:17px;line-height:2;color:#14532d;margin:14px 0;text-indent:0;"><b>1. 官方背书 + 协同设计。</b>第三方 harness 只能通过公开 API 逆向优化；官方团队可以和训练团队背靠背工作，让模型针对 harness 的调用方式做定向优化。这是任何社区项目都做不到的。</p>

<p style="font-size:17px;line-height:2;color:#14532d;margin:14px 0;text-indent:0;"><b>2. Trajectory 全量可追溯。</b>所有模型看到的东西（系统提示、推理、工具调用、子代理调度、每一次上下文注入）都记入追加式会话日志，可以按来源检查、回放、分叉、搜索。<b>配合 DeepSeek 不隐藏 CoT 思维链的模型，你几乎能看到 Agent 的完整脑内过程</b>——这在主流模型里越来越少见。</p>

<p style="font-size:17px;line-height:2;color:#14532d;margin:14px 0;text-indent:0;"><b>3. 它的 benchmark 一直用"Minimal mode"。</b>7 月 31 日发布的 V4-Flash-0731 官方智能体成绩（Terminal-Bench 2.1 82.7、DeepSWE 54.4 等），官方 changelog 明确说是用 Harness 的 <b>Minimal mode</b>（只有 shell + 文件编辑器）跑出来的——不是豪华全插件模式。这其实是一种克制的姿态：<b>官方先把"最小可用"做成基准，再往上堆插件。</b></p>
</div>

<div style="padding:28px;margin:28px 0;background:#1e293b;border-radius:14px;color:#f1f5f9;word-wrap:break-word;">
<div style="font-size:22px;font-weight:700;color:#f87171;margin:0 0 20px;padding-left:16px;border-left:5px solid #f87171;">怎么选：一张决策清单</div>

<div style="padding:14px;margin:14px 0;background:rgba(248,113,113,0.1);border-radius:8px;border-left:4px solid #f87171;">
<p style="font-size:16px;line-height:2;color:#fca5a5;margin:8px 0;text-indent:0;">• 想今天就能跑、要低成本、看重第三方实测数据 → <b>Pi</b>（或 Oh My Pi），接 DeepSeek V4 Flash</p>
<p style="font-size:16px;line-height:2;color:#fca5a5;margin:8px 0;text-indent:0;">• 想要桌面/Web 界面、全量可追溯日志、模型与 harness 深度协同 → <b>等 DeepSeek Harness</b>（先当小白鼠，作者明确说"会有很多坑"）</p>
<p style="font-size:16px;line-height:2;color:#fca5a5;margin:8px 0;text-indent:0;">• 重度依赖 DeepSeek 前缀缓存控成本 → Pi 生态（pi-deepseek-cache 等）今天就能做到 99%+ 命中；DeepSeek Harness 潜力更大但还没被实测</p>
<p style="font-size:16px;line-height:2;color:#fca5a5;margin:8px 0;text-indent:0;">• 想验证 DeepSeek 官方 benchmark 水分 → Harness 现在开源了，Minimal mode 已可跑，<b>终于可以用官方工具复现官方成绩</b></p>
</div>
</div>

<div style="padding:28px;margin:28px 0;background:#1e293b;border-radius:14px;color:#f1f5f9;word-wrap:break-word;">
<div style="font-weight:700;color:#f87171;font-size:22px;margin-bottom:16px;">写在最后</div>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">这一轮对比最有价值的启示，不是"谁赢了"，而是那句被反复验证的话：<b>harness 是模型的一部分，不是中立的管道。</b></p>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">同一个 DeepSeek V4 Flash，换个 harness，通过率能从 46.7% 变成 66.7%（Composio），能从 49.4% 变成 71.9%（Kinsley）。这个波动幅度，接近你花几个月、几百万美元等来的一次模型换代。</p>

<p style="font-size:17px;line-height:2;color:#cbd5e1;margin:14px 0;text-indent:0;">所以下一次看任何智能体排行榜，先问一句：<b>它的代码外面，到底包了什么？</b></p>
</div>

<div style="padding:20px;margin:28px 0;background:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;word-wrap:break-word;">
<div style="font-size:16px;font-weight:700;color:#1e293b;margin:0 0 12px;">事实来源（均可查证）</div>
<p style="font-size:14px;color:#64748b;line-height:1.9;margin:8px 0;">• DeepSeek Harness 开发者预览官方页：deepseek.com/harness（2026-08-14，MIT 开源，GitHub: deepseek-ai/deepseek-harness）<br>
• DeepSeek API 官方文档 · Pi 集成指南（pi-mono 配置示例）<br>
• DeepSeek V4-Flash-0731 官方 changelog（2026-07-31，标注 Harness minimal mode 跑分：Terminal-Bench 2.1 82.7、DeepSWE 54.4 等）<br>
• Composio 公开实测：《Finding the Best Harness for DeepSeek V4 Flash》（8 harness × 30 任务，2026-08）<br>
• Harrison Kinsley（sentdex）：《The Right Harness Is All You Need》，Terminal-Bench v2.1，89 任务（2026-08-10）<br>
• 36Kr / BestHub / OpenClawDatabase 相关报道（2026-08）；DeepSeek Harness 团队招聘信息（2026-05/06）</p>
</div>

</section>'''

os.makedirs("output", exist_ok=True)
out = f"output/sample_harness_vs_pi_{today}.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("预览已生成:", out)
print("标题: DeepSeek Harness vs Pi：同一个公式，两条相反的路线")
print("字数(约):", len(html)//2)
