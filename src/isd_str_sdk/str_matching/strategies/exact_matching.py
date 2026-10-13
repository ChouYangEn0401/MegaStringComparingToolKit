from typing import Any

from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching.null_policy import NullPolicy


class ExactMatchStrategy(Strategy[TwoSeriesComparisonContext]):
    @property
    def IsExactMatch(self) -> bool:
        return True

    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.null_policy = NullPolicy.from_kwargs(kwargs)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = context.row1.get(self.df1_col)
        val2 = context.row2.get(self.df2_col)
        # NOTE (0.4.6): two missing cells no longer count as "equal".
        # None == None / NaN cells used to slip through as a match; the
        # NullPolicy decides that now (FAIL by default, MATCH_IF_BOTH to opt in).
        handled = self.null_policy.intercept(val1, val2)
        if handled is not None:
            return handled
        flag = bool(val1 == val2)  # numpy scalars compare to numpy.bool_; keep a plain bool
        return StrategyResult(success=flag, score=1 if flag else 0)

