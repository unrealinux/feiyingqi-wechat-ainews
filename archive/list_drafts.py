"""查看草稿箱所有文章标题"""
import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import requests
from publisher import WeChatPublisher

publisher = WeChatPublisher()
token = publisher.get_access_token()
if not token:
    print("获取token失败")
    sys.exit(1)

all_drafts = []
offset = 0
count = 20
while True:
    url = "https://api.weixin.qq.com/cgi-bin/draft/batchget"
    params = {"access_token": token}
    data = {"offset": offset, "count": count, "no_content": 1}
    resp = requests.post(url, params=params, json=data, timeout=15)
    result = resp.json()
    items = result.get("item", [])
    total = result.get("total_count", 0)
    if not items:
        break
    all_drafts.extend(items)
    offset += count
    if offset >= total:
        break

print(f"草稿箱共 {total} 篇文章\n")
for i, draft in enumerate(all_drafts, 1):
    articles = draft.get("content", {}).get("news_item", [])
    title = articles[0].get("title", "无标题") if articles else "无标题"
    print(f"{i:2d}. {title}")
