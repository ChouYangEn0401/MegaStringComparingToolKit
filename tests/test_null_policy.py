"""
Tests for NullPolicy (0.4.6).

背景：pandas 讀 Excel 空格得到 NaN，舊版只擋 None，"nan" 字串會進 tokenizer
並以 1.0 分「配對成功」。這組測試釘住三種模式與所有兩欄策略的行為。
"""
import math

import pandas as pd
import pytest

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching import MatchingStrategyAdapter, NullMode, NullPolicy, STRATEGY_TABLE
from isd_str_sdk.str_matching.strategies.exact_matching import ExactMatchStrategy
from isd_str_sdk.str_matching.strategies.fuzzy_matching import (
    FuzzyRatioStrategy,
    JaroWinklerStrategy,
    LevenshteinStrategy,
)
from isd_str_sdk.str_matching.strategies.hybrid_matching import PreprocessedExactMatchStrategy
from isd_str_sdk.str_matching.strategies.structure_matching import (
    JaccardStrategy,
    LetterLCSStrategy,
    TwoSideInStringStrategy,
    WordLCSStrategy,
)

NAN = float("nan")


def _ctx(a, b) -> TwoSeriesComparisonContext:
    return TwoSeriesComparisonContext(row1=pd.Series({"a": a}), row2=pd.Series({"b": b}))


# 所有「兩欄字串」策略的建構器（名稱, factory(**kwargs)）
TWO_COLUMN_STRATEGIES = [
    ("Exact", lambda **kw: ExactMatchStrategy("a", "b", standard=None, **kw)),
    ("PreprocessedExact", lambda **kw: PreprocessedExactMatchStrategy("a", "b", standard=None, **kw)),
    ("Fuzzy", lambda **kw: FuzzyRatioStrategy("a", "b", standard=0.5, **kw)),
    ("Levenshtein", lambda **kw: LevenshteinStrategy("a", "b", standard=0.5, **kw)),
    ("JaroWinkler", lambda **kw: JaroWinklerStrategy("a", "b", standard=0.5, **kw)),
    ("Jaccard", lambda **kw: JaccardStrategy("a", "b", standard=0.5, **kw)),
    ("LetterLCS", lambda **kw: LetterLCSStrategy("a", "b", standard=0.5, **kw)),
    ("WordLCS", lambda **kw: WordLCSStrategy("a", "b", standard=0.5, **kw)),
    ("TwoSideIn", lambda **kw: TwoSideInStringStrategy("a", "b", standard=None, strategy_parameters=kw.pop("strategy_parameters", {}), **kw)),
]
IDS = [name for name, _ in TWO_COLUMN_STRATEGIES]
FACTORIES = [f for _, f in TWO_COLUMN_STRATEGIES]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. NullPolicy 本身
# ═══════════════════════════════════════════════════════════════════════════════

class TestNullPolicyUnit:
    def test_default_is_fail_mode(self):
        p = NullPolicy()
        assert p.mode is NullMode.FAIL
        assert p.empty_is_null is False
        assert p.null_like == frozenset()

    @pytest.mark.parametrize("value", [None, NAN, pd.NA, pd.NaT])
    def test_missing_scalars_are_null(self, value):
        assert NullPolicy().is_null(value) is True

    @pytest.mark.parametrize("value", ["", "   ", "nan", "None", "hello", 0, 1.5])
    def test_text_and_numbers_are_not_null_by_default(self, value):
        assert NullPolicy().is_null(value) is False

    def test_empty_is_null_option(self):
        p = NullPolicy(empty_is_null=True)
        assert p.is_null("") is True
        assert p.is_null("   ") is True
        assert p.is_null("x") is False

    def test_null_like_option_is_case_and_space_insensitive(self):
        p = NullPolicy(null_like=frozenset({"nan", "none", "n/a"}))
        assert p.is_null("NaN") is True
        assert p.is_null("  None ") is True
        assert p.is_null("N/A") is True
        assert p.is_null("Nonesuch") is False

    def test_intercept_fail_mode(self):
        p = NullPolicy()
        r = p.intercept(None, "x")
        assert r is not None and r.success is False and r.score == pytest.approx(-1.0)
        assert p.intercept(NAN, NAN).success is False
        assert p.intercept("x", "y") is None

    def test_intercept_match_if_both(self):
        p = NullPolicy(mode=NullMode.MATCH_IF_BOTH)
        both = p.intercept(NAN, None)
        assert both.success is True and both.score == pytest.approx(1.0)
        one = p.intercept(NAN, "x")
        assert one.success is False and one.score == pytest.approx(-1.0)
        assert p.intercept("x", "y") is None

    def test_intercept_as_text_never_intercepts(self):
        p = NullPolicy(mode=NullMode.AS_TEXT)
        assert p.intercept(None, NAN) is None

    def test_custom_null_score(self):
        p = NullPolicy(null_score=0.0)
        assert p.intercept(None, "x").score == pytest.approx(0.0)

    def test_from_params_parses_strings(self):
        p = NullPolicy.from_params({
            "null_mode": "Match_If_Both",
            "empty_is_null": "true",
            "null_like": "nan, None , n/a",
            "null_score": "0",
        })
        assert p.mode is NullMode.MATCH_IF_BOTH
        assert p.empty_is_null is True
        assert p.null_like == frozenset({"nan", "none", "n/a"})
        assert p.null_score == pytest.approx(0.0)

    def test_from_params_ignores_unknown_keys_and_empty(self):
        assert NullPolicy.from_params(None) == NullPolicy()
        assert NullPolicy.from_params({"strategy_mode": "any"}) == NullPolicy()

    def test_from_params_rejects_unknown_mode(self):
        with pytest.raises(ValueError):
            NullPolicy.from_params({"null_mode": "whatever"})

    def test_from_kwargs_prefers_explicit_object(self):
        explicit = NullPolicy(mode=NullMode.AS_TEXT)
        got = NullPolicy.from_kwargs({"null_policy": explicit, "strategy_parameters": {"null_mode": "fail"}})
        assert got is explicit

    def test_from_kwargs_rejects_wrong_type(self):
        with pytest.raises(TypeError):
            NullPolicy.from_kwargs({"null_policy": "fail"})

    def test_param_meta_schema(self):
        meta = NullPolicy.param_meta()
        assert set(meta) == {"null_mode", "empty_is_null", "null_like"}
        assert meta["null_mode"]["options"] == ["fail", "match_if_both", "as_text"]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. 所有兩欄策略：預設 FAIL 模式
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("factory", FACTORIES, ids=IDS)
class TestDefaultFailMode:
    def test_nan_vs_text_fails_with_minus_one(self, factory):
        r = factory().evaluate(_ctx(NAN, "hello"))
        assert r.success is False
        assert r.score == pytest.approx(-1.0)

    def test_nan_vs_nan_fails(self, factory):
        """這就是 FAULT hotfix 要修的假分數：兩個 NaN 不可以 1.0 配對成功。"""
        r = factory().evaluate(_ctx(NAN, NAN))
        assert r.success is False
        assert r.score == pytest.approx(-1.0)

    def test_none_vs_none_fails(self, factory):
        r = factory().evaluate(_ctx(None, None))
        assert r.success is False

    def test_pd_na_fails(self, factory):
        r = factory().evaluate(_ctx(pd.NA, "hello"))
        assert r.success is False

    def test_real_values_still_evaluated(self, factory):
        r = factory().evaluate(_ctx("hello", "hello"))
        assert r.success is True
        assert r.score == pytest.approx(1.0)

    def test_nan_text_literal_is_still_text(self, factory):
        """字串 "nan" 不是 null（除非放進 null_like），兩個 "nan" 字串相等。"""
        r = factory().evaluate(_ctx("nan", "nan"))
        assert r.success is True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. MATCH_IF_BOTH / AS_TEXT / empty_is_null / null_like 透過 strategy_parameters
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("factory", FACTORIES, ids=IDS)
class TestConfiguredModes:
    def test_match_if_both_via_params(self, factory):
        s = factory(strategy_parameters={"null_mode": "match_if_both"})
        both = s.evaluate(_ctx(NAN, None))
        assert both.success is True and both.score == pytest.approx(1.0)
        one = s.evaluate(_ctx(NAN, "hello"))
        assert one.success is False

    def test_match_if_both_via_object(self, factory):
        s = factory(null_policy=NullPolicy(mode=NullMode.MATCH_IF_BOTH))
        assert s.evaluate(_ctx(NAN, NAN)).success is True

    def test_as_text_restores_legacy_behaviour(self, factory):
        """AS_TEXT：不攔截，照 0.4.5 的方式比對。
        文字型策略把 NaN 變成 "nan" 字串 → 兩個 NaN 相等；
        EXACT 比的是原始值，NaN != NaN → 失敗（這也是 legacy）。"""
        s = factory(strategy_parameters={"null_mode": "as_text"})
        r = s.evaluate(_ctx(NAN, NAN))
        legacy_nan_equal = not (type(s) is ExactMatchStrategy)
        assert r.success is legacy_nan_equal
        # 不論哪個策略，AS_TEXT 都不會回 null_score
        assert r.score != pytest.approx(-1.0)

    def test_empty_is_null(self, factory):
        s = factory(strategy_parameters={"empty_is_null": True})
        r = s.evaluate(_ctx("", "   "))
        assert r.success is False and r.score == pytest.approx(-1.0)

    def test_null_like_texts(self, factory):
        s = factory(strategy_parameters={"null_like": "nan,none"})
        r = s.evaluate(_ctx("None", "NONE"))
        assert r.success is False and r.score == pytest.approx(-1.0)

    def test_null_like_plus_match_if_both(self, factory):
        s = factory(strategy_parameters={"null_like": ["none"], "null_mode": "match_if_both"})
        assert s.evaluate(_ctx("None", "none")).success is True
        assert s.evaluate(_ctx("None", "hello")).success is False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. 相容性：既有 API 路徑
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompatibility:
    def test_strategy_table_constructs_with_null_params(self):
        for name in ["EXACT", "FUZZY", "Levenshtein", "JaroWinkler", "JACCARD", "LetterLCS", "WordLCS", "PREPROCESSED_EXACT"]:
            cls = STRATEGY_TABLE[name]
            s = cls("a", "b", standard=0.5, strategy_parameters={"null_mode": "match_if_both"})
            assert s.evaluate(_ctx(NAN, NAN)).success is True, name

    def test_adapter_passes_special_params(self):
        """Level 2 adapter 只接受 str，所以用 null_like / empty_is_null 來驗證參數有傳到策略。"""
        strict = MatchingStrategyAdapter("WordLCS", standard=0.5, strategy_parameters={"null_like": "nan"})
        assert strict.run("nan", "nan").success is False
        assert strict.run("nan", "nan").score == pytest.approx(-1.0)
        default = MatchingStrategyAdapter("WordLCS", standard=0.5)
        assert default.run("nan", "nan").success is True
        both = MatchingStrategyAdapter("EXACT", standard=None,
                                       strategy_parameters={"empty_is_null": True, "null_mode": "match_if_both"})
        assert both.run("", "   ").success is True
        assert both.run("", "x").success is False

    def test_empty_strings_keep_legacy_meaning_by_default(self):
        # ExactMatch: "" == "" 仍然成功（既有 test_empty_strings_equal 的行為）
        assert ExactMatchStrategy("a", "b", standard=None).evaluate(_ctx("", "")).success is True
        # LCS: "" vs "" 仍是 0 分（既有 test_empty_strings 的行為）
        assert LetterLCSStrategy("a", "b", standard=0.5).evaluate(_ctx("", "")).score == pytest.approx(0.0)

    def test_lcs_none_legacy_test_still_holds(self):
        r = WordLCSStrategy("a", "b", standard=0.5).evaluate(_ctx(None, "hello"))
        assert r.success is False and r.score == pytest.approx(-1.0)
