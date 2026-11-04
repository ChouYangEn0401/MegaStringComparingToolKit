"""
CASE_SPACE_FREE_EXACT／CASE_SPACE_SYMBOL_FREE_EXACT 與 StrFunc_RemoveAllWhitespace。

兩段都是「比 PREPROCESSED_EXACT 嚴的完全比對」：pyDMS 的比對階梯把它們放在單純完全比對與
前清理完全比對之間（由嚴到鬆），差一點大小寫／空白／符號的先配掉。
"""

import pandas as pd
import pytest

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_cleaning import NOPARS_STRATEGY_TABLE, StrFunc_RemoveAllWhitespace
from isd_str_sdk.str_matching.adapters import STRATEGY_TABLE, get_strategy_param_meta
from isd_str_sdk.str_matching.strategies.hybrid_matching import (
    CaseSpaceFreeExactMatchStrategy,
    CaseSpaceSymbolFreeExactMatchStrategy,
    PreprocessedExactMatchStrategy,
)


def _hit(cls, a, b):
    ctx = TwoSeriesComparisonContext(pd.Series({"L": a}), pd.Series({"R": b}))
    return cls("L", "R", 1.0).evaluate(ctx)


class TestRemoveAllWhitespace:
    def test_removes_every_kind_of_space(self):
        p = StrFunc_RemoveAllWhitespace("")
        p.input_str = "  National  Taiwan\u3000Univ.\t\n"
        assert p._handle() == "NationalTaiwanUniv."

    def test_registered_in_nopars_table(self):
        assert NOPARS_STRATEGY_TABLE["StrFunc_RemoveAllWhitespace"] is StrFunc_RemoveAllWhitespace


class TestCaseSpaceFreeExact:
    def test_case_and_space_do_not_matter(self):
        r = _hit(CaseSpaceFreeExactMatchStrategy, "National Taiwan University", "national  taiwan\u3000university")
        assert r.success and r.score == 1

    def test_punctuation_still_matters(self):
        r = _hit(CaseSpaceFreeExactMatchStrategy, "Texas A&M University", "Texas A M University")
        assert not r.success and r.score == 0

    def test_null_policy_default(self):
        r = _hit(CaseSpaceFreeExactMatchStrategy, None, "x")
        assert not r.success and r.score == -1.0

    def test_is_exact_match_and_name(self):
        s = CaseSpaceFreeExactMatchStrategy("L", "R", 1.0)
        assert s.IsExactMatch and "ExactMatch" in type(s).__name__


class TestCaseSpaceSymbolFreeExact:
    @pytest.mark.parametrize("a,b", [
        ("Texas A&M University", "Texas A M University"),
        ("Université de Montréal", "Universite de Montreal"),
        ("King's College-London", "Kings College London"),
    ])
    def test_symbols_and_foreign_letters_do_not_matter(self, a, b):
        assert _hit(CaseSpaceSymbolFreeExactMatchStrategy, a, b).success

    def test_stricter_than_preprocessed(self):
        # 停止詞／機構詞（de ↔ of）這一段不轉，要到 PREPROCESSED_EXACT 才比得中
        a, b = "University of Montreal", "Universite de Montreal"
        assert not _hit(CaseSpaceSymbolFreeExactMatchStrategy, a, b).success
        assert _hit(PreprocessedExactMatchStrategy, a, b).success

    def test_is_exact_match_and_name(self):
        s = CaseSpaceSymbolFreeExactMatchStrategy("L", "R", 1.0)
        assert s.IsExactMatch and "ExactMatch" in type(s).__name__


class TestRegistration:
    def test_strategy_table(self):
        assert STRATEGY_TABLE["CASE_SPACE_FREE_EXACT"] is CaseSpaceFreeExactMatchStrategy
        assert STRATEGY_TABLE["CASE_SPACE_SYMBOL_FREE_EXACT"] is CaseSpaceSymbolFreeExactMatchStrategy

    @pytest.mark.parametrize("key", ["CASE_SPACE_FREE_EXACT", "CASE_SPACE_SYMBOL_FREE_EXACT"])
    def test_null_policy_meta(self, key):
        # 兩欄比對策略都吃 NullPolicy：參數說明裡有那三個鍵
        assert {"null_mode", "empty_is_null", "null_like"} <= set(get_strategy_param_meta(key))
