from legacy.EntireCompareTree.contexts import PRISTreeStructureContext

from isd_str_sdk.base.AbstractStrategy import Strategy


class PRISTreeWalkingStrategy(Strategy[PRISTreeStructureContext]):
    def __init__(self, df1: int, **kwargs): #, df2_ac_col: str, df2_constraint_col: str, **kwargs):
        self.df1_col = df1

    def evaluate(self, context: PRISTreeStructureContext):
        """
            這個 Strategy 不參與 evaluate。只是被要求實作，但不應被呼叫。
        """
        raise NotImplementedError("PRISTreeWalkingStrategy does not support evaluate()")

    def run(self, context: PRISTreeStructureContext) -> bool:
        """
            最高層入口：走策略樹，回傳 boolean（老接口）
        """
        # print(f"@@@@, df[{self.df1_col}] = {context.source_row.get(self.df1_col)}")
        # print(f"@@@@, tree[cur].AC = {context.root_node.get('right')}")
        # print(f"@@@@, tree[cur].CONSTRAINTS = {context.root_node.get('left')}")
        context.root_node.reset_results()
        res = context.root_node.run_strategy_and_get_result(context.source_row.get(self.df1_col))
        # print("FINAL:", res)
        return res

