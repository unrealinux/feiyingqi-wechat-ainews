import sys; sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import requests
from publisher import WeChatPublisher

p = WeChatPublisher()
t = p.get_access_token()
r = requests.post('https://api.weixin.qq.com/cgi-bin/draft/batchget',
    params={'access_token': t}, json={'offset': 0, 'count': 20},
    timeout=30, proxies=p.proxies if p.use_proxy else {})
d = r.json()
print(f"剩余草稿: {d.get('total_count', 0)} 篇")
items = d.get("item", [])
for item in items[:5]:
    content = item.get("content", {})
    news = content.get("news_item", [{}])[0] if content.get("news_item") else {}
    print(f"  - {news.get('title', '无标题')}")
