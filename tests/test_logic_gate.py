"""
Tests for logic-gate strategies (0.4.7, B-2).

背景：0.4.6 以前 AndStrategy / OrStrategy 的 evaluate() 讀 context.children 與
context.original_context，但 ChildrenValueComparisonContext 只有 children_results，
任何 AND / OR 節點一執行就 AttributeError（NotAND / NotOR 繼承它們，一樣壞）。
下游（ACA / pyDMS）各自用 sdk_compat.py 的 Fixed*Strategy 繞過；這組測試釘住
修好之後的語意，並逐一跟那份修正版的算法（下面 _REFERENCE）對照。
"""
import itertools

import pandas as pd
import pytest

from isd_str_sdk.base.AbstractStrategy import StrategyResult
from isd_str_sdk.core.contexts import ChildrenValueComparisonContext, TwoSeriesComparisonContext
from isd_str_sdk.str_matching import STRATEGY_TABLE
from isd_str_sdk.str_matching.strategies.exact_matching import ExactMatchStrategy
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy
from isd_str_sdk.str_matching.strategies.logic_gate import (
    AndStrategy,
    NotAndStrategy,
    NotOrStrategy,
    OrStrategy,
)


def _gate_ctx(values) -> ChildrenValueComparisonContext:
    return ChildrenValueComparisonContext(children_results=list(values))


# 下游 sdk_compat.py（Fixed*Strategy）的算法，抄成純函式當對照組：(success, score)
def _ref_and(v):
    return all(v), (sum(v) / len(v) if v else 0.0)


def _ref_or(v):
    return any(v), max((1.0 if x else 0.0 for x in v), default=0.0)


_REFERENCE = {
    "AND": (AndStrategy, _ref_and, False),
    "OR": (OrStrategy, _ref_or, False),
    "NotAND": (NotAndStrategy, _ref_and, True),
    "NotOR": (NotOrStrategy, _ref_or, True),
}

# 0～3 個子結果的所有布林組合
_ALL_COMBOS = [list(c) for n in range(4) for c in itertools.product([True, False], repeat=n)]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. 不再 AttributeError（B-2 本體）
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoAttributeError:
    @pytest.mark.parametrize("cls", [AndStrategy, OrStrategy, NotAndStrategy, NotOrStrategy])
    def test_evaluate_reads_only_children_results(self, cls):
        r = cls().evaluate(_gate_ctx([True, False]))
        assert isinstance(r, StrategyResult)
        assert isinstance(r.success, bool)

    @pytest.mark.parametrize("key", ["AND", "OR", "NotAND", "NotOR"])
    def test_strategy_table_gates_construct_without_args_and_run(self, key):
        # ACA / pyDMS 的樹執行器是這樣用的：STRATEGY_TABLE[operator]()
        assert STRATEGY_TABLE[key]().run(_gate_ctx([True])) in (True, False)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. 正反例
# ═══════════════════════════════════════════════════════════════════════════════

class TestAndStrategy:
    def test_all_true_succeeds(self):
        r = AndStrategy().evaluate(_gate_ctx([True, True, True]))
        assert r.success is True
        assert r.score == 1.0

    def test_one_false_fails(self):
        r = AndStrategy().evaluate(_gate_ctx([True, False, True]))
        assert r.success is False
        assert r.score == pytest.approx(2 / 3)

    def test_all_false_fails_with_zero_score(self):
        r = AndStrategy().evaluate(_gate_ctx([False, False]))
        assert r.success is False
        assert r.score == 0.0

    def test_empty_is_vacuously_true_with_zero_score(self):
        # 與下游修正版相同：all([]) 為 True，分數 0.0（不除以零）
        r = AndStrategy().evaluate(_gate_ctx([]))
        assert r.success is True
        assert r.score == 0.0


class TestOrStrategy:
    def test_any_true_succeeds(self):
        r = OrStrategy().evaluate(_gate_ctx([False, True, False]))
        assert r.success is True
        assert r.score == 1.0

    def test_all_false_fails(self):
        r = OrStrategy().evaluate(_gate_ctx([False, False]))
        assert r.success is False
        assert r.score == 0.0

    def test_empty_fails_with_zero_score(self):
        r = OrStrategy().evaluate(_gate_ctx([]))
        assert r.success is False
        assert r.score == 0.0


class TestNotGates:
    def test_not_and_flips_success_keeps_score(self):
        r = NotAndStrategy().evaluate(_gate_ctx([True, False]))
        assert r.success is True
        assert r.score == 0.5

    def test_not_and_all_true_fails(self):
        assert NotAndStrategy().run(_gate_ctx([True, True])) is False

    def test_not_or_all_false_succeeds(self):
        r = NotOrStrategy().evaluate(_gate_ctx([False, False]))
        assert r.success is True
        assert r.score == 0.0

    def test_not_or_any_true_fails(self):
        r = NotOrStrategy().evaluate(_gate_ctx([False, True]))
        assert r.success is False
        assert r.score == 1.0


class TestChildResultShapes:
    def test_accepts_strategy_results(self):
        kids = [StrategyResult(success=True, score=0.9), StrategyResult(success=False, score=0.4)]
        assert AndStrategy().run(_gate_ctx(kids)) is False
        assert OrStrategy().run(_gate_ctx(kids)) is True

    def test_strategy_result_score_does_not_leak_into_gate_score(self):
        # 閘的分數只看布林（與下游修正版一致），不是子結果分數的平均
        kids = [StrategyResult(success=True, score=0.9), StrategyResult(success=True, score=0.1)]
        assert AndStrategy().evaluate(_gate_ctx(kids)).score == 1.0

    def test_mixed_bool_and_strategy_result(self):
        kids = [True, StrategyResult(success=False, score=0.0)]
        assert AndStrategy().run(_gate_ctx(kids)) is False
        assert OrStrategy().run(_gate_ctx(kids)) is True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. 跟下游 sdk_compat.py 修正版逐一對照
# ═══════════════════════════════════════════════════════════════════════════════

class TestParityWithDownstreamShim:
    @pytest.mark.parametrize("key", list(_REFERENCE))
    @pytest.mark.parametrize("values", _ALL_COMBOS, ids=lambda v: "".join("T" if x else "F" for x in v) or "empty")
    def test_same_success_score_children(self, key, values):
        cls, ref, negate = _REFERENCE[key]
        r = cls().evaluate(_gate_ctx(values))
        exp_success, exp_score = ref(values)
        if negate:
            exp_success = not exp_success
        assert r.success is exp_success
        assert r.score == exp_score
        assert r.children is None


# ═══════════════════════════════════════════════════════════════════════════════
# 4. 小型樹：葉節點先跑、結果交給閘
# ═══════════════════════════════════════════════════════════════════════════════

class TestTinyTree:
    @staticmethod
    def _leaves(a, b):
        ctx = TwoSeriesComparisonContext(row1=pd.Series({"a": a}), row2=pd.Series({"b": b}))
        exact = ExactMatchStrategy("a", "b", standard=None).evaluate(ctx)
        fuzzy = FuzzyRatioStrategy("a", "b", standard=0.8).evaluate(ctx)
        return [exact, fuzzy]

    def test_and_of_exact_and_fuzzy(self):
        assert AndStrategy().run(_gate_ctx(self._leaves("Taipei", "Taipei"))) is True
        assert AndStrategy().run(_gate_ctx(self._leaves("Taipei", "Taipeii"))) is False

    def test_or_of_exact_and_fuzzy(self):
        assert OrStrategy().run(_gate_ctx(self._leaves("Taipei", "Taipeii"))) is True
        assert OrStrategy().run(_gate_ctx(self._leaves("Taipei", "Kaohsiung"))) is False
