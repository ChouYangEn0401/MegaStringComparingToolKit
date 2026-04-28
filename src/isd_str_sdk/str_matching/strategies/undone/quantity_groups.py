import pandas as pd
from rapidfuzz import fuzz # 替換 fuzzywuzzy 為 rapidfuzz，以獲得顯著的效能提升
from typing import Any, Dict
from isd_str_sdk.utils.exceptions import MissingParameters
from isd_str_sdk.base.AbstractStrategy import Strategy, AdvancedStrategy, StrategyResult
from isd_str_sdk.core.contexts import (
    TwoSeriesComparisonContext,
    TwoSeriesComparisonContextWithStrategyPars,
)

# from isd_py_framework_sdk.decorators import unfinished, on_dev
# @on_dev
class PreprocessedQuantityBasedLCSInStringStrategy(Strategy[TwoSeriesComparisonContext]):
    """"""
    """
        可能透過幾本清細並排序以後，雙向進行 LCS 去看是否有超過 某數量相同數目
        如果有超過，我們就把他視為 fuzzy 有過？
    """
    def __init__(
        self, df1: str, df2: str, standard: Any,
        strategy_parameters: dict, **kwargs
    ):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.mode = strategy_parameters.get("strategy_mode", "any")
        self.base_count = 4 ## 目前希望大於4

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        ...
    #     val1 = str(context.row1.get(self.df1_col) or "")
    #     val2 = str(context.row2.get(self.df2_col) or "")
    #
    #     if self.mode == "a_in_b":
    #         flag = val1 in val2
    #     elif self.mode == "b_in_a":
    #         flag = val2 in val1
    #     else:  # any
    #         flag = val1 in val2 or val2 in val1
    #
    #     return StrategyResult(success=flag, score=1 if flag else 0)




class NumberJaccardStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: int, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = int(standard)

    def _evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col)).split()
        val2 = str(context.row2.get(self.df2_col)).split()

        set1 = set(val1)
        set2 = set(val2)

        intersection_len = len(set1.intersection(set2))
        union_len = len(set1.union(set2))

        similarity = intersection_len / union_len if union_len > 0 else 0.0
        flag = intersection_len >= self.standard
        return StrategyResult(success=flag, score=similarity)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        return self._evaluate(context)

class FourJaccardRapidFuzzyScoreStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: int, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = int(standard)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col)).split()
        val2 = str(context.row2.get(self.df2_col)).split()

        set1 = set(val1)
        set2 = set(val2)
        intersection_len = len(set1.intersection(set2))

        similarity = fuzz.ratio(val1, val2) / 100.0
        flag = intersection_len >= self.standard
        return StrategyResult(success=flag, score=similarity)

class NewJACCARDStrategy(AdvancedStrategy[TwoSeriesComparisonContextWithStrategyPars]):
    def get_result(self) -> set[str]:
        return self.intersection

    def __init__(self, df1: str, df2: str, standard: float, strategy_parameters, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        # coerce standard to numeric when possible (strategies may expect float/int)
        try:
            self.standard = float(standard)
        except Exception:
            self.standard = standard

        try:
            self.split_segment = strategy_parameters['split_segment']
            self.strategy_mode = strategy_parameters['strategy_mode']
            self.scoring_method = strategy_parameters.get('scoring_method', 'union_base')
            self.extra_debug_print = strategy_parameters.get('extra_debug_print', False)
        except Exception:
            # clearly indicate which params are required
            raise MissingParameters(['split_segment', 'strategy_mode'])

    def get_advanced_settings(self) -> Dict[str, Dict[str, Any]]:
        return {
            'split_segment': {'mode': 'input', 'level': 'necessary'},
            'strategy_mode': {'mode': 'select', 'level': 'necessary', 'options': ['amount_mode', 'score_mode']},
            'scoring_method': {'mode': 'select', 'level': 'optional', 'options': ['union_base', 'set1_base', 'set2_base']},
            'extra_debug_print': {'mode': 'select', 'level': 'optional', 'options': ['False', 'True']},
        }

    def evaluate(self, context: TwoSeriesComparisonContextWithStrategyPars) -> StrategyResult:
        val1 = context.row1.get(self.df1_col)
        val2 = context.row2.get(self.df2_col)

        if val1 == "" or val2 == "" or pd.isna(val1) or pd.isna(val2):
            return StrategyResult(success=False, score=-1.0)

        val1 = str(val1).split(self.split_segment)
        val2 = str(val2).split(self.split_segment)

        set1 = set(val1)
        set2 = set(val2)

        set1_len = len(set1)
        set2_len = len(set2)
        self.intersection = set1.intersection(set2)
        intersection_len = len(self.intersection)
        union_len = len(set1.union(set2))

        if self.extra_debug_print:
            print(self.intersection)

        # amount_mode: require a minimum number of matching tokens
        if self.strategy_mode == 'amount_mode':
            try:
                min_count = int(self.standard)
            except Exception:
                min_count = int(float(self.standard)) if self.standard else 0
            success = intersection_len >= min_count
            return StrategyResult(success=success, score=float(intersection_len))

        # score_mode: compute a similarity ratio according to scoring_method
        elif self.strategy_mode == 'score_mode':
            if self.scoring_method == 'union_base':
                similarity = intersection_len / union_len if union_len > 0 else 0.0
            elif self.scoring_method == 'set1_base':
                similarity = intersection_len / set1_len if set1_len > 0 else 0.0
            elif self.scoring_method == 'set2_base':
                similarity = intersection_len / set2_len if set2_len > 0 else 0.0
            else:
                raise NotImplementedError
            try:
                thresh = float(self.standard)
            except Exception:
                thresh = 0.0
            return StrategyResult(success=similarity >= thresh, score=similarity)

        # unknown mode
        return StrategyResult(success=False, score=-1.0)

