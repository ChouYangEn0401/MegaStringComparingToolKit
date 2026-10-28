"""
邏輯閘策略（AND / OR / NotAND / NotOR）。

輸入是 ``ChildrenValueComparisonContext``：呼叫端（比對樹的執行器）先把每個子節點跑完，
把結果放進 ``children_results``，閘只負責「組合」，不自己去跑子節點。

0.4.7 修正（B-2）：0.4.6 以前的 ``evaluate()`` 讀 ``context.children`` 與
``context.original_context``，但 ``ChildrenValueComparisonContext`` 只有
``children_results`` 一個欄位，任何 AND / OR 節點一執行就 ``AttributeError``。
現在只讀 ``children_results``，語意與下游（ACA / pyDMS 的 ``sdk_compat.py``
``Fixed*Strategy``）的修正版一致：

- ``children_results`` 的每一項可以是 ``bool``，也可以是 ``StrategyResult``
  （取 ``.success``）；其他物件一律 ``bool()``。
- AND：``success = all(values)``，``score = True 的比例``（沒有子結果時 0.0）。
- OR：``success = any(values)``，``score = 1.0 if any else 0.0``（沒有子結果時 0.0）。
- NotAND / NotOR：只翻轉 ``success``，``score`` 不變。
- 回傳的 ``StrategyResult.children`` 為 ``None``（閘拿到的是組合前的布林，沒有子結果物件可帶）。
"""
from typing import Any, List

from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.core.contexts import ChildrenValueComparisonContext


def _as_bool(result: Any) -> bool:
    """``StrategyResult`` 取 ``.success``，舊式直接回 bool 的策略結果原樣轉 bool。"""
    return bool(getattr(result, "success", result))


def _child_values(context: ChildrenValueComparisonContext) -> List[bool]:
    return [_as_bool(r) for r in context.children_results]


class AndStrategy(Strategy[ChildrenValueComparisonContext]):
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        values = _child_values(context)
        success = all(values)
        score = sum(values) / len(values) if values else 0.0
        return StrategyResult(success=success, score=score)

class OrStrategy(Strategy[ChildrenValueComparisonContext]):
    def evaluate(self, context: ChildrenValueComparisonContext) -> StrategyResult:
        values = _child_values(context)
        success = any(values)
        score = max((1.0 if v else 0.0 for v in values), default=0.0)
        return StrategyResult(success=success, score=score)

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