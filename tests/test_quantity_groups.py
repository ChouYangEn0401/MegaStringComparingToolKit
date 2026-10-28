"""
Tests for count-threshold strategies in strategies/undone/quantity_groups.py (0.4.8).

背景：0.4.7 以前 FourJaccardRapidFuzzyScoreStrategy / NumberJaccardStrategy 寫
``self.standard = int(standard)``，判斷 ``intersection_len >= self.standard``。
ACA 傳 0.75 被截成 0 → 每一對都命中。PL 裁決（2026-10-28）：門檻是「共同詞個數」，
0.75 這種分數門檻是設定寫錯 —— 非整數直接 raise ValueError，整數值的浮點（4.0）當 4。
NewJACCARDStrategy 的 amount_mode 是同一種門檻（以前在 evaluate 裡 int() 截斷），比照辦理；
score_mode 的門檻是相似度比例，不動。
"""
import math

import pandas as pd
import pytest

from isd_str_sdk.base.AbstractStrategy import StrategyResult
from isd_str_sdk.core.contexts import (
    TwoSeriesComparisonContext,
    TwoSeriesComparisonContextWithStrategyPars,
)
from isd_str_sdk.str_matching import STRATEGY_TABLE, MatchingStrategyAdapter
from isd_str_sdk.str_matching.strategies.undone.quantity_groups import (
    FourJaccardRapidFuzzyScoreStrategy,
    NewJACCARDStrategy,
    NumberJaccardStrategy,
)

COUNT_CLASSES = [NumberJaccardStrategy, FourJaccardRapidFuzzyScoreStrategy]

# 非整數 / 不是數字 → ValueError
BAD_STANDARDS = [0.75, 4.5, 0.5, "0.75", "4.5", None, "abc", float("nan"), float("inf")]
# 整數值 → 收下，一律變成 int
GOOD_STANDARDS = [(4, 4), (4.0, 4), ("4", 4), ("4.0", 4), (0, 0), (1, 1)]


def _ctx(a, b) -> TwoSeriesComparisonContext:
    return TwoSeriesComparisonContext(row1=pd.Series({"a": a}), row2=pd.Series({"b": b}))


def _jctx(a, b, pars) -> TwoSeriesComparisonContextWithStrategyPars:
    return TwoSeriesComparisonContextWithStrategyPars(
        row1=pd.Series({"a": a}), row2=pd.Series({"b": b}), stra_pars=pars
    )


AMOUNT = {"split_segment": " ", "strategy_mode": "amount_mode"}
SCORE = {"split_segment": " ", "strategy_mode": "score_mode"}

# 共同詞：NATIONAL TAIWAN UNIVERSITY HOSPITAL = 4 個
A4 = "NATIONAL TAIWAN UNIVERSITY HOSPITAL TAIPEI"
B4 = "NATIONAL TAIWAN UNIVERSITY HOSPITAL HSINCHU"
# 共同詞 3 個
B3 = "NATIONAL TAIWAN UNIVERSITY CLINIC"
# 共同詞 0 個
B0 = "KYOTO MEDICAL SCHOOL"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. 非整數門檻 raise（bug 本體：0.75 不再被截成 0）
# ═══════════════════════════════════════════════════════════════════════════════

class TestRejectNonIntegerThreshold:
    @pytest.mark.parametrize("cls", COUNT_CLASSES)
    @pytest.mark.parametrize("standard", BAD_STANDARDS)
    def test_raises_value_error(self, cls, standard):
        with pytest.raises(ValueError):
            cls(df1="a", df2="b", standard=standard)

    @pytest.mark.parametrize("cls", COUNT_CLASSES)
    def test_message_explains_count_semantics(self, cls):
        with pytest.raises(ValueError) as ei:
            cls(df1="a", df2="b", standard=0.75)
        msg = str(ei.value)
        assert cls.__name__ in msg
        assert "共同詞個數" in msg
        assert "整數" in msg
        assert "0.75" in msg
        assert "設定寫錯" in msg

    def test_aca_call_form_via_adapter_raises(self):
        # ACA tests/pris_acdb_upgrade/wos_matching_pris_main.py 的寫法（傳類別而非字串鍵）
        with pytest.raises(ValueError):
            MatchingStrategyAdapter(FourJaccardRapidFuzzyScoreStrategy, 0.75)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. 整數值門檻照收、型別是 int
# ═══════════════════════════════════════════════════════════════════════════════

class TestAcceptIntegerThreshold:
    @pytest.mark.parametrize("cls", COUNT_CLASSES)
    @pytest.mark.parametrize("standard,expected", GOOD_STANDARDS)
    def test_integer_valued_is_accepted_as_int(self, cls, standard, expected):
        s = cls(df1="a", df2="b", standard=standard)
        assert s.standard == expected
        assert type(s.standard) is int

    def test_adapter_with_integer_threshold(self):
        r = MatchingStrategyAdapter(NumberJaccardStrategy, 4).run(A4, B4)
        assert r.success is True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. 正反例：門檻是共同詞個數
# ═══════════════════════════════════════════════════════════════════════════════

class TestCountSemantics:
    @pytest.mark.parametrize("cls", COUNT_CLASSES)
    def test_four_shared_words_meets_four(self, cls):
        r = cls(df1="a", df2="b", standard=4).evaluate(_ctx(A4, B4))
        assert isinstance(r, StrategyResult)
        assert r.success is True

    @pytest.mark.parametrize("cls", COUNT_CLASSES)
    def test_three_shared_words_misses_four(self, cls):
        r = cls(df1="a", df2="b", standard=4).evaluate(_ctx(A4, B3))
        assert r.success is False

    @pytest.mark.parametrize("cls", COUNT_CLASSES)
    def test_float_four_behaves_like_four(self, cls):
        for b in (B4, B3, B0):
            r_int = cls(df1="a", df2="b", standard=4).evaluate(_ctx(A4, b))
            r_flt = cls(df1="a", df2="b", standard=4.0).evaluate(_ctx(A4, b))
            assert (r_int.success, r_int.score) == (r_flt.success, r_flt.score)

    @pytest.mark.parametrize("cls", COUNT_CLASSES)
    def test_no_shared_words_misses_one(self, cls):
        # 修前：0.75 → 0 → 這一對也命中；現在門檻至少要是整數，1 個共同詞都沒有就不命中
        r = cls(df1="a", df2="b", standard=1).evaluate(_ctx(A4, B0))
        assert r.success is False

    def test_number_jaccard_score_is_jaccard_ratio(self):
        r = NumberJaccardStrategy(df1="a", df2="b", standard=4).evaluate(_ctx(A4, B4))
        assert math.isclose(r.score, 4 / 6)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. NewJACCARDStrategy：amount_mode 比照辦理，score_mode 不動
# ═══════════════════════════════════════════════════════════════════════════════

class TestNewJaccardAmountMode:
    def test_registered_in_strategy_table(self):
        assert STRATEGY_TABLE["NewJACCARDStrategy"] is NewJACCARDStrategy

    @pytest.mark.parametrize("standard", [0.75, 4.5, "0.75", "abc", float("nan")])
    def test_amount_mode_non_integer_raises(self, standard):
        with pytest.raises(ValueError) as ei:
            NewJACCARDStrategy(df1="a", df2="b", standard=standard, strategy_parameters=dict(AMOUNT))
        assert "共同詞個數" in str(ei.value)

    @pytest.mark.parametrize("standard", [2, 2.0, "2", "2.0"])
    def test_amount_mode_integer_accepted(self, standard):
        s = NewJACCARDStrategy(df1="a", df2="b", standard=standard, strategy_parameters=dict(AMOUNT))
        assert s.evaluate(_jctx("x y z", "x y w", AMOUNT)).success is True   # 共同 2
        assert s.evaluate(_jctx("x y z", "x w v", AMOUNT)).success is False  # 共同 1

    def test_amount_mode_score_is_intersection_count(self):
        s = NewJACCARDStrategy(df1="a", df2="b", standard=4, strategy_parameters=dict(AMOUNT))
        r = s.evaluate(_jctx(A4, B4, AMOUNT))
        assert r.success is True
        assert r.score == 4.0

    @pytest.mark.parametrize("standard", [None, ""])
    def test_amount_mode_empty_standard_keeps_legacy_zero(self, standard):
        # 舊行為：None / "" 在 amount_mode 等於門檻 0，這次不改
        s = NewJACCARDStrategy(df1="a", df2="b", standard=standard, strategy_parameters=dict(AMOUNT))
        assert s.evaluate(_jctx("x", "y", AMOUNT)).success is True

    def test_score_mode_fraction_threshold_untouched(self):
        s = NewJACCARDStrategy(df1="a", df2="b", standard=0.75, strategy_parameters=dict(SCORE))
        assert s.standard == 0.75
        # 共同 3 / 聯集 4 = 0.75 → 命中；共同 2 / 聯集 4 = 0.5 → 不命中
        assert s.evaluate(_jctx("x y z", "x y z w", SCORE)).success is True
        assert s.evaluate(_jctx("x y z", "x y w", SCORE)).success is False
