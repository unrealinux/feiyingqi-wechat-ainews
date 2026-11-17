"""出口 IP 相关的探测：家用宽带换 IP 时，微信会直接拒掉 access_token。

微信报错长这样：
    获取 access_token 失败: invalid ip 183.202.137.105 ipv6 ::ffff:183.202.137.105,
    not in whitelist rid: 6af653ac

那个 IP 只出现在错误消息里，不测一次就不知道现在漂到哪了。这里把探测和
IP 提取放在一处，供出稿前的预检和告警统计共用。
"""

import re
from typing import Optional, Tuple

import requests

from src.config import get_wechat_config, load_config

_IP_RE = re.compile(r"invalid ip\s+([0-9a-fA-F\.:]+)")


def extract_ip(text: str) -> str:
    """从微信错误消息里取出口 IP；取不到返回空串。"""
    m = _IP_RE.search(str(text or ""))
    return m.group(1) if m else ""


def probe_token() -> Tuple[Optional[str], str]:
    """直接探一次 token（不走缓存）。返回 (token, errmsg)，成功时 errmsg 为空。

    失败时 errmsg 就是微信的原始文案，里面带当前出口 IP，直接进告警底账，
    事后统计能看出 IP 漂移频率。
    """
    config = load_config()
    wechat = get_wechat_config(config)
    try:
        resp = requests.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": wechat.get("app_id", ""),
                "secret": wechat.get("app_secret", ""),
            },
            timeout=10,
        )
        data = resp.json()
    except Exception as e:  # 网络层失败也算一次探测失败
        return None, f"token 探测异常: {e}"
    if data.get("access_token"):
        return data["access_token"], ""
    return None, str(data.get("errmsg") or data)
