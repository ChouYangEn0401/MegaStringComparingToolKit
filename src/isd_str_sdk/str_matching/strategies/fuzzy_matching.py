from rapidfuzz import fuzz # 替換 fuzzywuzzy 為 rapidfuzz，以獲得顯著的效能提升
from rapidfuzz.distance import JaroWinkler, Levenshtein

from legacy.EntireCompareTree.contexts import TwoSeriesComparisonContext

from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.str_cleaning.StrProcessorsChain import StrProcessorsChain


class FuzzyRatioStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col))
        val2 = str(context.row2.get(self.df2_col))
        # 使用 rapidfuzz 替代 fuzzywuzzy，獲得更高的效能
        # rapidfuzz 的 ratio 函式返回 0-100 的整數，我們將其轉換為 0-1.0 的浮點數
        similarity = fuzz.ratio(val1, val2) / 100.0
        return StrategyResult(success=similarity >= self.standard, score=similarity)
    

class LevenshteinStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard  # 期望的相似度閾值 (0.0 ~ 1.0)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col) or "")
        val2 = str(context.row2.get(self.df2_col) or "")

        # RapidFuzz 直接提供 normalized_similarity (0.0 ~ 1.0)
        similarity = Levenshtein.normalized_similarity(val1, val2)

        return StrategyResult(success=similarity >= self.standard, score=similarity)


class JaroWinklerStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard  # 期望的相似度閾值 (0.0 ~ 1.0)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col) or "")
        val2 = str(context.row2.get(self.df2_col) or "")

        # 正確的呼叫方式 (0.0 ~ 1.0)
        similarity = JaroWinkler.normalized_similarity(val1, val2)

        return StrategyResult(success=similarity >= self.standard, score=similarity)

