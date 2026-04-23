import pandas as pd
from typing import List, Tuple, Dict, Any, Type, Union

from ....src.isd_str_sdk.base.AbstractNode import Strategy
from ..contexts import TwoSeriesComparisonContext
from ....src.isd_str_sdk.matching_tools.strategies.stras import ExactMatchStrategy, AbbrevExactMatchStrategy


# -------------------------------------
# Helper: run strategy for one pair
# -------------------------------------
def _run_strategy_once(strategy: Strategy, context, i, j, row2, df2, org_key):
    """
        對單一 (row1, row2) pair 運行策略。
            :param i: df1 的原始索引 i (確保傳輸的索引不會跑掉)。
            :param j: df2 的原始索引 j (確保傳輸的索引不會跑掉)。
    """
    s_result = strategy.evaluate(context)
    if not s_result.success:
        return None

    # 策略匹配成功，返回包含 i, j 索引和分數的字典
    return {
        "Strategy": strategy.__class__.__name__,
        "OrgSerial": row2[org_key],
        "i": i,  # 確保原始索引被正確寫入
        "j": j,  # 確保原始索引被正確寫入
        "Score": s_result.score,
    }


# -------------------------------------
# Worker: multiprocess_strategy_worker (保持名稱不變)
# -------------------------------------
def multiprocess_strategy_worker(
        i: int,
        row1_data: Dict[str, Any],
        df2_data: List[Tuple[Any, Any, Any]],
        df1_key: str,
        df2_key: str,
        org_key: str,
        strategy_cls: Type[Strategy],
        standard: Union[float, int],
        cached_pairs: set,
) -> Tuple[List[Dict[str, Any]], List[Tuple[int, int]]]:
    """
    多進程工作函式：只傳輸比對所需的值。
    """

    strategy = strategy_cls(df1_key, df2_key, standard)
    context = TwoSeriesComparisonContext(None, None)

    # 從傳輸過來的字典重建 row1 Series
    row1 = pd.Series(row1_data)

    worker_raw_matches = []
    worker_exact_pairs = []
    # 使用 strategy_cls.__name__ 進行判斷，確保在 Worker 中是獨立且正確的
    strategy_name = strategy_cls.__name__
    is_exact_level = strategy_cls in [ExactMatchStrategy, AbbrevExactMatchStrategy]

    # 遍歷預先提取的 df2 數據 (O(M))
    for j, v2, org_serial_val in df2_data:
        # 1. AI 快取過濾
        if (i, j) in cached_pairs:
            continue

        # 2. 構造 row2 Series (只包含比對所需的鍵)
        row2 = pd.Series({df2_key: v2, org_key: org_serial_val})

        context.row1 = row1
        context.row2 = row2

        # 3. 運行策略：match_obj 已經是包含正確分數和 i, j 的字典 (或 None)
        match_obj = _run_strategy_once(strategy, context, i, j, row2, pd.Series(), org_key)

        if match_obj:
            if is_exact_level:
                worker_exact_pairs.append((i, j))
            else:
                worker_raw_matches.append(match_obj)

    return worker_raw_matches, worker_exact_pairs

