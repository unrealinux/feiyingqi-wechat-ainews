"""第二步示范：原创评论文（仅生成本地预览，不建线上草稿）
主题：WAIC 2026 真实事件的原创评论
所有数据来自 2026-07 公开报道（Reuters / TechTimes / 上海发布 / 环球时报），文末标注来源。
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os, datetime

title = "WAIC 2026 落幕：当世界开始有两套 AI 规则"
today = datetime.date.today().strftime("%Y-%m-%d")

html = f'''<section>

<p style="font-size:15px;color:#888;margin:0 0 18px;">原创评论 · 不追热点、不堆数据、不说"替代"套话</p>

<h2 style="font-size:24px;font-weight:700;margin:24px 0 12px;">一场会，照出了 AI 世界的"裂痕"</h2>

<p style="font-size:17px;line-height:2;margin:14px 0;">2026 年 7 月 17 日到 20 日，世界人工智能大会（WAIC）在上海举行。这是它办到第九届，也是中国最高领导人<b>第一次</b>出席并致辞（据路透社 7 月 17 日报道）。</p>

<p style="font-size:17px;line-height:2;margin:14px 0;">真正值得注意的，不是又发布了多少新产品，而是会上出现了一个此前没有的东西：<b>两套并行的全球 AI 治理框架</b>。</p>

<p style="font-size:17px;line-height:2;margin:14px 0;">会前一天（7 月 16 日），由中国倡议、总部设在上海的"世界人工智能合作组织"（WAICO）由 29 个国家签署成立（TechTimes、新华社报道）。而华盛顿此前已拉起 35 国参与的"AI 机会声明"。两套规则，两种叙事，几乎没有国家同时加入两边。</p>

<blockquote style="border-left:4px solid #2563eb;background:#f0f4ff;padding:14px 18px;margin:20px 0;font-size:17px;line-height:2;color:#1e3a8a;">过去我们谈 AI，默认是一场比赛：谁模型更强、谁算力更猛。WAIC 2026 提醒我们，比赛的下半场，比的是<b>谁制定规则、谁供应底座、谁成为更多国家的技术伙伴</b>。</blockquote>

<h2 style="font-size:24px;font-weight:700;margin:24px 0 12px;">开源，成了新的"地缘筹码"</h2>

<p style="font-size:17px;line-height:2;margin:14px 0;">这次会上，中国把"开源开放"摆到了前所未有的高度。会议期间，Moonshot AI 发布开源大模型 Kimi K3，参数规模达到 2.8 万亿（MoE 架构），据多家媒体称为当时最大的开放权重模型之一；华为展示了 Atlas 950 超节点，强调"不依赖美国-origin 部件"也能训练、部署大模型。</p>

<p style="font-size:17px;line-height:2;margin:14px 0;">这两件事放在一起看很有意思：在被限制获取先进芯片的背景下，中国把"开源 + 自主底座"打包，作为给发展中国家的一种选项。路透社的报道点得很直白——这被定位为对抗美国"Pax Silica"倡议的替代方案。</p>

<p style="font-size:17px;line-height:2;margin:14px 0;">无论你认同哪一方，一个事实正在发生：<b>全球南方国家第一次有了"不选边也能用上先进 AI"的可能</b>。WAICO 成员里大量是"一带一路"和金砖国家，它们要的从来不是站队，而是入场券。</p>

<h2 style="font-size:24px;font-weight:700;margin:24px 0 12px;">但热闹之下，有几个冷问题</h2>

<p style="font-size:17px;line-height:2;margin:14px 0;"><b>第一，治理机构一旦成立，就会长期存在。</b> 今天签的是一纸章程，十年后影响的是几十个国家的 AI 监管形态。规则的分叉，比模型的分叉更难回头。</p>

<p style="font-size:17px;line-height:2;margin:14px 0;"><b>第二，"开源"不等于"中立"。</b> 开源降低了使用门槛，但模型的价值观、安全边界、训练语料，仍然由发布方决定。用谁的模型，某种程度上就是在接受谁的世界观。</p>

<p style="font-size:17px;line-height:2;margin:14px 0;"><b>第三，普通人的体感还很远。</b> 会上说中国 AI 产业规模 2025 年已超 1 万亿元（国家发改委数据），但"产业规模"和"我生活变好"之间，还隔着无数落地环节。别被宏大叙事带跑，真正要问的是：它帮你省了哪一段路、解决了哪个具体麻烦？</p>

<h2 style="font-size:24px;font-weight:700;margin:24px 0 12px;">写在最后</h2>

<p style="font-size:17px;line-height:2;margin:14px 0;">WAIC 2026 最值得记住的，不是哪款机器人又翻了个跟头，而是：<b>AI 的边界，正在从"技术竞赛"走向"秩序竞赛"</b>。</p>

<p style="font-size:17px;line-height:2;margin:14px 0;">对从业者，这是窗口期；对普通人，这是该认真理解"规则由谁定"的时刻。因为我们终将活在某一套规则之下——而那套规则，此刻正在上海和华盛顿同时被写下。</p>

<hr style="border:none;border-top:1px solid #eee;margin:28px 0;">

<p style="font-size:14px;color:#888;line-height:1.9;margin:10px 0;">数据来源（均为 2026-07 公开报道，可查证）：<br>
· 路透社 Reuters，2026-07-17，《Xi pitches China as leader of new global AI order》<br>
· TechTimes，2026-07-17，《China Launches Rival AI Governance Bloc as WAIC 2026 Opens》<br>
· 上海市政府发布，2026-07-10，《WAIC 2026 takes AI beyond conference halls》<br>
· 环球时报，2026-07-07，《2026 WAIC set for July 17 with over 300 global product debuts》<br>
· 国家发改委（NDRC）于 WAIC 2026 公布产业数据</p>

<p style="font-size:13px;color:#aaa;margin:16px 0 0;">（本文为示范稿，未发布、未建草稿。是否发布请由号主确认。）</p>

</section>'''

os.makedirs("output", exist_ok=True)
out = f"output/sample_waic2026_{today}.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("本地预览已生成:", out)
print("字数(约):", len(html)//2)
print("标题:", title)
