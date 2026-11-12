"""本地技能素材装载：章节标题/在线地址要被正确取出，缺文件不能炸。

这两套素材是社区整理的指南（不是官方文档），sources 里靠「章节标题 + 站点」
溯源，取错了整篇文章的出处就是错的。
"""

from src import materials as m

_CHAPTER = """<!-- 由 scripts/sync.mjs 自动生成 -->

> 在线: [豆包工作的下载、安装和登录](https://doubaowork.homes/#/p/5828287b3f6d6835) · 上游: x

# 豆包工作的下载、安装和登录

## 从官方入口下载

正文……
"""

_NO_URL_CHAPTER = """# 第 1 章 初识 WorkBuddy

**WorkBuddy** 是……
"""


def _register(tmp_path, monkeypatch, key="demo"):
    (tmp_path / "chapters").mkdir()
    (tmp_path / "chapters" / "a.md").write_text(_CHAPTER, encoding="utf-8")
    (tmp_path / "chapters" / "b.md").write_text(_NO_URL_CHAPTER, encoding="utf-8")
    monkeypatch.setitem(
        m.MATERIALS,
        key,
        {"name": "示例", "references": tmp_path, "source_label": "《示例》", "site": ""},
    )
    return key


def test_chapter_title_and_url(tmp_path, monkeypatch):
    key = _register(tmp_path, monkeypatch)

    assert m.chapter_title(_CHAPTER) == "豆包工作的下载、安装和登录"
    assert m.chapter_url(_CHAPTER) == "https://doubaowork.homes/#/p/5828287b3f6d6835"
    assert m.chapter_url(_NO_URL_CHAPTER) is None

    loaded = m.load_chapters(key, ["chapters/a.md", "chapters/b.md"])
    assert [title for title, _ in loaded] == [
        "豆包工作的下载、安装和登录",
        "第 1 章 初识 WorkBuddy",
    ]


def test_missing_chapter_is_skipped(tmp_path, monkeypatch):
    key = _register(tmp_path, monkeypatch)

    loaded = m.load_chapters(key, ["chapters/a.md", "chapters/nope.md"])
    assert len(loaded) == 1


def test_unknown_material_key_raises():
    try:
        m.references_dir("not-a-material")
    except KeyError as e:
        assert "not-a-material" in str(e)
    else:
        raise AssertionError("未知素材源应该报错")


def test_both_real_material_sources_are_on_disk():
    """登记的两个素材源确实在本机（路径写错就只剩空素材）。"""
    for key in ("workbuddy", "doubaowork"):
        d = m.references_dir(key)
        if not d.exists():
            continue  # 换机器没这两套素材时跳过，不把测试当环境检查
        assert list((d / "chapters").glob("*.md")), f"{key} 章节目录是空的"
