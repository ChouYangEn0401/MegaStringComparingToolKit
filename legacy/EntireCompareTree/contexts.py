import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Any

from legacy.PRISTree.PRISTreeNodeBase import PRISTreeNode
from isd_str_sdk.base.IComparisonContext import IComparisonContext


@dataclass(slots=True)
class TwoSeriesComparisonContext(IComparisonContext):
    """
    用來在遍歷樹時傳遞兩個row比較的外部資料。
    """
    row1: pd.Series
    row2: pd.Series
@dataclass(slots=True)
class TwoSeriesComparisonContextWithStrategyPars(TwoSeriesComparisonContext):
    """
    額外加入一些可以用來設定策略的參數
    """
    stra_pars: Dict[str, Any]
@dataclass(slots=True)
class ChildrenValueComparisonContext(IComparisonContext):
    """
    用來在遍歷樹時傳遞子節點的判定結果，屬於內部資料。
    """
    children_results: List[bool]
@dataclass(slots=True)
class PRISTreeStructureContext(IComparisonContext):
    """
    用來在遍歷樹時傳遞"PRIS舊的樹物件"，把邏輯拆出去，我這邊就不會被搞壞。
    """
    source_row: pd.Series
    root_node: PRISTreeNode  # recheck how this is passed and what is inside

# ### TODO: docs needed !!, when building adapter, i just realize that we need a much more detail ###
## documentation for all these class to make sure API usage is clear and simple
## the entire structure is nicely built, however, the clarity still have space for improvements