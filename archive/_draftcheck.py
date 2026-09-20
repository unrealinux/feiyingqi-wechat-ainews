import sys; sys.path.insert(0,'src'); sys.stdout.reconfigure(encoding='utf-8')
from publisher import WeChatPublisher
p=WeChatPublisher()
items=p.list_drafts(offset=0, count=20)
with open("output/_draftcount.txt","w",encoding="utf-8") as f:
    f.write("草稿箱当前篇数: %d\n" % len(items))
    for t,m in items:
        f.write(" - %s\n" % t)
