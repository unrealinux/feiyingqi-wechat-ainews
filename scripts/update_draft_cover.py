#!/usr/bin/env python3
r"""换掉草稿箱里某篇草稿的封面（标题、正文不动）。

用途：封面配错了图（例如主题选成工业机械臂）要重配。只能在**草稿**上改：
已经群发/发布出去的文章，封面由平台定死，API 改不了。

用法：
    python scripts/update_draft_cover.py output/xxx.jpg            # 改最新一篇
    python scripts/update_draft_cover.py output/xxx.jpg --index 1  # 改列表里第 2 篇
    python scripts/update_draft_cover.py --list                    # 只看不改

两个只能用血换来的微信坑（2026-10 实测）：
  1. **请求必须发原始 UTF-8**：用 requests 的 `json=` 会把非 ASCII 转成 \uXXXX，
     draft/update 把这些转义序列当普通字符存了 —— 标题/正文/作者全变乱码，
     且中文 author 会报 45110 author size out of limit。
     照 src/publisher.create_draft 的做法：json.dumps(ensure_ascii=False) + data=。
  2. **响应要自己按 UTF-8 解**：返回 Content-Type: text/plain（无 charset），
     requests 按 ISO-8859-1 解，中文全变乱码。
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests  # noqa: E402

from src.publisher import WeChatPublisher  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BATCHGET = "https://api.weixin.qq.com/cgi-bin/draft/batchget"
UPDATE = "https://api.weixin.qq.com/cgi-bin/draft/update"


def _plain(html):
    """标题/正文比对用：只留文字，忽略样式与重签过的图片 URL。"""
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html or ""))


def _post_json(url, token, payload, timeout=20):
    """发原始 UTF-8 的 JSON（不能用 requests 的 json=，见文件头坑 1），
    并自己按 UTF-8 解响应（坑 2）。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(
        url,
        params={"access_token": token},
        data=body,
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    return json.loads(resp.content.decode("utf-8"))


def _drafts(token):
    resp = _post_json(BATCHGET, token, {"offset": 0, "count": 20, "no_content": 0})
    if resp.get("errcode"):
        raise RuntimeError(f"读取草稿失败: {resp}")
    return resp.get("item", [])


def main():
    parser = argparse.ArgumentParser(description="替换草稿封面")
    parser.add_argument("image", nargs="?", help="新封面图片路径（1440x810）")
    parser.add_argument("--index", type=int, default=0, help="改第几篇（默认最新一篇）")
    parser.add_argument(
        "--author", default=None, help="默认沿用原署名；显式传空串则清空"
    )
    parser.add_argument("--list", action="store_true", help="只列出草稿，不改")
    args = parser.parse_args()

    publisher = WeChatPublisher()
    token = publisher.get_access_token()
    drafts = _drafts(token)
    if not drafts:
        print("草稿箱是空的")
        return 1

    print(f"草稿箱共 {len(drafts)} 篇：")
    for i, d in enumerate(drafts):
        a = d["content"]["news_item"][0]
        print(f"  [{i}] {a['title'][:40]}  (封面 {a.get('thumb_media_id', '')[:12]}…)")

    if args.list or not args.image:
        return 0

    if not Path(args.image).exists():
        print(f"找不到图片: {args.image}")
        return 1

    draft = drafts[args.index]
    item = draft["content"]["news_item"][0]
    old_thumb = item.get("thumb_media_id", "")
    new_thumb = publisher._upload_media(args.image, "image")
    if not new_thumb:
        print("封面素材上传失败，未做任何修改")
        return 1
    print(f"新封面已上传: {new_thumb[:12]}…（旧 {old_thumb[:12]}…）")

    articles = {
        "title": item["title"],
        "author": item.get("author", "") if args.author is None else args.author,
        "digest": item.get("digest", ""),
        "content": item["content"],
        "content_source_url": item.get("content_source_url", ""),
        "thumb_media_id": new_thumb,
        "need_open_comment": item.get("need_open_comment", 0),
        "only_fans_can_comment": item.get("only_fans_can_comment", 0),
    }
    resp = _post_json(
        UPDATE,
        token,
        {"media_id": draft["media_id"], "index": 0, "articles": articles},
    )
    if resp.get("errmsg") != "ok":
        print(f"更新失败: {resp}")
        return 1

    after = _drafts(token)[args.index]["content"]["news_item"][0]
    # 只比文字：微信每次保存都会重签正文里的图片 URL，比原始 HTML 会假告警
    same_text = _plain(after["content"]) == _plain(item["content"])
    print(f"标题        : {after['title']}")
    print(f"封面已更新  : {(after.get('thumb_media_id') or '')[:16]}…")
    print(f"标题/署名   : {after['title']} / {after.get('author')}")
    print(f"正文是否变动: {'否' if same_text else '是（注意核对）'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
