# --- 組合節點 (Composite Node) ---
from isd_str_sdk.base.AbstractNode import Node
from isd_str_sdk.base.AbstractStrategy import Strategy
from isd_str_sdk.base.IComparisonContext import IComparisonContext
from .contexts import TwoSeriesComparisonContext, ChildrenValueComparisonContext, PRISTreeStructureContext


# --- 具體節點實作 ---
class CompositeNode(Node):
    def __init__(self, strategy: Strategy[ChildrenValueComparisonContext]):
        super().__init__(strategy)

    @property
    def node_type(self) -> str:
        return "Logic"

    @property
    def display_value(self) -> str:
        return self._strategy.__class__.__name__.replace('Strategy', '').upper()

    def run_strategy(self, context: IComparisonContext) -> bool:
        if not isinstance(context, ChildrenValueComparisonContext):
            raise TypeError("CompositeNode requires a ChildrenValueComparisonContext.")

        # 在執行前清空上次的執行數據 (重要，避免混淆)
        self._last_executed_context = context

        """
            此部分邏輯，現在要把它搬到外面的visitor去
            以確保 Node 之間關係平等。
            且遍歷邏輯由外部管理，同時確保可以精準注入所需要的 context 作為元件。
        """
        # # 遞迴執行所有子節點，並收集結果
        # child_results = [child.run_strategy(context) for child in self._children]
        #
        # # 創建一個新的 ChildrenValueComparisonContext，並將結果傳遞給自己的策略
        # strategy_context = ChildrenValueComparisonContext(children_results=child_results)

        self._result = self._strategy.run(context)

        # 儲存結果
        self._last_execution_result = self.result

        return self.result

    def __repr__(self):
        return f"{self.strategy.__class__.__name__}"  # 例如，"AND" 或 "OR"

# --- 葉節點 (Leaf Node) ---
class LeafNode(Node):
    def __init__(self, strategy: Strategy[TwoSeriesComparisonContext]):
        super().__init__(strategy)

    @property
    def node_type(self) -> str:
        return "Comparison"

    @property
    def display_value(self) -> str:
        algo_name = self._strategy.__class__.__name__.replace('Strategy', '').lower()
        df1_col = getattr(self._strategy, 'df1_col', 'N/A')
        df2_col = getattr(self._strategy, 'df2_col', 'N/A')
        return f"{algo_name} ({df1_col}-{df2_col})"

    def run_strategy(self, context: IComparisonContext) -> bool:
        # LeafNode 執行前需要確保接收到正確的 Context
        if not isinstance(context, TwoSeriesComparisonContext):
            raise TypeError("LeafNode requires a TwoSeriesComparisonContext.")

        # 在執行前清空上次的執行數據 (重要，避免混淆)
        self._last_executed_context = context

        self._result = self._strategy.run(context)

        # 儲存結果
        self._last_execution_result = self.result

        return self.result

    def __repr__(self):
        return f"{self.strategy.name}" # 例如，"exact" 或 "fuzzy"

# --- 葉節點 (Leaf Node) ---
class PRISLeafNode(Node):
    def __init__(self, strategy: Strategy[PRISTreeStructureContext]):
        """
        此特別的葉節點關門處理原本PRIS用樹結構處理處理"權控詞"和"限定詞"的問題
        因為PRIS結構很不好管理與轉換(或只少我現在不想做)，所以用此樹來當container處理就好
        """
        super().__init__(strategy)

    @property
    def node_type(self) -> str:
        return "SpecialOperator"

    @property
    def display_value(self) -> str:
        algo_name = self._strategy.__class__.__name__.replace('Strategy', '').lower()
        df1_col = getattr(self._strategy, 'df1_col', 'N/A')
        df2_col = getattr(self._strategy, 'df2_col', 'N/A')
        return f"{algo_name} ({df1_col}-{df2_col})"

    def run_strategy(self, context: IComparisonContext) -> bool:
        # LeafNode 執行前需要確保接收到正確的 Context
        if not isinstance(context, PRISTreeStructureContext):
            print("LeafNode requires a PRISTreeStructureContext.")
            # raise TypeError("LeafNode requires a PRISTreeStructureContext.")

        # 在執行前清空上次的執行數據 (重要，避免混淆)
        self._last_executed_context = context

        self._result = self._strategy.run(context)
        self._last_execution_result = self.result  # 儲存結果
        return self.result

    def __repr__(self):
        return f"{self.strategy.__class__.__name__}" # 例如，"PRISTreeWalkingStrategy"


