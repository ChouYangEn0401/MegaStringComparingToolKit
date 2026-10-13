from rapidfuzz import fuzz # 替換 fuzzywuzzy 為 rapidfuzz，以獲得顯著的效能提升
from rapidfuzz.distance import JaroWinkler, Levenshtein

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.str_matching.null_policy import NullPolicy


class FuzzyRatioStrategy(Strategy[TwoSeriesComparisonContext]):
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
        val1 = NullPolicy.to_text(raw1)
        val2 = NullPolicy.to_text(raw2)
        # 使用 rapidfuzz 替代 fuzzywuzzy，獲得更高的效能
        # rapidfuzz 的 ratio 函式返回 0-100 的整數，我們將其轉換為 0-1.0 的浮點數
        similarity = fuzz.ratio(val1, val2) / 100.0
        return StrategyResult(success=similarity >= self.standard, score=similarity)


class LevenshteinStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard  # 期望的相似度閾值 (0.0 ~ 1.0)
        self.null_policy = NullPolicy.from_kwargs(kwargs)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        val1 = NullPolicy.to_text(raw1)
        val2 = NullPolicy.to_text(raw2)

        # RapidFuzz 直接提供 normalized_similarity (0.0 ~ 1.0)
        similarity = Levenshtein.normalized_similarity(val1, val2)

        return StrategyResult(success=similarity >= self.standard, score=similarity)


class JaroWinklerStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard  # 期望的相似度閾值 (0.0 ~ 1.0)
        self.null_policy = NullPolicy.from_kwargs(kwargs)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        val1 = NullPolicy.to_text(raw1)
        val2 = NullPolicy.to_text(raw2)

        # 正確的呼叫方式 (0.0 ~ 1.0)
        similarity = JaroWinkler.normalized_similarity(val1, val2)

        return StrategyResult(success=similarity >= self.standard, score=similarity)

