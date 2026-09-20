"""检查微信草稿箱实际内容（输出到UTF-8文件）"""
import sys
sys.path.insert(0, 'src')

from publisher import WeChatPublisher
import requests
import json

pub = WeChatPublisher()
token = pub.get_access_token()

# 获取草稿列表
url = 'https://api.weixin.qq.com/cgi-bin/draft/batchget'
params = {'access_token': token}
data = {'offset': 0, 'count': 3}

resp = requests.post(url, params=params, json=data, timeout=30)
result = resp.json()

# 保存到文件（UTF-8）
with open('draft_check.txt', 'w', encoding='utf-8') as f:
    f.write(f"获取草稿列表: errcode={result.get('errcode')}, total={result.get('total_count', 0)}\n\n")
    
    if 'item' in result:
        for i, item in enumerate(result['item'][:3], 1):
            content = item.get('content', {})
            title = content.get('title', '')
            digest = content.get('digest', '')
            
            f.write(f"草稿{i}:\n")
            f.write(f"  标题: {title}\n")
            f.write(f"  摘要: {digest[:50] if digest else '空'}\n")
            
            # 检查是否包含中文字符
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in title)
            f.write(f"  包含中文: {has_chinese}\n")
            
            if has_chinese:
                f.write(f"  ✅ 标题正常（UTF-8）\n")
            else:
                f.write(f"  ❌ 标题可能乱码\n")
            f.write("\n")

print("结果已保存到 draft_check.txt（UTF-8编码）")
print("请用记事本或VS Code打开查看实际内容")
