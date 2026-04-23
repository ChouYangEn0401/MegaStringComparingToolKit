from abc import ABC, abstractmethod
from isd_str_sdk.base.AbstractStrategy import Strategy
from isd_str_sdk.base.IComparisonContext import IComparisonContextFamily


class Node(ABC):
    """
    所有樹節點的抽象基類。
    """
    @property
    def children(self):
        return self._children
    @property
    def result(self):
        return self._result
    @property
    def strategy(self):
        return self._strategy
    @property
    def last_executed_context(self):
        return self._last_executed_context
    @property
    def last_execution_result(self):
        return self._last_execution_result

    def __init__(self, strategy: Strategy[IComparisonContextFamily] = None):
        self._children = []
        self._strategy = strategy
        self._result = None
        # 新增屬性用於暫存執行後的數據，以便視覺化
        self._last_executed_context: IComparisonContextFamily = None
        self._last_execution_result: bool = None

    def add_child(self, child: 'Node'):
        self._children.append(child)

    @abstractmethod
    def run_strategy(self, context: IComparisonContextFamily) -> bool:
        """
            繼承者維持該接口協定為最佳(context: IComparisonContextFamily)。
            因為這樣：
            1. 遵守
            因為這樣可以確保說在未來開發與繼承練上面，都透過最寬的設定去恐控制，
            然後，在實作裡面再動態檢查型別，以確保整理流程方便。

            當然如果真的要改變 IComparisonContext，那麼就要考慮外來所有傳遞物必須為 該 T 類。
        """
        pass

    @property
    @abstractmethod
    def display_value(self) -> str:
        """用於視覺化時顯示在節點上的文字"""
        pass

    @property
    @abstractmethod
    def node_type(self) -> str:
        """用於視覺化時區分節點類型（例如：'Operator', 'Comparison'）"""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(strategy={self.strategy})"


