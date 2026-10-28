"""封面被微信拒绝时的兜底：正文没问题，不能因为一张图当天就没稿。

2026-10-28 10:30 定时任务：draft/add 连续三次报“封面图片尺寸不合法 / 封面裁剪失败”，
1440×810 的原图换成 900×383 重编码版本就建成功了。
"""

from pathlib import Path

from PIL import Image

import src.publisher as publisher_module


def test_normalize_cover_resizes_to_wechat_size(tmp_path):
    src = tmp_path / "cover.jpg"
    Image.new("RGB", (1440, 810), (200, 220, 80)).save(src, "JPEG")

    out = publisher_module._normalize_cover_for_wechat(str(src))

    assert out, "能重编码就要返回新路径"
    with Image.open(out) as img:
        assert img.size == (900, 383)


def test_normalize_cover_returns_empty_on_bad_file(tmp_path):
    bad = tmp_path / "broken.jpg"
    bad.write_bytes(b"not an image")

    assert publisher_module._normalize_cover_for_wechat(str(bad)) == ""
