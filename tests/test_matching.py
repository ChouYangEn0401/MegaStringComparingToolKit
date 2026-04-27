"""
Tests for isd_str_sdk string-matching strategies.

覆蓋範圍
--------
- ExactMatchStrategy              (exact_matching)
- FuzzyRatioStrategy              (fuzzy_matching)
- LevenshteinStrategy             (fuzzy_matching)
- JaroWinklerStrategy             (fuzzy_matching)
- TwoSideInStringStrategy         (structure_matching)
- TwoSideInWith3WordsStringStrategy (structure_matching)
- LetterLCSStrategy               (structure_matching)
- WordLCSStrategy                 (structure_matching)
- JaccardStrategy                 (structure_matching)

全策略的共同測試
- success 旗標相對於 standard 閾值
- score 數值正確
- StrategyResult.run() 包裝方法
- 空字串 / None 邊界狀況

注意：HybridMatchingStrategy 需要 Excel 權控表，nlp_matching 需要
      sentence-transformers，均略過。LogicGate 策略的 context 定義
      與目前的 ChildrenValueComparisonContext 不相容，亦略過。
"""

import pytest
import pandas as pd

from isd_str_sdk.core.contexts import (
    TwoSeriesComparisonContext,
    TwoSeriesComparisonContextWithStrategyPars,
)
from isd_str_sdk.str_matching.strategies.exact_matching import ExactMatchStrategy
from isd_str_sdk.str_matching.strategies.fuzzy_matching import (
    FuzzyRatioStrategy,
    LevenshteinStrategy,
    JaroWinklerStrategy,
)
from isd_str_sdk.str_matching.strategies.structure_matching import (
    TwoSideInStringStrategy,
    TwoSideInWith3WordsStringStrategy,
    LetterLCSStrategy,
    WordLCSStrategy,
    JaccardStrategy,
)


# ── helper ───────────────────────────────────────────────────────────────────
def _ctx(a: str, b: str) -> TwoSeriesComparisonContext:
    """建立含有 'a' 欄 (row1) 和 'b' 欄 (row2) 的 TwoSeriesComparisonContext。"""
    return TwoSeriesComparisonContext(
        row1=pd.Series({"a": a}),
        row2=pd.Series({"b": b}),
    )


def _ctx_pars(a: str, b: str, **pars) -> TwoSeriesComparisonContextWithStrategyPars:
    return TwoSeriesComparisonContextWithStrategyPars(
        row1=pd.Series({"a": a}),
        row2=pd.Series({"b": b}),
        stra_pars=pars,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ExactMatchStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestExactMatchStrategy:
    def _s(self):
        return ExactMatchStrategy("a", "b", standard=None)

    def test_identical_strings_succeed(self):
        r = self._s().evaluate(_ctx("hello", "hello"))
        assert r.success is True
        assert r.score == 1

    def test_different_strings_fail(self):
        r = self._s().evaluate(_ctx("hello", "world"))
        assert r.success is False
        assert r.score == 0

    def test_case_sensitive(self):
        r = self._s().evaluate(_ctx("hello", "Hello"))
        assert r.success is False

    def test_empty_strings_equal(self):
        r = self._s().evaluate(_ctx("", ""))
        assert r.success is True

    def test_one_empty_string(self):
        r = self._s().evaluate(_ctx("hello", ""))
        assert r.success is False

    def test_is_exact_match_property(self):
        assert self._s().IsExactMatch is True

    def test_run_method_returns_bool(self):
        result = self._s().run(_ctx("abc", "abc"))
        assert result is True


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FuzzyRatioStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestFuzzyRatioStrategy:
    def _s(self, threshold: float):
        return FuzzyRatioStrategy("a", "b", standard=threshold)

    def test_identical_score_is_one(self):
        r = self._s(0.9).evaluate(_ctx("hello", "hello"))
        assert r.score == pytest.approx(1.0)
        assert r.success is True

    def test_completely_different_score_is_zero(self):
        r = self._s(0.5).evaluate(_ctx("abcde", "vwxyz"))
        assert r.score == pytest.approx(0.0)
        assert r.success is False

    def test_near_identical_above_threshold(self):
        # 'hello' vs 'helo' → 8/9 ≈ 0.889 > 0.8
        r = self._s(0.8).evaluate(_ctx("hello", "helo"))
        assert r.success is True
        assert r.score > 0.8

    def test_above_threshold_succeeds(self):
        r = self._s(0.5).evaluate(_ctx("hello", "helo"))
        assert r.success is True

    def test_below_threshold_fails(self):
        r = self._s(0.95).evaluate(_ctx("hello", "helo"))
        assert r.success is False

    def test_score_in_01_range(self):
        r = self._s(0.5).evaluate(_ctx("apple", "orange"))
        assert 0.0 <= r.score <= 1.0

    def test_is_not_exact_match(self):
        assert self._s(0.5).IsExactMatch is False


# ═══════════════════════════════════════════════════════════════════════════════
# 3. LevenshteinStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestLevenshteinStrategy:
    def _s(self, threshold: float):
        return LevenshteinStrategy("a", "b", standard=threshold)

    def test_identical_score_is_one(self):
        r = self._s(0.9).evaluate(_ctx("hello", "hello"))
        assert r.score == pytest.approx(1.0)
        assert r.success is True

    def test_completely_different_score_is_zero(self):
        r = self._s(0.5).evaluate(_ctx("abc", "xyz"))
        assert r.score == pytest.approx(0.0)
        assert r.success is False

    def test_one_char_difference(self):
        # 'hello' vs 'hellx': 1 edit out of 5 chars → 0.8
        r = self._s(0.5).evaluate(_ctx("hello", "hellx"))
        assert r.score == pytest.approx(0.8)
        assert r.success is True

    def test_threshold_respected_above(self):
        r = self._s(0.8).evaluate(_ctx("hello", "hellx"))
        assert r.success is True

    def test_threshold_respected_below(self):
        r = self._s(0.9).evaluate(_ctx("hello", "hellx"))
        assert r.success is False

    def test_empty_strings_identical(self):
        r = self._s(0.9).evaluate(_ctx("", ""))
        assert r.score == pytest.approx(1.0)
        assert r.success is True

    def test_empty_vs_nonempty(self):
        r = self._s(0.5).evaluate(_ctx("", "hello"))
        assert r.score == pytest.approx(0.0)
        assert r.success is False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. JaroWinklerStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestJaroWinklerStrategy:
    def _s(self, threshold: float):
        return JaroWinklerStrategy("a", "b", standard=threshold)

    def test_identical_score_is_one(self):
        r = self._s(0.9).evaluate(_ctx("hello", "hello"))
        assert r.score == pytest.approx(1.0)
        assert r.success is True

    def test_completely_different_score_is_zero(self):
        r = self._s(0.5).evaluate(_ctx("abc", "xyz"))
        assert r.score == pytest.approx(0.0)
        assert r.success is False

    def test_shared_prefix_boosts_score(self):
        # Jaro-Winkler rewards common prefix strings
        r = self._s(0.5).evaluate(_ctx("hello", "helo"))
        assert r.score > 0.9    # > 0.953

    def test_threshold_above_succeeds(self):
        r = self._s(0.9).evaluate(_ctx("hello", "helo"))
        assert r.success is True

    def test_threshold_below_fails(self):
        r = self._s(0.99).evaluate(_ctx("hello", "helo"))
        assert r.success is False

    def test_score_in_01_range(self):
        r = self._s(0.5).evaluate(_ctx("apple", "orange"))
        assert 0.0 <= r.score <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TwoSideInStringStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestTwoSideInStringStrategy:
    def _s(self, mode: str):
        return TwoSideInStringStrategy("a", "b", standard=None, strategy_parameters={"strategy_mode": mode})

    def test_any_mode_a_in_b(self):
        # "hello" is in "hello world"
        r = self._s("any").evaluate(_ctx("hello", "hello world"))
        assert r.success is True

    def test_any_mode_b_in_a(self):
        r = self._s("any").evaluate(_ctx("hello world", "world"))
        assert r.success is True

    def test_any_mode_no_match(self):
        r = self._s("any").evaluate(_ctx("apple", "banana"))
        assert r.success is False

    def test_a_in_b_mode_success(self):
        r = self._s("a_in_b").evaluate(_ctx("hello", "hello world"))
        assert r.success is True

    def test_a_in_b_mode_failure(self):
        r = self._s("a_in_b").evaluate(_ctx("hello world", "hello"))
        assert r.success is False

    def test_b_in_a_mode_success(self):
        r = self._s("b_in_a").evaluate(_ctx("hello world", "hello"))
        assert r.success is True

    def test_b_in_a_mode_failure(self):
        r = self._s("b_in_a").evaluate(_ctx("hello", "hello world"))
        assert r.success is False

    def test_score_is_1_on_success(self):
        r = self._s("any").evaluate(_ctx("hi", "hi there"))
        assert r.score == 1

    def test_score_is_0_on_failure(self):
        r = self._s("any").evaluate(_ctx("apple", "mango"))
        assert r.score == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 6. TwoSideInWith3WordsStringStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestTwoSideInWith3WordsStringStrategy:
    def _s(self):
        return TwoSideInWith3WordsStringStrategy("a", "b", standard=None)

    def test_long_substring_succeeds(self):
        # "ello" (4 chars) in "hello"
        r = self._s().evaluate(_ctx("ello", "hello"))
        assert r.success is True

    def test_short_substring_fails(self):
        # "hi" (2 chars) is too short even if it would match
        r = self._s().evaluate(_ctx("hi", "hi there"))
        assert r.success is False

    def test_exactly_3_chars_succeeds(self):
        r = self._s().evaluate(_ctx("hel", "hello world"))
        assert r.success is True

    def test_no_match(self):
        r = self._s().evaluate(_ctx("apple", "banana"))
        assert r.success is False

    def test_bidirectional_longer_b_in_a(self):
        r = self._s().evaluate(_ctx("hello world", "world"))
        assert r.success is True


# ═══════════════════════════════════════════════════════════════════════════════
# 7. LetterLCSStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestLetterLCSStrategy:
    def _s(self, threshold: float):
        return LetterLCSStrategy("a", "b", standard=threshold)

    def test_identical_score_is_one(self):
        r = self._s(0.9).evaluate(_ctx("abc", "abc"))
        assert r.score == pytest.approx(1.0)
        assert r.success is True

    def test_half_overlap(self):
        # "abcd" vs "ab": LCS = 2, max_len = 4 → 0.5
        r = self._s(0.4).evaluate(_ctx("abcd", "ab"))
        assert r.score == pytest.approx(0.5)
        assert r.success is True

    def test_no_overlap_score_zero(self):
        r = self._s(0.5).evaluate(_ctx("aaa", "bbb"))
        assert r.score == pytest.approx(0.0)
        assert r.success is False

    def test_threshold_above_succeeds(self):
        r = self._s(0.9).evaluate(_ctx("abc", "abc"))
        assert r.success is True

    def test_threshold_below_fails(self):
        r = self._s(0.6).evaluate(_ctx("abcd", "ab"))
        assert r.success is False

    def test_none_input_returns_failure(self):
        ctx = TwoSeriesComparisonContext(
            row1=pd.Series({"a": None}),
            row2=pd.Series({"b": "hello"}),
        )
        r = self._s(0.5).evaluate(ctx)
        assert r.success is False
        assert r.score == pytest.approx(-1.0)

    def test_empty_strings(self):
        r = self._s(0.5).evaluate(_ctx("", ""))
        assert r.score == pytest.approx(0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. WordLCSStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestWordLCSStrategy:
    def _s(self, threshold: float):
        return WordLCSStrategy("a", "b", standard=threshold)

    def test_identical_score_is_one(self):
        r = self._s(0.9).evaluate(_ctx("apple banana cherry", "apple banana cherry"))
        assert r.score == pytest.approx(1.0)
        assert r.success is True

    def test_partial_overlap(self):
        # "apple banana cherry" vs "apple banana" → LCS = 2, max_len = 3 → 0.667
        r = self._s(0.5).evaluate(_ctx("apple banana cherry", "apple banana"))
        assert r.score == pytest.approx(2 / 3)
        assert r.success is True

    def test_no_word_overlap(self):
        r = self._s(0.5).evaluate(_ctx("apple banana", "cherry mango"))
        assert r.score == pytest.approx(0.0)
        assert r.success is False

    def test_single_word_identical(self):
        r = self._s(0.9).evaluate(_ctx("MIT", "MIT"))
        assert r.score == pytest.approx(1.0)

    def test_threshold_below_fails(self):
        r = self._s(0.9).evaluate(_ctx("apple banana cherry", "apple banana"))
        assert r.success is False

    def test_semicolon_delimiter(self):
        # WordLCS tokenizes on semicolons too
        r = self._s(0.9).evaluate(_ctx("apple;banana", "apple;banana"))
        assert r.score == pytest.approx(1.0)

    def test_none_input_returns_failure(self):
        ctx = TwoSeriesComparisonContext(
            row1=pd.Series({"a": None}),
            row2=pd.Series({"b": "hello"}),
        )
        r = self._s(0.5).evaluate(ctx)
        assert r.success is False
        assert r.score == pytest.approx(-1.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. JaccardStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestJaccardStrategy:
    def _s(self, threshold: float):
        return JaccardStrategy("a", "b", standard=threshold)

    def test_identical_score_is_one(self):
        r = self._s(0.9).evaluate(_ctx("apple banana cherry", "apple banana cherry"))
        assert r.score == pytest.approx(1.0)
        assert r.success is True

    def test_completely_disjoint_score_is_zero(self):
        r = self._s(0.5).evaluate(_ctx("apple", "banana"))
        assert r.score == pytest.approx(0.0)
        assert r.success is False

    def test_partial_overlap(self):
        # {"apple", "banana"} ∩ {"apple", "cherry"} = {"apple"}
        # union = {"apple", "banana", "cherry"} → 1/3 ≈ 0.333
        r = self._s(0.1).evaluate(_ctx("apple banana", "apple cherry"))
        assert r.score == pytest.approx(1 / 3)
        assert r.success is True

    def test_subset_relationship(self):
        # {"apple"} ⊂ {"apple", "banana"} → 1/2 = 0.5
        r = self._s(0.4).evaluate(_ctx("apple", "apple banana"))
        assert r.score == pytest.approx(0.5)
        assert r.success is True

    def test_threshold_above_succeeds(self):
        r = self._s(0.9).evaluate(_ctx("apple banana cherry", "apple banana cherry"))
        assert r.success is True

    def test_threshold_below_fails(self):
        r = self._s(0.9).evaluate(_ctx("apple banana", "apple cherry"))
        assert r.success is False

    def test_duplicate_words_set_semantics(self):
        # Jaccard operates on sets, duplicates are counted once
        r = self._s(0.9).evaluate(_ctx("apple apple", "apple"))
        assert r.score == pytest.approx(1.0)
