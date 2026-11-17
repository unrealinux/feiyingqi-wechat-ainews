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
        {
            "name": "示例",
            "candidates": [str(tmp_path)],
            "source_label": "《示例》",
            "site": "",
        },
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
        md = [p for p in d.glob("*.md") if p.name.upper() != "INDEX.MD"]
        assert md, f"{key} 解析到 {d}，但里面没有章节"


def test_chapter_path_tolerates_layout_change(tmp_path, monkeypatch):
    """上游去掉 chapters/ 这层后，旧 rel 路径仍要能读到（2026-11-17 事故）。"""
    key = _register(tmp_path, monkeypatch)          # 目录里直接是 a.md / b.md
    path = m.chapter_path(key, "chapters/a.md")
    assert path.exists() and path.name == "a.md"


def test_references_dir_searches_candidates(tmp_path, monkeypatch):
    """候选表按顺序找到第一个真有章节的目录，别写死单个路径。"""
    import pathlib

    empty = tmp_path / "empty"
    empty.mkdir()
    good = tmp_path / "good"
    good.mkdir()
    (good / "part1-01.md").write_text("# 章节\n正文", encoding="utf-8")
    monkeypatch.setitem(
        m.MATERIALS,
        "demo2",
        {
            "name": "示例",
            "candidates": [str(empty), str(good)],
            "source_label": "《示例》",
            "site": "",
        },
    )
    monkeypatch.setattr(m, "_HOME", tmp_path)
    assert m.references_dir("demo2") == good


def test_real_repos_resolve_to_a_dir_with_chapters():
    """两个素材源在当前机器上都要解析到真有章节的目录。"""
    for key in ("workbuddy", "doubaowork"):
        d = m.references_dir(key)
        if not d.exists():
            continue
        md = [p for p in d.glob("*.md") if p.name.upper() != "INDEX.MD"]
        assert md, f"{key} 解析到 {d}，但里面没有章节"
