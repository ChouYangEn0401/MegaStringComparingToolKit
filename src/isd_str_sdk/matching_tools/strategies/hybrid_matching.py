from typing import List, Any, Type

from legacy.EntireCompareTree.contexts import TwoSeriesComparisonContext

from isd_str_sdk.base.AbstractStrategy import StrategyResult
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.core import (
    StrFunc_Uppercase,
    StrFunc_AscendDictionaryOrder,
    StrFunc_KeepEnglishLetterAndDigits,
    StrFunc_ExcelACTable_UnionLetter_FOREIGN,
    StrFunc_Lowercase,
    StrFunc_ExcelACTable_UnionLetter_ALLOrg,
    StrFunc_ExcelACTable_UnionLetter_STOPWORD,
    StrProcessorsChain,
)
from isd_str_sdk.matching_tools.strategies.exact_matching import ExactMatchStrategy


# ### REFACTOR: AdvancedStrategy ###
# 此狀況下是否應該讓AdvancedStrategy變成 interface 這樣就可以註冊接口了呢？
# 此狀況下是否應該直接設計一個 preprocessed 的空架構，讓人直接註冊現有方法就好，會不會更乾淨簡潔呢？
# 頂多在用 strategy pattern 製作出一些常見的就好了？？
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
        self.chain = StrProcessorsChain(processors or self.DEFAULT_PROCESSORS)

    def _normalization(self, text) -> str:
        return self.chain.run(str(text))

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        val1 = self._normalization(context.row1.get(self.df1_col))
        val2 = self._normalization(context.row2.get(self.df2_col))
        flag = val1 == val2
        return StrategyResult(success=flag, score=1 if flag else 0)
# ### REFACTOR: AdvancedStrategy ###

