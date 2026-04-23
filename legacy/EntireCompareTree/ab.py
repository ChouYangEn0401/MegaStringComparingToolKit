from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Generic, TypeVar, Dict, Any, Optional


# 定義 Context 的型別
class IComparisonContext(ABC):
    """
    用來在遍歷樹時傳遞所有外部資料。
    """
    pass

@dataclass
class StrategyResult:
    success: bool
    score: float | None = None
    children: Optional[List["StrategyResult"]] = None
    # ### NOTE: more features !? ###
    # confidence
    # matched_token_count
    # used_model_version
    # processing_time
    # logs
    # ### NOTE: more features !? ###

IComparisonContextFamily = TypeVar("ContextType", bound=IComparisonContext)
class Strategy(Generic[IComparisonContextFamily], ABC):
    """
    所有運算策略的抽象基類。
    """
    @property
    def IsExactMatch(self) -> bool:
        # ### REFACTOR: 目前還需要想辦法讓他僅針對某class，而不會因為繼承的關係導致繼承者被給予不對的參數 ###
        return False ## 因為大多算法都是模糊匹配，所以我們只針對式的進行覆寫
        # ### REFACTOR: 目前還需要想辦法讓他僅針對某class，而不會因為繼承的關係導致繼承者被給予不對的參數 ###
    @abstractmethod
    def evaluate(self, context: IComparisonContextFamily) -> StrategyResult:
        pass
    def run(self, context: IComparisonContextFamily) -> bool:
        return self.evaluate(context).success

class AdvancedStrategy(Strategy[IComparisonContextFamily]):
    """
    所有運算策略的抽象基類。
    """
    @abstractmethod
    def get_advanced_settings(self) -> Dict[str, Dict[str, Any]]:
        """
            the key here is the label and its input category on the ui
            and the extra info may help to provide more info for the ui
        """
        example = {
            'setting_1': {'mode': 'input', 'level': 'optional/necessary'},
            'setting_2': {'mode': 'select', 'level': 'optional/necessary', 'options': ['option_1', 'option_2', 'option_3']},
        }
        return example

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
        self._last_executed_context: IComparisonContext = None
        self._last_execution_result: bool = None

    def add_child(self, child: 'Node'):
        self._children.append(child)

    @abstractmethod
    def run_strategy(self, context: IComparisonContext) -> bool:
        """
            繼承者維持該接口協定為最佳(context: IComparisonContext)。
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


