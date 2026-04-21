from abc import ABC, abstractmethod
from enum import Enum, auto, IntEnum
from typing import List, Any, Dict, Type
from rapidfuzz import fuzz # 替換 fuzzywuzzy 為 rapidfuzz，以獲得顯著的效能提升
from rapidfuzz.distance import JaroWinkler, Levenshtein
from sentence_transformers import SentenceTransformer
import numpy as np
import re
import inspect

from src.hyper_framework.decorators_pack import deprecated
from src.lib.multi_condition_clean.EntireCompareTree.ab import Strategy, AdvancedStrategy, StrategyResult, \
    IComparisonContextFamily
from src.lib.multi_condition_clean.EntireCompareTree.contexts import ChildrenValueComparisonContext, TwoSeriesComparisonContext, PRISTreeStructureContext, TwoSeriesComparisonContextWithStrategyPars
from src.lib.processors_strategies.cleaning_module.str_processors import (
    StrFunc_Uppercase,
    StrFunc_AscendDictionaryOrder, StrFunc_NormalizeParentheses, StrFunc_NormalizeWhitespace,
    StrFunc_KeepEnglishParenthesesAndSpaces, StrFunc_KeepEnglishLetterAndDigits,
    StrFunc_ExcelACTable_UnionLetter_FOREIGN, StrFunc_Lowercase, StrFunc_ExcelACTable_UnionLetter_ALLOrg,
    StrFunc_ExcelACTable_UnionLetter_STOPWORD
)
from src.lib.processors_strategies.base.processor_base import StrProcessorBase, StrProcessorChain

# ### REFACTOR: 是否考慮將此 大library 進行拆分，以方便管理？ ###
# ### REFACTOR: 是否考慮將此 大library 進行拆分，以方便管理？ ###
# ### REFACTOR: 是否考慮將此 大library 進行拆分，以方便管理？ ###

class AndStrategy(Strategy[ChildrenValueComparisonContext]):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return all(context.children_results)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        results = [child.evaluate(context.original_context) for child in context.children]
        success = all(r.success for r in results)
        # 你可以用平均分數
        score = sum(r.score or 0 for r in results) / len(results)
        return StrategyResult(success=success, score=score, children=results)

class OrStrategy(Strategy[ChildrenValueComparisonContext]):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return any(context.children_results)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        results = [child.evaluate(context.original_context) for child in context.children]
        success = any(r.success for r in results)
        score = max(r.score or 0 for r in results)
        return StrategyResult(success=success, score=score, children=results)

# ### NOTE: untested !@! ### #
# class NotStrategy(Strategy[ChildrenValueComparisonContext]):
#     def evaluate(self, context):
#         if len(context.children) != 1:
#             raise ValueError("NOT strategy requires exactly one child")
#
#         child = context.children[0].evaluate(context.original_context)
#
#         return StrategyResult(
#             success = not child.success,
#             score = 1 - (child.score or 0),  # optional
#             children = [child]
#         )

class NotOrStrategy(OrStrategy):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # """ 先執行 Or 運算以後 翻轉結果 """
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return not super().run(context)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        base_result = super().evaluate(context)
        return StrategyResult(
            success = not base_result.success,  ## 其餘不變，目前只翻轉結果
            score = base_result.score,
            children = base_result.children,
        )

class NotAndStrategy(AndStrategy):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # """ 先執行 And 運算以後 翻轉結果 """
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return not super().run(context)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        base_result = super().evaluate(context)
        return StrategyResult(
            success = not base_result.success,  ## 其餘不變，目前只翻轉結果
            score = base_result.score,
            children = base_result.children,
        )


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

# ### REFACTOR: 此策略要先予以更新 ###
## 縮寫算法要改成
##  -> 小心版 [視為完全比對]
##  -> 危險版 [視為模糊比對]
class AbbrevExactMatchStrategy(Strategy[TwoSeriesComparisonContext]):
    """
    Abbreviation-aware exact-ish matching strategy
    """

    # @property
    # def IsExactMatch(self) -> bool:
    #     return True
    # ### TODO: 要有簡單基本型(搭配processed) -> True ###
    # ### TODO: 搭配進階型(搭配processed) -> False ###

    # =========================================================
    # Enums (全部集中在 class 內)
    # =========================================================
    class Signal(Enum):
        EXACT_NAME = auto()          # name == name
        SAME_ABBR = auto()           # abbr == abbr
        ABBR_IN_PAREN = auto()       # MIT vs XXX (MIT)
        NAME_EQ_ABBR = auto()        # NTU vs National Taiwan University
    class Tier(IntEnum):
        STRICT = 0   # 幾乎零風險
        SAFE = 1
        MEDIUM = 2
        RISKY = 3

    # =========================================================
    # Signal → Tier mapping（你的「誰好誰壞」標準）
    # =========================================================

    SIGNAL_TIER_MAP = {
        Signal.EXACT_NAME: Tier.STRICT,
        Signal.ABBR_IN_PAREN: Tier.SAFE,
        Signal.NAME_EQ_ABBR: Tier.MEDIUM,
        Signal.SAME_ABBR: Tier.RISKY,
    }

    STOPWORDS = {"of", "the", "at", "in", "and", "de", "with", "&", "and"}

    # =========================================================
    # Init
    # =========================================================

    def __init__(
        self,
        df1: str,
        df2: str,
        standard: Any = None,
        strategy_parameters: dict | None = None,
        **kwargs
    ):
        self.df1_col = df1
        self.df2_col = df2

        # standard = 允許的最大 tier（預設 SAFE）
        self.allowed_tier = (
            self.Tier(standard)
            if standard is not None
            else self.Tier.SAFE
        )

        strategy_parameters = strategy_parameters or {}

        # 可選：限制允許的 signal（不給就全開）
        enabled = strategy_parameters.get("enabled_signals")
        self.enabled_signals = (
            {self.Signal[s] for s in enabled}
            if enabled
            else set(self.Signal)
        )

    # =========================================================
    # Normalization
    # =========================================================

    def _normalization(self, text: str) -> str:
        return text.strip()

    def _normalize(self, text: str):
        if not text:
            return "", ""

        text = self._normalization(text)

        # 拆 name + (abbr)
        match = re.match(r"^(.+?)(?:\s*\((.*?)\))?$", text)
        if match:
            name = match.group(1).strip().lower()
            abbr = (match.group(2) or "").strip().lower()
        else:
            name = text.lower()
            abbr = ""

        abbr = abbr.replace(".", "")  # N.T.U. → ntu
        return name, abbr

    # =========================================================
    # Signal detection helpers
    # =========================================================

    def _collect_signals(self, name1, abbr1, name2, abbr2) -> set:
        signals = set()

        # 1) 完整名稱相同
        if name1 and name1 == name2:
            signals.add(self.Signal.EXACT_NAME)

        # 2) 縮寫相同
        if abbr1 and abbr1 == abbr2:
            signals.add(self.Signal.SAME_ABBR)

        # 3) 縮寫出現在括號
        # MIT vs Massachusetts Institute of Technology (MIT)
        if abbr2 and name1 == abbr2:
            signals.add(self.Signal.ABBR_IN_PAREN)
        if abbr1 and name2 == abbr1:
            signals.add(self.Signal.ABBR_IN_PAREN)

        # 4) 全名 vs 縮寫（雙向）
        if abbr1 and name2 == abbr1:
            signals.add(self.Signal.NAME_EQ_ABBR)
        if abbr2 and name1 == abbr2:
            signals.add(self.Signal.NAME_EQ_ABBR)

        return signals & self.enabled_signals

    # =========================================================
    # Evaluate
    # =========================================================

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = context.row1.get(self.df1_col)
        val2 = context.row2.get(self.df2_col)

        name1, abbr1 = self._normalize(val1)
        name2, abbr2 = self._normalize(val2)

        signals = self._collect_signals(name1, abbr1, name2, abbr2)

        if not signals:
            return StrategyResult(success=False, score=0)

        # 聚合：取「最好的一個理由」
        final_tier = min(self.SIGNAL_TIER_MAP[s] for s in signals)

        success = final_tier <= self.allowed_tier

        return StrategyResult(
            success=success,
            score=1 if success else 0,
            # metadata={
            #     "signals": [s.name for s in signals],
            #     "final_tier": final_tier.name,
            #     "allowed_tier": self.allowed_tier.name,
            # }
        )

class PreprocessedAbbrevExactStrategy(AbbrevExactMatchStrategy):
    @property
    def IsExactMatch(self) -> bool:
        return False

    DEFAULT_PROCESSORS = [
        StrFunc_ExcelACTable_UnionLetter_STOPWORD,     # 停止詞統一
        StrFunc_ExcelACTable_UnionLetter_FOREIGN,      # 國外符號轉換
        StrFunc_Lowercase,
        StrFunc_ExcelACTable_UnionLetter_ALLOrg,       # 機構詞轉換
        StrFunc_NormalizeParentheses,                  # 保留括號語意（必須）
        StrFunc_NormalizeWhitespace,                   # 空白統一
        StrFunc_KeepEnglishParenthesesAndSpaces,       # 保留英文 + 空白 + 括號
        StrFunc_Uppercase,                             # 大寫一致化
    ]

    def __init__(self, df1, df2, standard: int = 1, processors: List[Type[StrProcessorBase]] = None, **kwargs):
        super().__init__(df1, df2, standard)
        self.chain = StrProcessorChain(processors or self.DEFAULT_PROCESSORS)

    def _normalization(self, text) -> str:
        return self.chain.run(str(text))
# ### REFACTOR: 此策略要先予以更新 ###

class PreprocessedExactMatchStrategy(ExactMatchStrategy):
    DEFAULT_PROCESSORS = [
        StrFunc_ExcelACTable_UnionLetter_STOPWORD,     # 停止詞統一
        StrFunc_ExcelACTable_UnionLetter_FOREIGN,      # 國外符號轉換
        StrFunc_Lowercase,
        StrFunc_ExcelACTable_UnionLetter_ALLOrg,       # 機構詞轉換
        StrFunc_KeepEnglishLetterAndDigits,            # 保留英文數
        StrFunc_Uppercase,                             # 大寫一致化
        StrFunc_AscendDictionaryOrder,                 # 字點順序排列
    ]

    def __init__(self, df1: str, df2: str, standard: Any, processors: List[Type[StrProcessorBase]] = None, **kwargs):
        super().__init__(df1, df2, standard)
        self.chain = StrProcessorChain(processors or self.DEFAULT_PROCESSORS)

    def _normalization(self, text) -> str:
        return self.chain.run(str(text))

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = self._normalization(context.row1.get(self.df1_col))
        val2 = self._normalization(context.row2.get(self.df2_col))
        flag = val1 == val2
        return StrategyResult(success=flag, score=1 if flag else 0)

# ### TODO: 未完成 ###
## 我這邊希望可以加入一個"刪掉沒有意義詞會的完全比對"，例如冠詞停滯詞等等，全部去除，然後進行完全比對吧？
class PreprocessedExtractionExactMatchStrategy(PreprocessedExactMatchStrategy):
    DEFAULT_PROCESSORS = [
        StrFunc_ExcelACTable_UnionLetter_STOPWORD,     # 停止詞統一
        StrFunc_ExcelACTable_UnionLetter_FOREIGN,      # 國外符號轉換
        StrFunc_Lowercase,
        StrFunc_ExcelACTable_UnionLetter_ALLOrg,       # 機構詞轉換
        StrFunc_KeepEnglishLetterAndDigits,            # 保留英文數
        StrFunc_Uppercase,                             # 大寫一致化
        StrFunc_AscendDictionaryOrder,                 # 字點順序排列
    ]
    def __init__(self, df1: str, df2: str, standard: Any, processors: List[Type[StrProcessorBase]] = None, **kwargs):
        super().__init__(df1, df2, standard, processors or self.DEFAULT_PROCESSORS)
    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        ...
        # val1 = self._normalization(context.row1.get(self.df1_col))
        # val2 = self._normalization(context.row2.get(self.df2_col))
        # flag = val1 == val2
        # return StrategyResult(success=flag, score=1 if flag else 0)
# ### TODO: 未完成 ###

@deprecated("This Function Seems A Little Useless !!")
class InStringStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = context.row1.get(self.df1_col)
        val2 = context.row2.get(self.df2_col)
        flag = str(val2) in str(val1)
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

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col) or "")
        val2 = str(context.row2.get(self.df2_col) or "")

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

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col) or "")
        val2 = str(context.row2.get(self.df2_col) or "")
        flag = (val1 in val2 and len(val1)>=3) or (val2 in val1 and len(val2)>=3)
        return StrategyResult(success=flag, score=1 if flag else 0)

# ### REFACTOR: 如何透過限縮數量，讓IN可以在某數量相同以後 ###
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
# ### REFACTOR: 如何透過限縮數量，讓IN可以在某數量相同以後 ###

# --- 基於字串距離的模糊比對 ---
# ### TODO: complete all this with preprocessed strategy ###
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

class PreprocessedFuzzyRatioStrategy(Strategy[TwoSeriesComparisonContext]):
    DEFAULT_PROCESSORS = []
    def __init__(self, df1: str, df2: str, standard: Any, processors: List[Type[StrProcessorBase]] = None, **kwargs):
        super().__init__(df1, df2, standard)
        self.chain = StrProcessorChain(processors or self.DEFAULT_PROCESSORS)
    def _normalization(self, text) -> str:
        return self.chain.run(str(text))
    def evaluate(self, context: IComparisonContextFamily) -> StrategyResult:
        ...

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

class LCSBaseStrategy(Strategy[TwoSeriesComparisonContext], ABC):
    def __init__(self, df1: str, df2: str, standard: float, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard

    @abstractmethod
    def _tokenize(self, text: str) -> List[str]:
        pass

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1_raw = context.row1.get(self.df1_col)
        val2_raw = context.row2.get(self.df2_col)

        if val2_raw is None or val1_raw is None:
            return StrategyResult(success=False, score=-1.0)

        val1 = str(val1_raw).strip() if val1_raw is not None else ""
        val2 = str(val2_raw).strip() if val2_raw is not None else ""

        try:
            tokens1 = self._tokenize(val1)
            tokens2 = self._tokenize(val2)

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

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col)).split()
        val2 = str(context.row2.get(self.df2_col)).split()

        set1 = set(val1)
        set2 = set(val2)

        intersection_len = len(set1.intersection(set2))
        union_len = len(set1.union(set2))

        similarity = intersection_len / union_len if union_len > 0 else 0.0
        return StrategyResult(success=similarity >= self.standard, score=similarity)

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

class MissingParameters(Exception):
    def __init__(self, options: List[str], message=None):
        if message is None:
            str_ = ', '.join([f"`{option}`" for option in options])
            message = f"Missing Important Parameters {str_} !!"
        super().__init__(message)

    def __str__(self):
        """
        提供更詳細的例外訊息，包含發生錯誤的類別。
        """
        # 嘗試找出呼叫此例外的類別
        frame = inspect.currentframe().f_back
        while frame:
            if 'self' in frame.f_locals:
                calling_class = frame.f_locals['self'].__class__.__name__
                return f"錯誤：在類別 '{calling_class}' 中發生 MissingParameters。\n{super().__str__()}"
            frame = frame.f_back
        return super().__str__()

class NewStrategy(Strategy[TwoSeriesComparisonContextWithStrategyPars]):
    def __init__(self, df1: str, df2: str, standard: float, strategy_parameters, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        try:
            self.keyword = strategy_parameters['keyword']
        except:
            ## will just broken if not provided with
            raise MissingParameters(['keyword'])

class NewJACCARDStrategy(AdvancedStrategy[TwoSeriesComparisonContextWithStrategyPars]):
    def get_result(self) -> set[str]:
        return self.intersection

    def __init__(self, df1: str, df2: str, standard: float, strategy_parameters, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        try:
            self.split_segment = strategy_parameters['split_segment']
            self.strategy_mode = strategy_parameters['strategy_mode']
            self.scoring_method = strategy_parameters.get('scoring_method', 'union_base')
            self.extra_debug_print = strategy_parameters.get('extra_debug_print', False)
        except:
            ## will just broken if not provided with
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
        set2_len = len(set1)
        self.intersection = set1.intersection(set2)
        intersection_len = len(self.intersection)
        union_len = len(set1.union(set2))

        if self.extra_debug_print:
            print(self.intersection)

        if self.strategy_mode == 'amount_mode':
            return intersection_len >= self.standard
        elif self.strategy_mode == 'score_mode':
            if self.strategy_mode == 'union_base':
                similarity = intersection_len / union_len if union_len > 0 else 0.0
            elif self.strategy_mode == 'set1_base':
                similarity = intersection_len / set1_len if set1_len > 0 else 0.0
            elif self.strategy_mode == 'set2_base':
                similarity = intersection_len / set2_len if set2_len > 0 else 0.0
            else:
                raise NotImplementedError
            return StrategyResult(success=similarity >= self.standard, score=similarity)
        raise NotImplementedError
        return StrategyResult(success=False, score=-1.0)
# ### TODO: complete all this with preprocessed strategy ###

# --- 基於 AI 模型的語義比對 ---
class EmbeddingSimilarityStrategy(Strategy[TwoSeriesComparisonContext]):
    def __init__(self, df1: str, df2: str, standard: float, model_name: str = 'all-MiniLM-L6-v2', **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard

        # 使用一個預訓練的輕量級模型
        self.model = SentenceTransformer(model_name)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = str(context.row1.get(self.df1_col))
        val2 = str(context.row2.get(self.df2_col))

        if not val1 or not val2:
            return StrategyResult(success=False, score=-1.0)

        # 將字串轉換為 embeddings (向量)
        embeddings = self.model.encode([val1, val2])

        # 計算餘弦相似度
        similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))

        return StrategyResult(success=similarity >= self.standard, score=similarity)

class PRISTreeWalkingStrategy(Strategy[PRISTreeStructureContext]):
    def __init__(self, df1: int, **kwargs): #, df2_ac_col: str, df2_constraint_col: str, **kwargs):
        self.df1_col = df1

    def evaluate(self, context: PRISTreeStructureContext):
        """
            這個 Strategy 不參與 evaluate。只是被要求實作，但不應被呼叫。
        """
        raise NotImplementedError("PRISTreeWalkingStrategy does not support evaluate()")

    def run(self, context: PRISTreeStructureContext) -> bool:
        """
            最高層入口：走策略樹，回傳 boolean（老接口）
        """
        # print(f"@@@@, df[{self.df1_col}] = {context.source_row.get(self.df1_col)}")
        # print(f"@@@@, tree[cur].AC = {context.root_node.get('right')}")
        # print(f"@@@@, tree[cur].CONSTRAINTS = {context.root_node.get('left')}")
        context.root_node.reset_results()
        res = context.root_node.run_strategy_and_get_result(context.source_row.get(self.df1_col))
        # print("FINAL:", res)
        return res


# ### mvp ### #
# ### REFACTOR: mvp simple one, we may need a much more stable and clean ###
STRATEGY_TABLE = {
    "AndStrategy": AndStrategy,
    "OrStrategy": OrStrategy,
    # "NotStrategy": NotStrategy,
    "NotOrStrategy": NotOrStrategy,
    "NotAndStrategy": NotAndStrategy,
    "ExactMatchStrategy": ExactMatchStrategy,
    "AbbrevExactMatchStrategy": AbbrevExactMatchStrategy,
    "PreprocessedAbbrevExactStrategy": PreprocessedAbbrevExactStrategy,
    "PreprocessedExactMatchStrategy": PreprocessedExactMatchStrategy,
    "PreprocessedExtractionExactMatchStrategy": PreprocessedExtractionExactMatchStrategy,
    "InStringStrategy": InStringStrategy,
    "TwoSideInWith3WordsStringStrategy": TwoSideInWith3WordsStringStrategy,
    "TwoSideInStringStrategy": TwoSideInStringStrategy,
    "PreprocessedQuantityBasedLCSInStringStrategy": PreprocessedQuantityBasedLCSInStringStrategy,
    "FuzzyRatioStrategy": FuzzyRatioStrategy,
    "PreprocessedFuzzyRatioStrategy": PreprocessedFuzzyRatioStrategy,
    "JaroWinklerStrategy": JaroWinklerStrategy,
    "LevenshteinStrategy": LevenshteinStrategy,
    "LCSBaseStrategy": LCSBaseStrategy,
    "LetterLCSStrategy": LetterLCSStrategy,
    "WordLCSStrategy": WordLCSStrategy,
    "JaccardStrategy": JaccardStrategy,
    "NewStrategy": NewStrategy,
    "NewJACCARDStrategy": NewJACCARDStrategy,
    "NumberJaccardStrategy": NumberJaccardStrategy,
    "FourJaccardRapidFuzzyScoreStrategy": FourJaccardRapidFuzzyScoreStrategy,
    "EmbeddingSimilarityStrategy": EmbeddingSimilarityStrategy,
    "PRISTreeWalkingStrategy": PRISTreeWalkingStrategy,
}

class MatchingStrategyAdapter:
    def __init__(self, strategy_name: str, standard: float):
        self.strategy = STRATEGY_TABLE[strategy_name]("str1", "str2", standard)

    def run(
            self,
            ## Public Easy API
            str1: str, str2: str,
            ## Hidden-able Advanced API Settings
            split_segment: str = " ； ", strategy_mode: str = "amount_mode", extra_debug_print: bool = False,
    ):
        assert type(str1) == str, "`str1` Is Not String Type !!"
        assert type(str2) == str, "`str2` Is Not String Type !!"

        import pandas as pd

        # ctx = TwoSeriesComparisonContextWithStrategyPars(
        ctx = TwoSeriesComparisonContext(
            row1=pd.Series({"str1": str1}),
            row2=pd.Series({"str2": str2}),
            # stra_pars={
            #     "split_segment": split_segment,
            #     "strategy_mode": strategy_mode,
            #     "extra_debug_print": extra_debug_print,
            # },
        )

        result = self.strategy.evaluate(ctx)
        return result
# ### REFACTOR: mvp simple one, we may need a much more stable and clean ###


if __name__ == "__main__":
    """
        我們會需要一個api接口來處理這個問題，統一函數的呼叫，也方便其他人使用
        *** 急 ***
        *** 急 ***
        *** 急 ***
    """
    import pandas as pd

    while True:
        ctx = TwoSeriesComparisonContextWithStrategyPars(
            row1=pd.Series({'name': input('c_str1--->')+' ； '+input('o_str1--->')}),
            row2=pd.Series({'name': input('c_str2--->')+' ； '+input('o_str2--->')}),
            stra_pars={"split_segment": " ； ", "strategy_mode": "amount_mode", "extra_debug_print": True},
        )

        strategy = NewJACCARDStrategy(df1='name', df2='name', standard=1, strategy_parameters=ctx.stra_pars)
        print(strategy.run(ctx), '\n')

