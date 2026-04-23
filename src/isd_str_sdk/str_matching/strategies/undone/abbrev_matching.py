from enum import Enum, auto, IntEnum
from typing import List, Any, Type
import re

from isd_str_sdk.base import StrProcessorsChain
from isd_str_sdk.matching_tools.strategies.hybrid_matching import PreprocessedExactMatchStrategy
from legacy.EntireCompareTree.contexts import TwoSeriesComparisonContext

from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.str_cleaning import (
    StrFunc_Uppercase,
    StrFunc_AscendDictionaryOrder,
    StrFunc_NormalizeParentheses,
    StrFunc_NormalizeWhitespace,
    StrFunc_KeepEnglishParenthesesAndSpaces,
    StrFunc_KeepEnglishLetterAndDigits,
    StrFunc_ExcelACTable_UnionLetter_FOREIGN,
    StrFunc_Lowercase,
    StrFunc_ExcelACTable_UnionLetter_ALLOrg,
    StrFunc_ExcelACTable_UnionLetter_STOPWORD,
)



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
        self.chain = StrProcessorsChain(processors or self.DEFAULT_PROCESSORS)

    def _normalization(self, text) -> str:
        return self.chain.run(str(text))
# ### REFACTOR: 此策略要先予以更新 ###



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