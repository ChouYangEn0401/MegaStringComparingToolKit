import pandas as pd
from collections import deque

from isd_str_sdk.base.AbstractNode import Node
from isd_str_sdk.str_matching.strategies import *
from isd_str_sdk.core.contexts import (
    TwoSeriesComparisonContext,
    ChildrenValueComparisonContext
)

from legacy.EntireCompareTree.contexts import PRISTreeStructureContext
from legacy.PRISTree.PRISTreeNodeBase import PRISTreeNode


class TreeExecutor:
    """
    負責遍歷樹狀結構並執行每個節點的策略，並精確管理與注入 Context 至 正確的 Strategy 裡面。
    """

    def __init__(self):
        # Context 物件預先建立一次，往後每次只 mutate 屬性而不重新 new，
        # 避免 N×M 次的 allocation 。3.10+ slots=True 的 dataclass 是 mutable 的。
        self.primary_context: TwoSeriesComparisonContext = TwoSeriesComparisonContext(row1=None, row2=None)
        self.pris_tree_context: PRISTreeStructureContext = PRISTreeStructureContext(source_row=None, root_node=None)
        self._b_is_ready = False

    def compile(self):
        self._b_is_ready = True
        return self

    def set_primary_context(self, row1: pd.Series, row2: pd.Series):
        """
        LazyInitialization預備將要執行的測資。
            Args:
                row1: 第一個資料列。(預設應為: source_df)
                row2: 第二個資料列。(預設應為: ac_df)
        """
        # mutate 該共享 context，而不是建新物件 (避免 N×M 次 allocation)
        self.primary_context.row1 = row1
        self.primary_context.row2 = row2
        return self
    def set_pris_tree_context(self, source_row: pd.Series, root_node: PRISTreeNode):
        self.pris_tree_context.source_row = source_row
        self.pris_tree_context.root_node = root_node
        return self

    def execute_tree(self, root_node: Node) -> bool:
        """
        執行整個樹，並將所有 Context 的管理權限集中在此。
            Args:
                root_node: 樹的根節點。
            Returns:
                樹根節點的最終結果。
        """
        if not self._b_is_ready:
            raise ValueError("Please Make Sure You Compile This Module (TreeExecutor) !!!")

        # 實作一個非遞迴的後序遍歷，以節省記憶體 # 使用兩個堆疊來模擬後序遍歷
        stack1 = deque([root_node])
        stack2 = deque()

        while stack1:
            node = stack1.pop()
            stack2.append(node)
            for child in node.children:
                stack1.append(child)

        # 現在 stack2 中已經是後序遍歷的順序，我們開始處理節點
        while stack2:
            node = stack2.pop()
            self._process_node(node)

        # 樹的最終結果儲存在根節點中
        return root_node.result

    def _process_node(self, node: Node):
        """
        私有方法，根據節點類型精準注入 Context 並執行策略。
        """
        # 葉節點：直接使用 primary_context
        if not node.children:
            # 這裡我們根據 node_type 精準注入 Context
            if node.node_type == "Comparison":
                return node.run_strategy(self.primary_context)
            elif node.node_type == "SpecialOperator":
                return node.run_strategy(self.pris_tree_context)
            elif node.node_type == "Logic":
                pass
            else:
                raise TypeError(f"Unknown leaf node type: {node.node_type}")

        # 在這裡，我們能確保所有子節點都已經被處理
        # 因此，它們的結果都已經儲存在 _last_execution_result 中
        child_results = [child.result for child in node.children]
        composite_context = ChildrenValueComparisonContext(children_results=child_results)
        node.run_strategy(composite_context)


