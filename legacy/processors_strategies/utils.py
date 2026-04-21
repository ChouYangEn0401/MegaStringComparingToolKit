import functools
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, IntFlag
from typing import Optional, Any, List


# =============================================================================
# 1. 基礎資料結構 (Data Classes & Enums)
# =============================================================================

class RuntimeMatchingController(Enum):
    AllMatch = 0x01  ## 全部比完才會停止
    MatchBreak = 0x02  ## 只要一個對象成功匹配，就會停止
    ExactMatchBreak = 0x03  ## 只要一個完全比對的策略成功，就會停止
    FuzzyMatchBreak = 0x04  ## 只要一個模糊比對的策略成功，就會停止
    ExactMetBreak = 0x05  ## 只要遇到完全比對的策略，就會停止
    FuzzyMetBreak = 0x06  ## 只要遇到模糊比對的策略，就會停止

class MatchMode(IntFlag):
    """匹配策略模式 - 使用位元操作分類"""

    # 基礎模式 (0x0000)
    ORIGINAL_RESULT = 0x0000  # 返回所有原始結果

    # 分數相關模式 (0x01xx)
    BestScoreMatcher = 0x0101  # 最高分者（字典序第一個）
    AllBestScoreMatchers = 0x0102  # 所有最高分者
    All97ScoreMatchers = 0x0103  # 所有分數 >= 97 者
    AllAboveZScoreMatchers = 0x0104  # 所有分數 >= Z 者
    Top3ScoreMatchers = 0x0105  # 前三高分者

    # 數量相關模式 (0x02xx) - 統計「候選人(ac_text)出現次數」
    GreatestAmountMatcher = 0x0201  # 出現最多次的候選人（字典序第一個）
    AllGreatestAmountMatchers = 0x0202  # 所有出現最多次的候選人
    AllMoreThanTwoMatchers = 0x0203  # 所有出現 >= 2 次的候選人
    AllMoreThanNMatchers = 0x0204  # 所有出現 >= N 次的候選人

    # 去重模式 (0x03xx) - 每個候選人只保留一個
    DeduplicateByBestScore = 0x0301  # 每個 ac_text 只保留最高分的一個
    DeduplicateByFirstMatch = 0x0302  # 每個 ac_text 只保留第一次匹配的
    DeduplicateByLastMatch = 0x0303  # 每個 ac_text 只保留最後一次匹配的
    DeduplicateByMostPhases = 0x0304  # 每個 ac_text 只保留經過最多清理階段的

    # 組合模式 (0x04xx)
    MostFrequentInOverZScore = 0x0401  # 高分組中出現最頻繁的候選人
    BestScoreInFrequentGroup = 0x0402  # 高頻組中分數最高的候選人


@dataclass
class MatchContext:
    """儲存當前比對的上下文資料"""
    ac_text: str
    raw_text: str

    # Lazy
    processed_ac_text: str = ""
    processed_raw_text: str = ""
    _is_ready: bool = False

    @property
    def is_ready(self):
        return self._is_ready

    def compile(self):
        if self._is_ready:
            raise ValueError("This Context Is Already Compiled !! Please Make Sure If There Are Any Logic Error !!")

        self.processed_ac_text = self.ac_text
        self.processed_raw_text = self.raw_text
        self._is_ready = True

@dataclass
class MatchCandidate:
    """單個匹配成功的候選人"""
    ac_text: str
    raw_text: str

    matching_score: float
    matching_info: Any = None
    runtime_matching_phases: list[str] = field(default_factory=list)

@dataclass
class MatchSession:
    """匹配會話：記錄所有匹配結果與當前模式"""
    mode: RuntimeMatchingController  # ### FIXME: string compare will be slower than boolean flag ###

    ## Lasy Init
    matched_candidates: list[MatchCandidate] = field(default_factory=list)

    def add_candidate(
            self,
            ac_text: str, raw_text: str, score: float, phases: list[str],
            pac_text: str, praw_text: str,
    ):
        self.matched_candidates.append(
            MatchCandidate(
                ac_text=ac_text, raw_text=raw_text,
                matching_score=score, runtime_matching_phases=phases,
                matching_info={"pac": pac_text, "praw": praw_text},
            )
        )

# 用於模擬匹配結果的物件
class ExampleMatchResult:
    def __init__(self, is_match: bool):
        self.result = is_match

# =============================================================================
# 2. 裝飾器 (Decorator)
# =============================================================================

def with_match_session(func):
    """
    裝飾器：自動建立 MatchSession 並注入到函數中
    """

    # ### REFACTOR: the usage of this function, may be, there are a better practice ?? ###
    @functools.wraps(func)
    def wrapper(matching_mode: MatchMode, runtime_controller_mode: RuntimeMatchingController, *args, **kwargs):
        # session_mode = "AllMatch" # if True else "MatchBreak"
        session = MatchSession(mode=runtime_controller_mode)
        return func(matching_mode, runtime_controller_mode, *args, **kwargs, decorator_auto_fill_savor=session)
    # ### REFACTOR: the usage of this function, may be, there are a better practice ?? ###

    return wrapper

# =============================================================================
# 3. 策略函數 (Strategies)
# =============================================================================

@with_match_session
def strategy_clean_all_then_match(
    matching_mode: MatchMode, runtime_controller_mode: RuntimeMatchingController,
    context: MatchContext,
    text_cleaning_methods: list, matching_methods: list,
    decorator_auto_fill_savor: MatchSession = None,
    b_detail_print: bool = False,
):
    """策略 1：將 Raw Text 全部清理完畢後，再進行比對"""
    phases = []

    # 1. 全部清理完
    for tcm in text_cleaning_methods:
        context.processed_raw_text = tcm.run(context.processed_raw_text)
        phases.append("[tcm]"+tcm.strategy.__class__.__name__)

    # 2. 全部比對完
    for mm in matching_methods:
        result = mm.run(context.processed_ac_text, context.processed_raw_text)
        phases.append("[mm]"+str(mm.strategy.__class__.__name__))
        if b_detail_print:
            print(context.processed_ac_text, context.processed_raw_text, phases[-1], result)  # for debug
        if result.success:
            decorator_auto_fill_savor.add_candidate(
                ac_text=context.ac_text, raw_text=context.raw_text, score=result.score, phases=phases.copy(),
                pac_text=context.processed_ac_text, praw_text=context.processed_raw_text,
            )
        if decorator_auto_fill_savor.mode == "MatchBreak":
            break

    return decorator_auto_fill_savor

@with_match_session
def strategy_clean_step_and_match(
    matching_mode: MatchMode, runtime_controller_mode: RuntimeMatchingController,
    context: MatchContext,
    text_cleaning_methods: list, matching_methods: list,
    decorator_auto_fill_savor: MatchSession = None,
    b_detail_print: bool = False,
):
    """策略 2：每清理一步，就嘗試比對一次 (增量比對)"""
    phases = []

    for tcm in text_cleaning_methods:
        # 每清理一次
        context.processed_raw_text = tcm.run(context.processed_raw_text)
        phases.append("[tcm]"+tcm.strategy.__class__.__name__)

        # 立即比對
        for mm in matching_methods:
            result = mm.run(context.processed_ac_text, context.processed_raw_text)
            phases.append("[mm]"+str(mm.strategy.__class__.__name__))
            if b_detail_print:
                print(context.processed_ac_text, context.processed_raw_text, phases[-1], result)  # for debug
            if result.success:
                decorator_auto_fill_savor.add_candidate(
                    ac_text=context.ac_text, raw_text=context.raw_text, score=result.score, phases=phases.copy(),
                    pac_text=context.processed_ac_text, praw_text=context.processed_raw_text,
                )
            if decorator_auto_fill_savor.mode == "MatchBreak":
                break

    return decorator_auto_fill_savor

@with_match_session
def strategy_static_ac_dynamic_raw(
    matching_mode: MatchMode, runtime_controller_mode: RuntimeMatchingController,
    context: MatchContext,
    text_cleaning_methods: list, ac_cleaning_methods: list,
    matching_methods: list, decorator_auto_fill_savor: MatchSession = None,
    b_detail_print: bool = False,
):
    """策略 3：AC 先清理完 (靜態)，RAW 逐步清理 (動態)，每步比對"""
    phases = []

    # AC 全部清理完
    for acm in ac_cleaning_methods:
        context.processed_ac_text = acm.run(context.processed_ac_text)
        phases.append("[acm]"+acm.strategy.__class__.__name__)

    # RAW 逐步清理並比對
    for tcm in text_cleaning_methods:
        context.processed_raw_text = tcm.run(context.processed_raw_text)
        phases.append("[tcm]"+tcm.strategy.__class__.__name__)

        for mm in matching_methods:
            result = mm.run(context.processed_ac_text, context.processed_raw_text)
            phases.append("[mm]"+str(mm.strategy.__class__.__name__))
            if b_detail_print:
                print(context.processed_ac_text, context.processed_raw_text, phases[-1], result)  # for debug
            if result.success:
                decorator_auto_fill_savor.add_candidate(
                    ac_text=context.ac_text, raw_text=context.raw_text, score=result.score, phases=phases.copy(),
                    pac_text=context.processed_ac_text, praw_text=context.processed_raw_text,
                )
            if decorator_auto_fill_savor.mode == "MatchBreak":
                break

    return decorator_auto_fill_savor

@with_match_session
def strategy_exhaustive_cross_match(
        matching_mode: MatchMode, runtime_controller_mode: RuntimeMatchingController,
        context: MatchContext,
        text_cleaning_methods: list, ac_cleaning_methods: list,
        matching_methods: list,
        decorator_auto_fill_savor: MatchSession = None,
        b_detail_print: bool = False,
):
    """策略 4：窮舉法，AC 與 RAW 皆逐步清理，所有組合皆比對"""
    phases = []

    for acm in ac_cleaning_methods:
        # AC 每清理一次
        context.processed_ac_text = acm.run(context.processed_ac_text)
        phases.append("[acm]"+acm.strategy.__class__.__name__)

        for tcm in text_cleaning_methods:
            # RAW 每清理一次
            context.processed_raw_text = tcm.run(context.processed_raw_text)
            phases.append("[tcm]"+tcm.strategy.__class__.__name__)

            # 全部比對
            for mm in matching_methods:
                result = mm.run(context.processed_ac_text, context.processed_raw_text)
                phases.append("[mm]"+str(mm.strategy.__class__.__name__))
                if b_detail_print:
                    print(context.processed_ac_text, context.processed_raw_text, phases[-1], result)  # for debug
                if result.success:
                    decorator_auto_fill_savor.add_candidate(
                        ac_text=context.ac_text, raw_text=context.raw_text, score=result.score, phases=phases.copy(),
                        pac_text=context.processed_ac_text, praw_text=context.processed_raw_text,
                    )
                if decorator_auto_fill_savor.mode == "MatchBreak":
                    break

    return decorator_auto_fill_savor

@with_match_session
def strategy_configurable_pipeline(
    matching_mode: MatchMode, runtime_controller_mode: RuntimeMatchingController,
    context: MatchContext,
    payload_cleaning_methods: dict[str, tuple[str, Any]], matching_methods: list,
    decorator_auto_fill_savor: MatchSession = None,
    b_detail_print: bool = False,
):
    """策略 5：可配置管道，透過 Dict 定義清理順序"""
    phases = []

    for stra_name, _tuple in payload_cleaning_methods.items():
        stra_type, core_method = _tuple

        # 依據給定規則清理對象
        if stra_type == "acm":
            context.processed_ac_text = core_method.run(context.processed_ac_text)
            phases.append("[acm]"+core_method.strategy.__class__.__name__)
        elif stra_type == "tcm":
            context.processed_raw_text = core_method.run(context.processed_raw_text)
            phases.append("[tcm]"+core_method.strategy.__class__.__name__)

        # 每清理一次，全部比對完
        for mm in matching_methods:
            result = mm.run(context.processed_ac_text, context.processed_raw_text)
            phases.append("[mm]"+str(mm.strategy.__class__.__name__))
            if b_detail_print:
                print(context.processed_ac_text, context.processed_raw_text, phases[-1], result)  # for debug
            if result.success:
                decorator_auto_fill_savor.add_candidate(
                    ac_text=context.ac_text, raw_text=context.raw_text, score=result.score, phases=phases.copy(),
                    pac_text=context.processed_ac_text, praw_text=context.processed_raw_text,
                )
            if decorator_auto_fill_savor.mode == "MatchBreak":
                break

    return decorator_auto_fill_savor

@with_match_session
def strategy_unified_operation_flow(
    matching_mode: MatchMode, runtime_controller_mode: RuntimeMatchingController,
    context: MatchContext,
    payload_methods: dict[str, tuple[str, Any]],
    decorator_auto_fill_savor: MatchSession = None,
    b_detail_print: bool = False,
):
    """策略 6：統一操作流，清理與比對混合在同一個列表中"""
    phases = []

    for stra_name, _tuple in payload_methods.items():
        stra_type, core_method = _tuple
        result = None

        # 依據給定規則清理對象
        if stra_type == "acm":
            context.processed_ac_text = core_method.run(context.processed_ac_text)
        elif stra_type == "tcm":
            context.processed_raw_text = core_method.run(context.processed_raw_text)
        elif stra_type == "mm":
            result = core_method.run(context.processed_ac_text, context.processed_raw_text)
        phases.append(core_method.strategy.__class__.__name__)

        if stra_type=="mm" and result.success:
            if b_detail_print:
                print(context.processed_ac_text, context.processed_raw_text, phases[-1], result)  # for debug
            decorator_auto_fill_savor.add_candidate(
                ac_text=context.ac_text, raw_text=context.raw_text, score=0.00, phases=phases.copy(),
                pac_text=context.processed_ac_text, praw_text=context.processed_raw_text,
            )
        if decorator_auto_fill_savor.mode == "MatchBreak":
            break

    return decorator_auto_fill_savor

# =============================================================================
# 4. 候選人選擇工具
# =============================================================================

def candidate_selector(matching_mode: MatchMode, session: MatchSession, **kwargs) -> Optional[List[MatchCandidate]]:
    """從會話結果中選擇最佳候選人

    Args:
        mode: 匹配模式
        session: 匹配會話
        **kwargs: 額外參數
            - n: 用於 AllMoreThanNMatchers
            - Z: 用於 AllAboveZScoreMatchers (默認 95)
            - score_threshold: 別名，同 Z

    Returns:
        符合條件的候選人列表
    """
    if not session.matched_candidates:
        return []

    candidates = session.matched_candidates

    # === 基礎模式 ===
    if matching_mode == MatchMode.ORIGINAL_RESULT:
        return candidates

    # === 分數相關模式 (0x01xx) ===
    elif matching_mode == MatchMode.BestScoreMatcher:
        if not candidates:
            return []
        max_score = max(c.matching_score for c in candidates)
        best_candidates = [c for c in candidates if c.matching_score == max_score]
        # 字典序排序：先按 ac_text，再按 raw_text
        best_candidates.sort(key=lambda c: (c.ac_text, c.raw_text))
        return [best_candidates[0]]

    elif matching_mode == MatchMode.AllBestScoreMatchers:
        if not candidates:
            return []
        max_score = max(c.matching_score for c in candidates)
        return [c for c in candidates if c.matching_score == max_score]

    elif matching_mode == MatchMode.All97ScoreMatchers:
        return [c for c in candidates if c.matching_score >= 97]

    elif matching_mode == MatchMode.AllAboveZScoreMatchers:
        threshold = kwargs.get('Z', kwargs.get('score_threshold', 95))
        return [c for c in candidates if c.matching_score >= threshold]

    elif matching_mode == MatchMode.Top3ScoreMatchers:
        sorted_candidates = sorted(candidates, key=lambda c: c.matching_score, reverse=True)
        return sorted_candidates[:3]

    # === 數量相關模式 (0x02xx) - 按 ac_text 分組統計 ===
    elif matching_mode == MatchMode.GreatestAmountMatcher:
        if not candidates:
            return []
        _map = defaultdict(list)
        for c in candidates:
            _map[c.ac_text].append(c)  # 按候選人分組

        max_amount = max(len(v) for v in _map.values())
        most_frequent = [key for key, v in _map.items() if len(v) == max_amount]
        most_frequent.sort()  # 字典序
        return _map[most_frequent[0]]

    elif matching_mode == MatchMode.AllGreatestAmountMatchers:
        if not candidates:
            return []
        _map = defaultdict(list)
        for c in candidates:
            _map[c.ac_text].append(c)

        max_amount = max(len(v) for v in _map.values())
        result = []
        for key, v in _map.items():
            if len(v) == max_amount:
                result.extend(v)
        return result

    elif matching_mode == MatchMode.AllMoreThanTwoMatchers:
        if not candidates:
            return []
        _map = defaultdict(list)
        for c in candidates:
            _map[c.ac_text].append(c)

        result = []
        for key, v in _map.items():
            if len(v) >= 2:
                result.extend(v)
        return result

    elif matching_mode == MatchMode.AllMoreThanNMatchers:
        if not candidates:
            return []
        n = kwargs.get('n', 2)
        _map = defaultdict(list)
        for c in candidates:
            _map[c.ac_text].append(c)

        result = []
        for key, v in _map.items():
            if len(v) >= n:
                result.extend(v)
        return result

    # === 去重模式 (0x03xx) - 每個 ac_text 只保留一個 ===
    elif matching_mode == MatchMode.DeduplicateByBestScore:
        if not candidates:
            return []
        _map = defaultdict(list)
        for c in candidates:
            _map[c.ac_text].append(c)

        result = []
        for key, v in _map.items():
            best = max(v, key=lambda c: c.matching_score)
            result.append(best)
        return result

    elif matching_mode == MatchMode.DeduplicateByFirstMatch:
        _map = {}
        for c in candidates:
            if c.ac_text not in _map:  # 只保留第一次出現的
                _map[c.ac_text] = c
        return list(_map.values())

    elif matching_mode == MatchMode.DeduplicateByLastMatch:
        _map = {}
        for c in candidates:
            _map[c.ac_text] = c  # 不斷覆蓋，保留最後一個
        return list(_map.values())

    elif matching_mode == MatchMode.DeduplicateByMostPhases:
        _map = defaultdict(list)
        for c in candidates:
            _map[c.ac_text].append(c)

        result = []
        for key, v in _map.items():
            # 選擇經過最多清理階段的
            longest = max(v, key=lambda c: len(c.runtime_matching_phases))
            result.append(longest)
        return result

    # === 組合模式 (0x04xx) ===
    elif matching_mode == MatchMode.MostFrequentInOverZScore:
        # 先篩選高分組
        threshold = kwargs.get('Z', kwargs.get('score_threshold', 85))
        high_score_candidates = [c for c in candidates if c.matching_score >= threshold]

        if not high_score_candidates:
            return []

        # 在高分組中找出現最頻繁的候選人
        _map = defaultdict(list)
        for c in high_score_candidates:
            _map[c.ac_text].append(c)

        max_amount = max(len(v) for v in _map.values())
        result = []
        for key, v in _map.items():
            if len(v) == max_amount:
                result.extend(v)
        return result

    elif matching_mode == MatchMode.BestScoreInFrequentGroup:
        # 先找出現頻率最高的候選人
        _map = defaultdict(list)
        for c in candidates:
            _map[c.ac_text].append(c)

        max_amount = max(len(v) for v in _map.values())
        frequent_candidates = []
        for key, v in _map.items():
            if len(v) == max_amount:
                frequent_candidates.extend(v)

        # 在高頻組中找最高分
        if not frequent_candidates:
            return []

        max_score = max(c.matching_score for c in frequent_candidates)
        return [c for c in frequent_candidates if c.matching_score == max_score]

    # 預設返回原始結果
    return candidates

# 工具函數：檢查模式類別
def get_mode_category(matching_mode: MatchMode) -> str:
    """獲取模式所屬類別"""
    if matching_mode == MatchMode.ORIGINAL_RESULT:
        return "基礎模式"
    elif 0x0100 <= matching_mode < 0x0200:
        return "分數相關模式"
    elif 0x0200 <= matching_mode < 0x0300:
        return "數量相關模式"
    elif 0x0300 <= matching_mode < 0x0400:
        return "組合模式"
    return "未知模式"

# 工具函數：列出某類別的所有模式
def list_modes_by_category(category_prefix: int) -> List[MatchMode]:
    """列出指定類別的所有模式"""
    return [mode for mode in MatchMode if category_prefix <= mode < category_prefix + 0x0100]

