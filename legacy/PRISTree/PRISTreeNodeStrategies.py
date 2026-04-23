from typing import List

from legacy.PRISTree.PRISTreeNodeBase import PRISTreeNode, PRISTreeNodeStrategy, OperationGatePRISTreeNodeStrategy
from isd_str_sdk.base.IStrProcessor import StrProcessorBase

# --- 邏輯運算子策略 ---
class And_PRISTreeNodeStrategy(OperationGatePRISTreeNodeStrategy):
    def execute(self, node, word="AVA") -> bool:
        # print(f"##[ AND: init({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
        right_res = node.right.run_strategy_and_get_result(word) if node.right else False
        if not right_res:
            node._b_result = False
            # print(f"##] AND: end({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
            return False

        left_res = node.left.run_strategy_and_get_result(word) if node.left else False
        node._b_result = right_res and left_res
        # print(f"##] AND: end({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
        return node._b_result

class Or_PRISTreeNodeStrategy(OperationGatePRISTreeNodeStrategy):
    def execute(self, node: "PRISTreeNode", word: str = "AVA") -> bool:
        # print(f"##[ OR: init({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
        left_res = node.left.run_strategy_and_get_result(word) if node.left else False
        if left_res:
            node._b_result = True
            # print(f"##] OR: end({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
            return True

        right_res = node.right.run_strategy_and_get_result(word) if node.right else False
        node._b_result = right_res
        # print(f"##] OR: end({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
        return node._b_result

class Not_PRISTreeNodeStrategy(OperationGatePRISTreeNodeStrategy):
    def execute(self, node: "PRISTreeNode", word: str = "AVA") -> bool:
        left_res = node.left.run_strategy_and_get_result(word) if node.left else False
        node._b_result = not left_res
        return node._b_result


# --- 文字處理策略（假設有一個簡單的策略） ---
class SimpleTextStrategyPRISTree(PRISTreeNodeStrategy):
    def __init__(self, node: "PRISTreeNode" = None, word: str = "AVA", compare_text: bool = None, stras: List[StrProcessorBase] = None): ## 改一下不是StrProcessorBase，要改用D模組的東西
        pass
        # self._compare_text = compare_text
        # self._strategies = [stra(compare_text) for stra in stras]
        # ### NOTE: 應該要先去決定要真度誰處理，在想如何實作，先跳過 ###
        # print("\t\texe")
        # tmp = node.value
        # for stra in self._strategies:
        #     stra.get_result() ## 需要把它做出來
        # ### NOTE: 應該要先去決定要真度誰處理，在想如何實作，先跳過 ###

        # ### TODO: 地址條會需要先切斷處理！ ###
        # ### TODO: 地址條是否要讓他可以進行前清理？ ###

    def execute(self, node: "PRISTreeNode", word: str = "AVA") -> bool:
        def my_inner_fuzzy(val1):
            # print(f"##[ SimpleText: init({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
            from rapidfuzz.distance import Levenshtein
            distance = Levenshtein.distance(node.value.upper(), val1.upper())
            max_len = max(len(node.value), len(val1))
            similarity = 1.0 - (distance / max_len if max_len > 0 else 1.0)
            # print(f"\t\texe: `{node.value}` Sim `{val1}` >= 0.95: {similarity}, {similarity >= 0.95}")
            return similarity >= 0.95
        node._b_result = any([my_inner_fuzzy(str_) for str_ in word.split(', ')])
        # print(f"##] SimpleText: end({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
        return node._b_result

# --- 文字處理策略（假設有一個簡單的策略） ---
class InText_PRISTreeNodeStrategy(PRISTreeNodeStrategy):
    def execute(self, node: "PRISTreeNode", word: str = "AVA") -> bool:
        # print(f"##[ InText: init({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
        ## 先讓他每次都要重跑，不然就需要reset-all函數
        # if node.result is not None:
        #     return node.result
        node._b_result = (f" {node.value.upper()} " in word.upper()) or (node.value.upper() in word.upper())
        # print(f"\t\texe: `{node.value}` In `{word}`: {node._b_result}")
        # print(f"##] InText: end({node.result}/{node.left.result if node.left is not None else node.left}/{node.right.result if node.right is not None else node.right})")
        return node._b_result

class FuzzyText_PRISTreeNodeStrategy(PRISTreeNodeStrategy):
    def execute(self, node: "PRISTreeNode", word: str = "AVA") -> bool:
        ## 先讓他每次都要重跑，不然就需要reset-all函數
        # if node.result is not None:
        #     return node.result
        # print("\t\texe")
        val1 = str(node.value)
        from rapidfuzz.distance import Levenshtein
        distance = Levenshtein.distance(val1.upper(), word.upper())
        max_len = max(len(val1), len(word))
        similarity = 1.0 - (distance / max_len if max_len > 0 else 1.0)
        # print(f"\t\texe: {node.value} Sim {word} >= 0.95: {similarity}, {similarity >= 0.95}")
        node._b_result = similarity >= 0.95
        return node._b_result

