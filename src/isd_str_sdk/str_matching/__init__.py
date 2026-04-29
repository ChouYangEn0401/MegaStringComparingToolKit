from typing import List, Tuple, Union, Type
import pandas as pd

from isd_str_sdk.str_matching.adapters import MatchingStrategyAdapter, STRATEGY_TABLE
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext


def match(
    list1: List[str],
    list2: List[str],
    strategy: Union[str, Type] = "FUZZY",
    threshold: float = 0.0,
    **strategy_params,
) -> List[Tuple[str, str, float]]:
    """
    Level 1 API：對 list1 裡的每個字串，在 list2 中找最佳比對。

    回傳：[(str1, best_match, score), ...]，只含 score >= threshold 的配對。

    Parameters
    ----------
    list1 : 要配對的字串清單（「查詢方」）
    list2 : 候選字串清單（「被比對方」）
    strategy : 策略名稱字串或策略類別，預設 "FUZZY"
               可用："FUZZY" / "EXACT" / "Levenshtein" / "JaroWinkler"
                     "JACCARD" / "LetterLCS" / "WordLCS" / "PREPROCESSED_EXACT"
    threshold : 最低分數門檻（0.0 ~ 1.0），低於此分數的配對不會出現在結果中

    Examples
    --------
    >>> from isd_str_sdk.str_matching import match
    >>> match(["MIT", "Stanford"], ["M.I.T.", "Stanford University"], strategy="FUZZY", threshold=0.5)
    [('MIT', 'M.I.T.', 0.6667), ('Stanford', 'Stanford University', 0.7273)]
    """
    if isinstance(strategy, str):
        strategy_cls = STRATEGY_TABLE[strategy]
    else:
        strategy_cls = strategy

    ## Claude Sonnet 4.5 Edit
    # Pass the caller-provided `threshold` into the strategy as its `standard`
    # value so that strategy implementations that rely on an internal
    # standard/threshold see the same value as the caller's filter.
    strat = strategy_cls("a", "b", standard=threshold, **strategy_params)

    results = []
    for s1 in list1:
        best_s2 = None
        best_score = -1.0
        for s2 in list2:
            ctx = TwoSeriesComparisonContext(
                row1=pd.Series({"a": s1}),
                row2=pd.Series({"b": s2}),
            )
            r = strat.evaluate(ctx)
            if r.score is not None and r.score > best_score:
                best_score = r.score
                best_s2 = s2
        if best_s2 is not None and best_score >= threshold:
            results.append((s1, best_s2, round(best_score, 4)))

    return results


__all__ = ["match", "MatchingStrategyAdapter", "STRATEGY_TABLE",
           "STRATEGY_PARAM_META", "get_strategy_param_meta"]

