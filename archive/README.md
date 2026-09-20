# archive/ — 一次性发布脚本归档

按 `AGENTS.md` 第 4 节"脚本管理"要求归档：一篇文章一个有语义命名脚本，发布后归档，不堆积在根目录。

## 运行方式

这些脚本使用相对路径（`src/`、`output/`），**仍需在仓库根目录运行**：

```powershell
python archive\create_glm53_draft.py
python archive\gen_sample_waic.py
```

## 分组

- `create_gpt6_astra_draft.py` — 第九篇《OpenAI 秀出来的 99.9%，和它藏起来的 41.4%》（GPT-6 Astra 深读，2026-09-10 已建草稿；支持 `--preview` 仅本地出封面）
- `create_*_draft.py` — 各篇原创文的草稿创建脚本（封面绘制 + `create_draft`）
- `gen_sample_*.py` — 各篇 HTML 预览生成脚本（本地确认用）
- `check_draft.py` / `check_drafts.py` / `list_drafts.py` / `_draftcheck.py` — 草稿箱检查
- `update_rogue_agent_draft.py` / `add_text.py` / `make_covers.py` — 草稿/封面微调
- `draft_check.txt` / `emoji_result.txt` / `emoji_test.txt` — 当时的测试输出
- `batch_generate.py` — ⚠️ 批量发布脚本，**已停用**（违反 AGENTS.md 第 1 条"禁止批量发布"红线，切勿再运行；确认无用后可直接删除）

## 注意

- 运行前确认 `.env` 密钥已配置（微信 AppID/Secret、LLM key 等均已外置到 `.env`）。
- 这些脚本只创建草稿（`create_draft`），不群发；群发需按 AGENTS.md 逐次授权。
