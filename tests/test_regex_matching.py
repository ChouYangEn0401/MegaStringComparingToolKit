"""
Tests for the regex matching strategies (0.4.9).

- RegexExtractExactStrategy     擷取後比對
- RegexRuleStrategy             一欄放 regex 規則
- RegexNamedGroupsStrategy      具名群組逐欄比
- RegexNormalizedExactStrategy  規則表正規化後完全比對
"""
import pickle
import time

import pandas as pd
import pytest

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching import (
    STRATEGY_TABLE,
    MatchingStrategyAdapter,
    NullMode,
    NullPolicy,
    get_strategy_param_meta,
    match,
)
from isd_str_sdk.str_matching.strategies.regex_matching import (
    RegexExtractExactStrategy,
    RegexNamedGroupsStrategy,
    RegexNormalizedExactStrategy,
    RegexRuleStrategy,
)

NAN = float("nan")


def _ctx(a, b) -> TwoSeriesComparisonContext:
    return TwoSeriesComparisonContext(row1=pd.Series({"a": a}), row2=pd.Series({"b": b}))


DOI = r"10\.\d{4,9}/\S+"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. RegexExtractExactStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegexExtractExact:
    def _s(self, standard=None, **kw):
        return RegexExtractExactStrategy("a", "b", standard, **kw)

    def test_doi_inside_different_strings(self):
        s = self._s(pattern=DOI, ignore_case=True)
        r = s.evaluate(_ctx("Smith 2020, doi:10.1000/ABC.1", "https://doi.org/10.1000/abc.1"))
        assert r.success is True and r.score == 1
        assert s.evaluate(_ctx("doi:10.1000/abc.1", "doi:10.1000/abc.2")).success is False

    def test_case_sensitive_by_default(self):
        s = self._s(pattern=DOI)
        assert s.evaluate(_ctx("10.1000/ABC", "10.1000/abc")).success is False

    def test_nothing_extracted_fails_with_zero(self):
        s = self._s(pattern=r"\d{4}")
        r = s.evaluate(_ctx("no year", "no year"))
        assert r.success is False and r.score == 0.0
        assert s.evaluate(_ctx("1999", "none")).success is False

    def test_group_index_and_name(self):
        by_index = self._s(pattern=r"ISSN\s*(\d{4}-\d{3}[\dX])", group=1)
        assert by_index.evaluate(_ctx("ISSN 1234-567X", "Journal (ISSN1234-567X)")).success is True
        by_name = self._s(pattern=r"(?P<zip>\d{3,5})\s*,?\s*Taiwan", group="zip")
        assert by_name.evaluate(_ctx("Taipei 10617, Taiwan", "Taipei City 10617 Taiwan")).success is True
        # 群組號碼從字串來（GUI）
        assert self._s(pattern=r"(\d+)-(\d+)", group="2").evaluate(_ctx("1-9", "5-9")).success is True

    def test_right_pattern(self):
        s = self._s(pattern=r"\((\d{4})\)", right_pattern=r"year=(\d{4})", group=1)
        assert s.evaluate(_ctx("Title (2021)", "id=7&year=2021")).success is True

    def test_all_list_and_all_set(self):
        text1, text2 = "codes A1 B2 C3", "C3 then A1 B2"
        lst = self._s(pattern=r"[A-Z]\d", extract_mode="all_list")
        assert lst.evaluate(_ctx(text1, text2)).success is False          # 順序不同
        assert lst.evaluate(_ctx(text1, "x A1 B2 C3")).success is True
        st = self._s(pattern=r"[A-Z]\d", extract_mode="all_set")
        assert st.evaluate(_ctx(text1, text2)).score == pytest.approx(1.0)
        partial = self._s(0.5, pattern=r"[A-Z]\d", extract_mode="all_set").evaluate(_ctx("A1 B2", "A1 C3"))
        assert partial.score == pytest.approx(1 / 3) and partial.success is False
        assert st.IsExactMatch is False and lst.IsExactMatch is True

    def test_construction_errors(self):
        with pytest.raises(ValueError, match="pattern"):
            self._s()
        with pytest.raises(ValueError, match="regex"):
            self._s(pattern="(unclosed")
        with pytest.raises(ValueError, match="群組"):
            self._s(pattern=r"(\d+)", group=2)
        with pytest.raises(ValueError, match="群組"):
            self._s(pattern=r"(\d+)", group="nope")
        with pytest.raises(ValueError, match="extract_mode"):
            self._s(pattern=r"\d", extract_mode="weird")

    def test_params_via_strategy_parameters_and_level1(self):
        s = self._s(strategy_parameters={"pattern": r"\d{4}", "ignore_case": "true"})
        assert s.ignore_case is True
        assert s.evaluate(_ctx("in 2020", "2020!")).success is True
        result = match(["Paper A (2019)", "Paper B (2021)"], ["2021 issue", "2019 issue"],
                       strategy="REGEX_EXTRACT_EXACT", threshold=1, pattern=r"\d{4}")
        assert result == [("Paper A (2019)", "2019 issue", 1), ("Paper B (2021)", "2021 issue", 1)]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RegexRuleStrategy
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegexRule:
    def _s(self, **kw):
        return RegexRuleStrategy("a", "b", None, **kw)

    def test_rule_on_right_by_default(self):
        s = self._s()
        rule = r"\bNatl?\.?\s+Taiwan\s+Univ"
        assert s.evaluate(_ctx("Dept Chem, Natl Taiwan Univ, Taipei", rule)).success is True
        assert s.evaluate(_ctx("Natl Tsing Hua Univ", rule)).success is False

    def test_rule_side_left(self):
        s = self._s(rule_side="left")
        assert s.evaluate(_ctx(r"^Kyoto", "Kyoto University")).success is True
        assert s.evaluate(_ctx("Kyoto University", r"^Kyoto")).success is False

    def test_match_modes_and_ignore_case(self):
        text = "Kyoto University"
        assert self._s(match_mode="fullmatch").evaluate(_ctx(text, "Kyoto")).success is False
        assert self._s(match_mode="fullmatch").evaluate(_ctx(text, r"Kyoto \w+")).success is True
        assert self._s(match_mode="match").evaluate(_ctx(text, "University")).success is False
        assert self._s().evaluate(_ctx(text, "university")).success is False
        assert self._s(ignore_case=True).evaluate(_ctx(text, "university")).success is True

    def test_strip_rule(self):
        assert self._s().evaluate(_ctx("Kyoto", "Kyoto ")).success is True
        assert self._s(strip_rule=False).evaluate(_ctx("Kyoto", "Kyoto ")).success is False

    def test_empty_rule_never_matches(self):
        r = self._s().evaluate(_ctx("anything", "   "))
        assert r.success is False and r.score == 0.0

    def test_invalid_rule_fails_or_raises(self):
        r = self._s().evaluate(_ctx("abc", "(unclosed"))
        assert r.success is False and r.score == pytest.approx(-1.0)
        with pytest.raises(ValueError, match="regex"):
            self._s(on_invalid="raise").evaluate(_ctx("abc", "(unclosed"))

    def test_timeout_protects_batch(self):
        s = self._s(regex_timeout=0.05)
        t0 = time.perf_counter()
        r = s.evaluate(_ctx("a" * 40 + "b", r"(a|aa)+$"))
        assert time.perf_counter() - t0 < 2.0
        assert r.success is False and r.score == pytest.approx(-1.0)
        with pytest.raises(ValueError, match="秒"):
            self._s(regex_timeout=0.05, on_invalid="raise").evaluate(_ctx("a" * 40 + "b", r"(a|aa)+$"))

    def test_compiled_rules_are_cached_and_dropped_on_pickle(self):
        s = self._s()
        s.evaluate(_ctx("abc", "b"))
        s.evaluate(_ctx("xbz", "b"))
        assert list(s._cache) == ["b"]
        clone = pickle.loads(pickle.dumps(s))
        assert clone._cache == {} and clone.evaluate(_ctx("abc", "b")).success is True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. RegexNamedGroupsStrategy
# ═══════════════════════════════════════════════════════════════════════════════

CITE = r"(?P<year>\d{4})\s+Vol\s*(?P<vol>\d+)(?:\((?P<no>\d+)\))?(?:\s+pp\s*(?P<pages>[\d-]+))?"


class TestRegexNamedGroups:
    def _s(self, standard=None, **kw):
        return RegexNamedGroupsStrategy("a", "b", standard, **kw)

    def test_all_fields_equal(self):
        r = self._s(pattern=CITE).evaluate(_ctx("2021 Vol 12(3) pp 45-67", "2021 Vol12(3) pp45-67"))
        assert r.success is True and r.score == pytest.approx(1.0)
        assert [c.success for c in r.children] == [True, True, True, True]

    def test_partial_score_and_children(self):
        s = self._s(0.7, pattern=CITE)
        r = s.evaluate(_ctx("2021 Vol 12(3) pp 45-67", "2021 Vol 12(4) pp 45-67"))
        assert r.score == pytest.approx(3 / 4) and r.success is True
        assert [c.score for c in r.children] == [1, 1, 0, 1]
        assert self._s(pattern=CITE).evaluate(_ctx("2021 Vol 12(3)", "2021 Vol 12(4)")).success is False

    def test_group_missing_on_both_sides_is_not_counted(self):
        r = self._s(pattern=CITE).evaluate(_ctx("2021 Vol 12", "2021 Vol 12"))
        assert r.score == pytest.approx(1.0)  # no / pages 兩邊都沒有 → 不列入計分
        assert [c.score for c in r.children] == [1, 1, None, None]
        one_side = self._s(pattern=CITE).evaluate(_ctx("2021 Vol 12(3)", "2021 Vol 12"))
        assert one_side.score == pytest.approx(2 / 3)

    def test_groups_subset(self):
        s = self._s(pattern=CITE, groups="year, vol")
        assert s.groups == ["year", "vol"]
        assert s.evaluate(_ctx("2021 Vol 12(3)", "2021 Vol 12(9)")).success is True

    def test_pattern_not_matching_fails(self):
        r = self._s(pattern=CITE).evaluate(_ctx("2021 Vol 12", "no citation here"))
        assert r.success is False and r.score == 0.0

    def test_right_pattern_and_ignore_case(self):
        s = self._s(pattern=r"(?P<last>\w+),\s*(?P<first>\w+)", right_pattern=r"(?P<first>\w+)\s+(?P<last>\w+)",
                    match_mode="fullmatch", ignore_case=True)
        assert s.evaluate(_ctx("Chou, YangEn", "yangen chou")).success is True

    def test_construction_errors(self):
        with pytest.raises(ValueError, match="具名群組"):
            self._s(pattern=r"(\d+)")
        with pytest.raises(ValueError, match="具名群組"):
            self._s(pattern=CITE, groups="year,missing")
        with pytest.raises(ValueError, match="match_mode"):
            self._s(pattern=CITE, match_mode="nope")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. RegexNormalizedExactStrategy
# ═══════════════════════════════════════════════════════════════════════════════

RULES_TEXT = r"""
# 縮寫展開
\bUniv\b\.? => University
\bNatl\b\.? => National
# 去掉系所前綴
^Dept\.?\s+of\s+[^,]+,\s* =>
\d{3,5}
"""


class TestRegexNormalizedExact:
    def _s(self, **kw):
        return RegexNormalizedExactStrategy("a", "b", None, **kw)

    def test_rules_from_text(self):
        s = self._s(rules=RULES_TEXT)
        assert len(s.rules) == 4
        assert s.normalize("Dept. of Chemistry, Natl. Taiwan Univ. Taipei 10617") == "National Taiwan University Taipei"
        assert s.evaluate(_ctx("Natl Taiwan Univ", "National Taiwan University")).success is True
        assert s.evaluate(_ctx("Natl Taiwan Univ", "National Tsing Hua University")).success is False

    def test_rules_from_pairs_with_backrefs(self):
        s = self._s(rules=[(r"(\w+),\s*(\w+)", r"\2 \1"), ("[.]",)])
        assert s.normalize("Chou, YangEn.") == "YangEn Chou"

    def test_order_matters(self):
        a = self._s(rules=[("Univ", "University"), ("University", "U")])
        b = self._s(rules=[("University", "U"), ("Univ", "University")])
        assert a.normalize("Univ") == "U"
        assert b.normalize("Univ") == "University"

    def test_ignore_case_and_whitespace(self):
        s = self._s(rules=r"\buniv\b => university", ignore_case=True)
        assert s.evaluate(_ctx("KYOTO   UNIV", " kyoto University ")).success is True
        raw = self._s(rules="x => y", collapse_whitespace=False)
        assert raw.evaluate(_ctx("a  b", "a b")).success is False

    def test_construction_errors(self):
        with pytest.raises(ValueError, match="rules"):
            self._s()
        with pytest.raises(ValueError, match="第 2 條"):
            self._s(rules=["ok", "(bad"])
        with pytest.raises(ValueError, match="空的"):
            self._s(rules="# only a comment")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. 共通：註冊、參數 meta、NullPolicy、pickle
# ═══════════════════════════════════════════════════════════════════════════════

FACTORIES = {
    "REGEX_EXTRACT_EXACT": lambda **kw: RegexExtractExactStrategy("a", "b", None, pattern=r"\w+", **kw),
    "REGEX_RULE": lambda **kw: RegexRuleStrategy("a", "b", None, **kw),
    "REGEX_NAMED_GROUPS": lambda **kw: RegexNamedGroupsStrategy("a", "b", None, pattern=r"(?P<w>\w+)", **kw),
    "REGEX_NORMALIZED_EXACT": lambda **kw: RegexNormalizedExactStrategy("a", "b", None, rules=r"\s+ => ", **kw),
}


@pytest.mark.parametrize("name", list(FACTORIES))
class TestRegexCommon:
    def test_registered(self, name):
        assert STRATEGY_TABLE[name] is type(FACTORIES[name]())

    def test_param_meta_has_own_keys_then_null_keys(self, name):
        meta = get_strategy_param_meta(name)
        own = list(get_strategy_param_meta(name, include_null_policy=False))
        assert own and list(meta)[: len(own)] == own
        assert {"null_mode", "empty_is_null", "null_like"} <= set(meta)
        for spec in meta.values():
            assert spec["mode"] in ("input", "select") and spec["level"] in ("necessary", "optional")

    def test_null_policy(self, name):
        s = FACTORIES[name]()
        r = s.evaluate(_ctx(NAN, "hello"))
        assert r.success is False and r.score == pytest.approx(-1.0)
        assert s.evaluate(_ctx(None, None)).success is False
        both = FACTORIES[name](null_policy=NullPolicy(mode=NullMode.MATCH_IF_BOTH))
        assert both.evaluate(_ctx(NAN, None)).success is True
        assert FACTORIES[name](strategy_parameters={"empty_is_null": True}).evaluate(_ctx("", " ")).score == pytest.approx(-1.0)

    def test_same_text_matches(self, name):
        assert FACTORIES[name]().evaluate(_ctx("hello", "hello")).success is True

    def test_pickle_roundtrip(self, name):
        s = FACTORIES[name]()
        clone = pickle.loads(pickle.dumps(s))
        assert clone.evaluate(_ctx("hello", "hello")).success is True


def test_adapter_with_gui_style_string_params():
    """GUI 送進來的全部是字串（放在 strategy_parameters）。"""
    a = MatchingStrategyAdapter("REGEX_RULE", None, strategy_parameters={
        "match_mode": "fullmatch", "ignore_case": "True", "regex_timeout": "0.5", "on_invalid": "fail",
    })
    assert a.run("Kyoto University", r"kyoto \w+").success is True
    b = MatchingStrategyAdapter("REGEX_NORMALIZED_EXACT", None, strategy_parameters={
        "rules": "\\bUniv\\b => University\n", "collapse_whitespace": "True",
    })
    assert b.run("Kyoto Univ", "Kyoto  University").success is True
