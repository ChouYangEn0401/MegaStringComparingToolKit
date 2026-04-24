import pandas as pd
from dataclasses import dataclass

from legacy.PRISTree.PRISTreeNodeBase import PRISTreeNode
from isd_str_sdk.base.IComparisonContext import IComparisonContext

# import this first to make sure the original link will be maintained
# but it seems to be fine even if removed, because other place should use from lib directly not circular import
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext, TwoSeriesComparisonContextWithStrategyPars, ChildrenValueComparisonContext

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