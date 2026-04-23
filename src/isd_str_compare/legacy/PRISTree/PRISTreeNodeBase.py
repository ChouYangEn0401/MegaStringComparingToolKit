from abc import ABC, abstractmethod
from typing import Literal, Optional


# --- 策略模式：定義各種運算邏輯的抽象基類 ---
class PRISTreeNodeStrategy(ABC):
    """
        所有節點策略的抽象基類
    """
    # _instance = None  ## 我希望可以用單例模式來減少instantiate的部分，但目前要等應用的地方出來才知道怎麼設架構比較好
    #
    # def __new__(cls, *args, **kwargs):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)

    @abstractmethod
    def execute(self, node: "PRISTreeNode", word: str = None) -> bool:
        raise NotImplementedError

class OperationGatePRISTreeNodeStrategy(PRISTreeNodeStrategy):
    """
        所有節點策略的抽象基類
    """
    # _instance = None  ## 我希望可以用單例模式來減少instantiate的部分，但目前要等應用的地方出來才知道怎麼設架構比較好
    #
    # def __new__(cls, *args, **kwargs):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)

    @abstractmethod
    def execute(self, node: "PRISTreeNode") -> bool:
        raise NotImplementedError

# PRISTreeNode 定義：二元樹節點結構
# GLOBAL_INT_BY_PRISTREENODE = 0
class PRISTreeNode:
    @property
    def value(self):
        return self._value
    @property
    def result(self) -> Optional[bool]:
        return self._b_result
    @property
    def node_type(self) -> str:
        return self._type
    @property
    def Excel_AC_UID(self) -> str:
        return self._acid

    def __repr__(self):
        strategy_name = self._strategy.__class__.__name__ if self._strategy else "None"
        return (f"PRISTreeNode(ID={self._id}, ExcelUID={self._acid}, Label='{self._value}', "
                f"Type='{self._type}', Strategy={strategy_name}, Result={self._b_result})")

    def __init__(self, node_id, value, type: Literal["Operator", "Text", "Constraint"], acid):
        self._id = node_id    # 節點ID (整數)，用來串樹用的流水號
        self._value = value   # 節點顯示文字
        self._strategy: PRISTreeNodeStrategy = None   # 節點文字處理邏輯
        self._b_result: bool = None  # 用來記錄`節點文字處理邏輯`的處理結果，目前先用True/False來做種類
        self._type = type  # 簡單記錄一下，節點的屬性
        self._acid = acid  # Excel中權控詞的唯一識別號碼

        self.left: "PRISTreeNode" = None     # 左子節點
        self.right: "PRISTreeNode" = None    # 右子節點

    def reset_results(self):
        self._b_result = None
        if self.left:
            self.left.reset_results()
        if self.right:
            self.right.reset_results()

    def set_strategy(self, new_strategy: "PRISTreeNodeStrategy"):
        self._strategy = new_strategy

    def _run_strategy(self, word="ABC"):
        # global GLOBAL_INT_BY_PRISTREENODE
        # print(f"# {GLOBAL_INT_BY_PRISTREENODE}. {self.node_type}:{self.value}--{self._strategy.__class__}：  [{self._b_result}]")
        self._b_result = self._strategy.execute(self, word)
        # print(f"# {GLOBAL_INT_BY_PRISTREENODE}. {self.node_type}:{self.value}--{self._strategy.__class__}：  [{self._b_result}]")
        # GLOBAL_INT_BY_PRISTREENODE += 1
        return self._b_result

    def run_strategy_and_get_result(self, word="ABC"):
        if self._b_result is None:
            self._run_strategy(word)
        return self._b_result

    def get(self, key: Literal['left', 'right'], default=None):
        if key == 'left':
            return get_left_branch(self.left) if self.left is not None else default
        elif key == 'right':
            return self.right.value if self.right is not None else default
        return default

PRECEDENCE = {
    "OR": 1,
    "AND": 2,
    "NOT": 3,
    None: 4
}
def get_left_branch(node: PRISTreeNode, parent_op=None) -> str:
    """
    遞迴生成節點子樹的運算式，PreOrder 遍歷，依優先級加括號。
    """
    if node is None:
        return ""

    # leaf
    if node.node_type != "LOGIC":
        return node.value

    op = node.value.upper()

    # 處理左右子樹
    left_expr = get_left_branch(node.left, parent_op=op) if node.left else ""
    right_expr = get_left_branch(node.right, parent_op=op) if node.right else ""

    if op == "NOT":
        expr = f"NOT {left_expr}"
    else:
        expr = f"{left_expr} {op} {right_expr}"

    # 括號最小化：子節點優先級比父節點低時加括號
    if parent_op is not None and PRECEDENCE[op] < PRECEDENCE[parent_op]:
        return f"({expr})"
    return expr

# 計算樹深度（高度）
def tree_depth(node: "PRISTreeNode"):
    if not node:
        return 0
    return 1 + max(tree_depth(node.left), tree_depth(node.right))

# 計算樹寬度（葉節點數量）
def tree_width(node: "PRISTreeNode"):
    if not node:
        return 0
    if not node.left and not node.right:
        return 1
    return tree_width(node.left) + tree_width(node.right)

