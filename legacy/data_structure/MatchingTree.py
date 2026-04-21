"""
    測試代碼，有太多不會與不確定的東西
    實作起來實在太抽象了，先用簡單的架構打好，未來要調整再說
"""
from abc import ABC, abstractmethod
from typing import Type, Union, Dict, Tuple, List
import pandas as pd

from src.lib.multi_condition_clean.data_structure.NodeStrategies import OrStrategy, AndStrategy
from src.lib.multi_condition_clean.data_structure.base.TreeBase import PRISTreeNode ## temp
from src.lib.multi_condition_clean.data_structure.base.TreeTraversal import TreeTraversal, get_value, print_node_info
from src.lib.multi_condition_clean.data_structure.battered___BaseTreeNode import BinaryTreeNodeBase


class ExecutableNodeBase(ABC):
    @property
    def result(self):
        return self._result
    @property
    @abstractmethod
    def value(self):
        pass
    def __init__(self, strategy = None):
        self._strategy = strategy
        self._result = None
    def set_strategy(self, new_strategy = None):
        self._strategy = new_strategy
    def execute_node(self, cmp_data, *args, **kwargs) -> bool:
        return self._execute_node(cmp_data, *args, **kwargs)
    def _execute_node(self, cmp_data, *args, **kwargs) -> bool:
        if self._strategy is None:
            raise ValueError("Strategy Cannot be Empty !!")
        if self._result is None:
            self._result = self._strategy.run_strategy(cmp_data, self.value)
        return self._result

class SingleComparisonMethodTailNode(ExecutableNodeBase):
    @property
    def value(self):
        return self.ac_data
    def __init__(self, ac_data: str, strategy: Type):
        super().__init__(strategy)
        self.ac_data = ac_data

class MultipleComparisonMethodNode(ExecutableNodeBase):
    @property
    def value(self):
        pass
    def __init__(self):
        super().__init__()
        self.left: SingleComparisonMethodTailNode = None
        self.right: SingleComparisonMethodTailNode = None

class MultipleColumnComparisonNode(BinaryTreeNodeBase):
    def __init__(self):
        super().__init__()
        self.left: Union[MultipleComparisonMethodNode | MultipleColumnComparisonNode] = None
        self.right: Union[MultipleComparisonMethodNode | MultipleColumnComparisonNode] = None
class MultipleConditionNode(BinaryTreeNodeBase, PRISTreeNode):
    def __init__(self):
        super().__init__()
        self.left: Union[MultipleColumnComparisonNode | MultipleConditionNode] = None
        self.right: Union[MultipleColumnComparisonNode | MultipleConditionNode] = None
        self.tt = None
        self.callback = None
    def travel_set_callback(self, new_callback):
        self.callback = new_callback
        return self
    def travel_build(self):
        if self.callback is None:
            raise ValueError("Please Set_Callback Before Build !!")
        self.tt = TreeTraversal(self, callback_when_loop_to_each_node=self.callback)
    def travel_compare(self, cmp_series: pd.Series):
        if self.tt is None:
            raise ValueError("Please Build Before Compare !!")
        self.tt.PostOrderAlgor()



########################################   Notion   ########################################
runtime_records: Dict[Tuple[int, int], bool] = {}

def build_tree(row, config_rule) -> MultipleConditionNode:
    return MultipleConditionNode()

def try_run(
        source_df: pd.DataFrame, df1_selected: List[str],
        ac_df: pd.DataFrame, df2_selected: List[str],
        config_rule: Dict
):
    for idx1, row1 in source_df.iterrows():
        for idx2, row2 in ac_df.iterrows():
            result = nsquare_compare(row1, row2, df1_selected, df2_selected, config_rule, callback=print_node_info)
            runtime_records[tuple(idx1, idx2)] = result

def nsquare_compare(row1, row2, df1_selected, df2_selected, config_rule, callback):
    cmp_series = row1[df1_selected]
    target_series = row2[df2_selected]

    ac_tree = build_tree(target_series, config_rule)
    ac_tree.travel_set_callback(callback).travel_build()

    ac_tree.travel_compare(cmp_series)
    print(ac_tree.result)
    return ac_tree.result
########################################   Notion   ########################################

strategy_map = {
    "OR": OrStrategy(),
    "AND": AndStrategy(),
    "exact": ExactMatchStrategy(),
    "fuzzy": FuzzyTextStrategy(),
    "LCS": LCSStrategy(),
}

if __name__ == "__main__":
    df1 = pd.DataFrame({
        'A': [1, 2, 3, 4],
        'B': [5, 6, 7, 8],
        'C': ['apple', 'banana', 'cherry', 'date'],
        'D': [9.1, 10.2, 11.3, 12.4]
    })

    df2 = pd.DataFrame({
        'A': [1, 2, 3, 5],
        'B': [5, 6, 9, 9],
        'C': ['aple', 'blueberry', 'cherry', 'date'],
        'D': [9.1, 10.5, 11.3, 12.6]
    })

    # print(df1)
    # print(df2)

    df1_selected = ["A", "B", "C", "D"]
    df2_selected = ["A", "B", "C", "D"]
    config_rule = {
        "Rules": [  ## layer 1
            "OR",
            {
                "ColsCompare": [  ## layer 2
                    "AND",
                    {
                        "df1": "A",
                        "df2": "A",
                        "method": [  ## layer 3
                            "OR",
                            {
                                "algo": "exact",
                                "standard": 1,
                            }
                        ],
                    },
                    {
                        "df1": "C",
                        "df2": "C",
                        "method": [
                            "OR",
                            {
                                "algo": "fuzzy",
                                "standard": 0.97,
                            },
                            {
                                "algo": "LCS",
                                "standard": 0.93,
                            }
                        ],
                    },
                ]
            },
        ]
    }

    try_run(
        df1, df1_selected,
        df2, df2_selected,
        config_rule
    )


