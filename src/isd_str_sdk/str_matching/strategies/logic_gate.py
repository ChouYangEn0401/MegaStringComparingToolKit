from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from legacy.EntireCompareTree.contexts import ChildrenValueComparisonContext


class AndStrategy(Strategy[ChildrenValueComparisonContext]):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return all(context.children_results)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        results = [child.evaluate(context.original_context) for child in context.children]
        success = all(r.success for r in results)
        # 你可以用平均分數
        score = sum(r.score or 0 for r in results) / len(results)
        return StrategyResult(success=success, score=score, children=results)

class OrStrategy(Strategy[ChildrenValueComparisonContext]):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return any(context.children_results)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        results = [child.evaluate(context.original_context) for child in context.children]
        success = any(r.success for r in results)
        score = max(r.score or 0 for r in results)
        return StrategyResult(success=success, score=score, children=results)

# ### NOTE: untested !@! ### #
# class NotStrategy(Strategy[ChildrenValueComparisonContext]):
#     def evaluate(self, context):
#         if len(context.children) != 1:
#             raise ValueError("NOT strategy requires exactly one child")
#
#         child = context.children[0].evaluate(context.original_context)
#
#         return StrategyResult(
#             success = not child.success,
#             score = 1 - (child.score or 0),  # optional
#             children = [child]
#         )

class NotOrStrategy(OrStrategy):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # """ 先執行 Or 運算以後 翻轉結果 """
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return not super().run(context)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        base_result = super().evaluate(context)
        return StrategyResult(
            success = not base_result.success,  ## 其餘不變，目前只翻轉結果
            score = base_result.score,
            children = base_result.children,
        )

class NotAndStrategy(AndStrategy):
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    # """ 先執行 And 運算以後 翻轉結果 """
    # def run(self, context: ChildrenValueComparisonContext) -> bool:
    #     return not super().run(context)
    # ### NOTE:old_deprecated_maybe logic before applying `evaluate`, keep this until tested !@! ### #
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        base_result = super().evaluate(context)
        return StrategyResult(
            success = not base_result.success,  ## 其餘不變，目前只翻轉結果
            score = base_result.score,
            children = base_result.children,
        )