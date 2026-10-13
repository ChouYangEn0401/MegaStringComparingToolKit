import re
from typing import Any, List
from abc import ABC, abstractmethod
from isd_py_framework_sdk.helpers.decorators.lifecycle import deprecated

from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching.null_policy import NullPolicy


# --------------------------------------------------------- #
# IN-STRING STRATEGIES                                        #
# --------------------------------------------------------- #

# ### REFACTOR: 如何透過限縮數量，讓IN可以在某數量相同以後 ###
@deprecated("This Function Seems A Little Useless !!")
class InStringStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.null_policy = NullPolicy.from_kwargs(kwargs)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        flag = str(raw2) in str(raw1)
        return StrategyResult(success=flag, score=1 if flag else 0)

class TwoSideInStringStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(
        self, df1: str, df2: str, standard: Any,
        strategy_parameters: dict, **kwargs
    ):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.mode = strategy_parameters.get("strategy_mode", "any")
        self.null_policy = NullPolicy.from_kwargs({"strategy_parameters": strategy_parameters, **kwargs})

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        val1 = str(raw1 or "")
        val2 = str(raw2 or "")

        if self.mode == "a_in_b":
            flag = val1 in val2
        elif self.mode == "b_in_a":
            flag = val2 in val1
        else:  # any
            flag = val1 in val2 or val2 in val1

        return StrategyResult(success=flag, score=1 if flag else 0)

class TwoSideInWith3WordsStringStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(
        self, df1: str, df2: str, standard: int, **kwargs
    ):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.null_policy = NullPolicy.from_kwargs(kwargs)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        val1 = str(raw1 or "")
        val2 = str(raw2 or "")
        flag = (val1 in val2 and len(val1)>=3) or (val2 in val1 and len(val2)>=3)
        return StrategyResult(success=flag, score=1 if flag else 0)
# ### REFACTOR: 如何透過限縮數量，讓IN可以在某數量相同以後 ###


class LCSBaseStrategy(Strategy[TwoSeriesComparisonContext], ABC):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.null_policy = NullPolicy.from_kwargs(kwargs)

    @abstractmethod
    def _tokenize(self, text: str) -> List[str]:
        pass

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1_raw = context.row1.get(self.df1_col)
        val2_raw = context.row2.get(self.df2_col)

        # None / NaN / pd.NA / (optionally) "" are decided by the NullPolicy
        # BEFORE anything is turned into text, so "nan" never reaches the
        # tokenizer. Default policy: either side null -> success=False, score=-1.0
        handled = self.null_policy.intercept(val1_raw, val2_raw)
        if handled is not None:
            return handled

        val1 = NullPolicy.to_text(val1_raw).strip()
        val2 = NullPolicy.to_text(val2_raw).strip()

        try:
            tokens1 = self._tokenize(val1)
            tokens2 = self._tokenize(val2)
            if not isinstance(tokens1, list) or not isinstance(tokens2, list):
                return StrategyResult(success=False, score=-1.0)

            m, n = len(tokens1), len(tokens2)

            # 保持 tokens1 長度較大，空間優化
            if m < n:
                tokens1, tokens2 = tokens2, tokens1
                m, n = n, m

            dp = [[0] * (n + 1) for _ in range(2)]

            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if tokens1[i - 1] == tokens2[j - 1]:
                        dp[i % 2][j] = dp[(i - 1) % 2][j - 1] + 1
                    else:
                        dp[i % 2][j] = max(dp[(i - 1) % 2][j], dp[i % 2][j - 1])

            lcs_length = dp[m % 2][n]
            max_len = max(len(tokens1), len(tokens2))
            similarity = lcs_length / max_len if max_len > 0 else 0.0

            return StrategyResult(success=similarity >= self.standard, score=similarity)

        except Exception as e:
            raise ValueError(f"[LCS ERROR] val1={val1}, val2={val2}, error={str(e)}") from e
class LetterLCSStrategy(LCSBaseStrategy):
    """ Normal LCS That Count Each Letter As Unit """
    def _tokenize(self, text: str) -> List[str]:
        return list(text)
class WordLCSStrategy(LCSBaseStrategy):
    """ Normal LCS That Count Each English-Word As Unit """
    def _tokenize(self, text: str) -> List[str]:
        return [token.strip() for token in re.split(r'[;,，、\s]+', text) if token.strip()]

class JaccardStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.null_policy = NullPolicy.from_kwargs(kwargs)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        val1 = NullPolicy.to_text(raw1).split()
        val2 = NullPolicy.to_text(raw2).split()

        set1 = set(val1)
        set2 = set(val2)

        intersection_len = len(set1.intersection(set2))
        union_len = len(set1.union(set2))

        similarity = intersection_len / union_len if union_len > 0 else 0.0
        return StrategyResult(success=similarity >= self.standard, score=similarity)
