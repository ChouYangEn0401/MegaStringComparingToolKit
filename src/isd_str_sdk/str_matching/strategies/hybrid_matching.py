import re
from typing import Any, Dict, FrozenSet, Iterable, List, Tuple, Type

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.base.AbstractStrategy import StrategyResult
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.str_cleaning import (
    StrFunc_Uppercase,
    StrFunc_AscendDictionaryOrder,
    StrFunc_KeepEnglishLetterAndDigits,
    StrFunc_ExcelACTable_UnionLetter_FOREIGN,
    StrFunc_Lowercase,
    StrFunc_ExcelACTable_UnionLetter_ALLOrg,
    StrFunc_ExcelACTable_UnionLetter_STOPWORD,
)
from isd_str_sdk.str_matching.strategies.exact_matching import ExactMatchStrategy
from isd_str_sdk.str_matching.null_policy import NullMode


# ### REFACTOR: AdvancedStrategy ###
# 此狀況下是否應該讓AdvancedStrategy變成 interface 這樣就可以註冊接口了呢？
# 此狀況下是否應該直接設計一個 preprocessed 的空架構，讓人直接註冊現有方法就好，會不會更乾淨簡潔呢？
# 頂多在用 strategy pattern 製作出一些常見的就好了？？
class PreprocessedExactMatchStrategy(ExactMatchStrategy):
    """
    正規化 pipeline（``DEFAULT_PROCESSORS``）之後完全比對。

    注意：第 7 步 ``StrFunc_AscendDictionaryOrder`` 因為第 5 步
    ``StrFunc_KeepEnglishLetterAndDigits`` 已經把空白拿掉、整串只剩一個詞，**永遠不生效**——
    所以這一款是「空格不分、詞序要一樣」。要空格與詞序都不分，請用
    ``SpacingAndOrderFreeExactStrategy``（0.4.9，``"SPACING_ORDER_FREE_EXACT"``）；
    這一款的行為刻意不改（下游的比對階梯逐格守著它的產出）。
    """
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
        super().__init__(df1, df2, standard, **kwargs)  # kwargs carries null_policy / strategy_parameters
        self.chain = StrProcessorsChain(processors or self.DEFAULT_PROCESSORS)

    def _normalization(self, text) -> str:
        return self.chain.run(str(text))

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        val1 = self._normalization(raw1)
        val2 = self._normalization(raw2)
        flag = val1 == val2
        return StrategyResult(success=flag, score=1 if flag else 0)
# ### REFACTOR: AdvancedStrategy ###



class SpacingAndOrderFreeExactStrategy(ExactMatchStrategy):
    """
    空格與詞序都不分的完全比對（0.4.9，``"SPACING_ORDER_FREE_EXACT"``）。

    ``PreprocessedExactMatchStrategy`` 是「空格不分、詞序要一樣」；這一款兩件事都做到，
    做法是 **暴力列舉空格**：

    1. 前處理照 ``PreprocessedExactMatchStrategy`` 的前四步（停止詞、國外符號、小寫、機構詞），
       再以空白切成單詞、每個單詞只留英文字母與數字、轉大寫 → ``w1 w2 … wn``（n−1 個空隙）。
       只剩符號的單詞直接丟掉。
    2. 每個空隙「留或拿掉」共 2^(n−1) 種組合；拿掉的空隙把兩邊的詞黏起來。
    3. 每一種組合 → 照字母排序 → 用空白接起來 ＝ 一個「代表字串」。一個名字得到一組代表字串。
    4. 兩個名字只要有 **任何一個** 代表字串相同就算比中（``success=True, score=1``），否則 ``score=0``。

    例：``Tsing Hua University`` 有一種組合是 ``TSINGHUA｜UNIVERSITY``，跟 ``Tsinghua University``
    相同 → 比中；``National Taiwan University`` / ``Taiwan National University`` 全部空隙都留著、
    排序後都是 ``NATIONAL TAIWAN UNIVERSITY`` → 比中。

    **超集保證**：「空隙全部拿掉」那一組就等於 ``PreprocessedExactMatchStrategy`` 的正規化結果，
    所以它比得中的，這一款一定也比得中（只會多、不會少）。兩邊都正規化成空字串
    （例如整串都是中文）也一樣算比中——這是為了守住超集，跟 ``PREPROCESSED_EXACT`` 相同。

    **上限**：空隙數超過 ``max_gaps``（預設 12，即最多 4096 種組合）的名字，只用兩種代表字串：
    「全部拿掉」與「全部留著＋排序」。所以超長的名字仍保有超集性質與詞序不分，
    但「部分空格不同」不保證比得中。

    **批次**：``batch_match(left, right)`` 用反查表（代表字串 → 哪些名字）直接拿候選，
    不必 N×M 兩兩比，結果跟逐對 ``evaluate()`` 逐格相同。每個名字的代表字串會快取。

    參數（keyword 或 ``strategy_parameters``）
    ------------------------------------------
    max_gaps : int, 預設 12
        空隙數上限，超過就只用兩種代表字串。
    pre_processors : list[type], 選填
        取代前四步的清理流程（預設 ``PRE_PROCESSORS``）。

    空值照 ``NullPolicy``（預設任一側 null → ``success=False, score=-1.0``）。
    """

    PRE_PROCESSORS = list(PreprocessedExactMatchStrategy.DEFAULT_PROCESSORS[:4])
    DEFAULT_MAX_GAPS = 12
    _CACHE_LIMIT = 200_000

    def __init__(self, df1: str, df2: str, standard: Any, pre_processors: List[Type[StrProcessorBase]] = None, **kwargs):
        from isd_str_sdk.str_matching.strategies._params import get_param, to_int

        super().__init__(df1, df2, standard, **kwargs)
        self.max_gaps = to_int(get_param(kwargs, "max_gaps", self.DEFAULT_MAX_GAPS),
                               "max_gaps", type(self).__name__, minimum=0)
        self.pre_chain = StrProcessorsChain(pre_processors or self.PRE_PROCESSORS)
        self._cache: dict = {}

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_cache"] = {}  # 快取不跟著 pickle（進程池送出去時不帶一大包）
        return state

    # ── 代表字串 ──────────────────────────────────────────────────────────
    def tokens(self, text: Any) -> List[str]:
        """前處理後的單詞（大寫、只剩英數）。"""
        cleaned = self.pre_chain.run(str(text))
        words = ("".join(_ALNUM.findall(chunk)) for chunk in cleaned.split())
        return [w.upper() for w in words if w]

    def representatives(self, text: Any) -> FrozenSet[str]:
        """一個名字的所有代表字串（有快取）。"""
        key = str(text)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        reps = _representatives(self.tokens(key), self.max_gaps)
        if len(self._cache) >= self._CACHE_LIMIT:
            self._cache.clear()
        self._cache[key] = reps
        return reps

    # ── 逐對 ──────────────────────────────────────────────────────────────
    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled
        flag = not self.representatives(raw1).isdisjoint(self.representatives(raw2))
        return StrategyResult(success=flag, score=1 if flag else 0)

    # ── 批次（反查表 / group）────────────────────────────────────────────
    def build_index(self, values: Iterable[Any]) -> Dict[str, List[int]]:
        """代表字串 → 擁有它的位置（0 起算）。null（依 NullPolicy）不進表。"""
        index: Dict[str, List[int]] = {}
        as_text = self.null_policy.mode is NullMode.AS_TEXT
        for pos, value in enumerate(values):
            if not as_text and self.null_policy.is_null(value):
                continue
            for rep in self.representatives(value):
                index.setdefault(rep, []).append(pos)
        return index

    def batch_match(self, left: Iterable[Any], right: Iterable[Any]) -> List[Tuple[int, int]]:
        """
        回傳所有比中的 ``(左邊位置, 右邊位置)``（位置從 0 起算，依序排好）。

        跟對每一格跑 ``evaluate()`` 取 ``success=True`` 的結果逐格相同，但只看共用代表字串的候選，
        不做 N×M。null 照 NullPolicy：``match_if_both`` 時兩邊都 null 的也算比中。
        """
        left = list(left)
        right = list(right)
        index = self.build_index(right)
        as_text = self.null_policy.mode is NullMode.AS_TEXT
        right_nulls = [] if as_text else [j for j, v in enumerate(right) if self.null_policy.is_null(v)]
        pairs = set()
        for i, value in enumerate(left):
            if not as_text and self.null_policy.is_null(value):
                if self.null_policy.mode is NullMode.MATCH_IF_BOTH:
                    pairs.update((i, j) for j in right_nulls)
                continue
            for rep in self.representatives(value):
                for j in index.get(rep, ()):
                    pairs.add((i, j))
        return sorted(pairs)


_ALNUM = re.compile(r"[a-zA-Z0-9]+")


def _representatives(tokens: List[str], max_gaps: int) -> FrozenSet[str]:
    if not tokens:
        return frozenset({""})
    gaps = len(tokens) - 1
    if gaps > max_gaps:
        return frozenset({"".join(tokens), " ".join(sorted(tokens))})
    reps = set()
    for mask in range(1 << gaps):  # 第 k 位 = 1 → 第 k 個空隙拿掉
        words = [tokens[0]]
        for k in range(gaps):
            if mask >> k & 1:
                words[-1] += tokens[k + 1]
            else:
                words.append(tokens[k + 1])
        reps.add(" ".join(sorted(words)))
    return frozenset(reps)
