from typing import Any

from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from legacy.EntireCompareTree.contexts import TwoSeriesComparisonContext


class ExactMatchStrategy(Strategy[TwoSeriesComparisonContext]):
    @property
    def IsExactMatch(self) -> bool:
        return True

    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = context.row1.get(self.df1_col)
        val2 = context.row2.get(self.df2_col)
        flag = val1 == val2
        return StrategyResult(success=flag, score=1 if flag else 0)

