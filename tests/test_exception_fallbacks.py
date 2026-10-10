"""收窄裸 except 之后的兜底分支测试。

这 8 处裸 except 原本覆盖不到任何测试（`_parse_date`、`_load_font`、`_group_by_month`
在 tests/ 里引用数都是 0），而收窄异常类型最怕的就是「写窄了但真出错的场景没覆盖」：
把该兜底的异常漏在外面，线上就从「静默兜底」变成「直接崩」。

所以这里逐个构造**坏输入**，把兜底分支逼出来：
输入有多脏，兜底就得有多宽（这句决定了每个 except 里该列哪几种异常）。
"""

from __future__ import annotations

import datetime

import pytest

from src.analytics import Analytics
from src.fetcher import NewsFetcher, NewsItem


class TestAnalyticsFallbacks:
    """`_group_by_month`：解析不出月份就跳过，不该整批统计崩掉。"""

    def test_missing_date_is_skipped(self):
        by_month = Analytics()._group_by_month([{"title": "没有 date"}])
        assert by_month == {}

    def test_none_date_is_skipped(self):
        by_month = Analytics()._group_by_month([{"date": None}, {"date": "2026-10-09"}])
        assert by_month == {"2026-10": 1}

    def test_normal_dates_are_counted(self):
        by_month = Analytics()._group_by_month(
            [{"date": "2026-10-01"}, {"date": "2026-10-02"}, {"date": "2026-09-30"}]
        )
        assert by_month == {"2026-09": 1, "2026-10": 2}


class TestFetcherDateFallbacks:
    """日期解析失败是常态（各家 RSS 格式不一样），两处兜底都得活下来。"""

    def test_filter_by_date_keeps_item_with_bad_date(self):
        """按日期过滤时，日期没法解析的条目要保留（fail-open），不能悄悄丢掉。"""
        fetcher = NewsFetcher()
        bad = NewsItem(
            title="坏日期", url="https://example.com/1", published_at="不是日期"
        )
        fresh = NewsItem(
            title="今天",
            url="https://example.com/2",
            published_at=datetime.date.today().isoformat(),
        )

        kept = fetcher._filter_by_date([bad, fresh], days=7)

        assert bad in kept and fresh in kept

    def test_filter_by_date_drops_old_item(self):
        fetcher = NewsFetcher()
        old = NewsItem(
            title="很久以前", url="https://example.com/3", published_at="2000-01-01"
        )

        assert fetcher._filter_by_date([old], days=7) == []

    @pytest.mark.parametrize("raw", ["", None, "不是日期", "2026-13-45"])
    def test_parse_date_falls_back_to_today(self, raw):
        today = datetime.date.today().isoformat()
        assert NewsFetcher()._parse_date(raw).startswith(today)

    def test_parse_date_handles_rfc2822(self):
        """RSS 常见格式要能解析，别退化到兜底。"""
        assert (
            NewsFetcher()._parse_date("Wed, 08 Oct 2026 12:00:00 GMT") == "2026-10-08"
        )


class TestCoverFontFallback:
    """字体加载失败的兜底：回退默认字体，但必须告警——否则「变丑了」查不出来。"""

    def test_font_load_failure_falls_back_and_warns_once(self, monkeypatch, caplog):
        from src import cover_generator
        import os

        generator = cover_generator.CoverGenerator()
        if not any(os.path.exists(path) for path in generator._font_paths):
            pytest.skip("本机没有可用的字体文件，无法构造加载失败")

        real_truetype = cover_generator.ImageFont.truetype

        def boom(font=None, *args, **kwargs):
            # 只让「按路径加载」失败：Pillow 10+ 的 load_default() 内部也走 truetype，
            # 但它传的是 BytesIO，那是兜底本身，不能一起打掉
            if isinstance(font, str):
                raise OSError("字体文件损坏")
            return real_truetype(font, *args, **kwargs)

        monkeypatch.setattr(cover_generator.ImageFont, "truetype", boom)

        with caplog.at_level("WARNING"):
            first = generator._load_font(20)
            second = generator._load_font(20)  # 同一次运行里不该再刷一条

        assert first is not None and second is not None
        warnings = [
            record for record in caplog.records if "回退默认字体" in record.message
        ]
        assert len(warnings) == 1, "字体回退只该告警一次，否则每张封面都刷屏"

    def test_no_font_at_all_raises_instead_of_returning_none(self, monkeypatch):
        """连内置默认字体都加载不了时要抛错：封面宁可失败，也不能拿到一个 None 继续画。"""
        from src import cover_generator
        import os

        generator = cover_generator.CoverGenerator()
        if not any(os.path.exists(path) for path in generator._font_paths):
            pytest.skip("本机没有可用的字体文件")

        def always_boom(*args, **kwargs):
            raise OSError("没有任何可用字体")

        monkeypatch.setattr(cover_generator.ImageFont, "truetype", always_boom)

        with pytest.raises(OSError):
            generator._load_font(20)

    def test_successful_load_does_not_warn(self, caplog):
        from src import cover_generator
        import os

        generator = cover_generator.CoverGenerator()
        if not any(os.path.exists(path) for path in generator._font_paths):
            pytest.skip("本机没有可用的字体文件")

        with caplog.at_level("WARNING"):
            assert generator._load_font(20) is not None

        assert [r for r in caplog.records if "回退默认字体" in r.message] == []
