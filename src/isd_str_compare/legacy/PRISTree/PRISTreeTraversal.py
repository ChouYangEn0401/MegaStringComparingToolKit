from typing import Callable

from src.lib.multi_condition_clean.PRISTree.PRISTreeNodeBase import PRISTreeNode


class TreeTraversal:
    def __init__(self, root_node: PRISTreeNode, callback_when_loop_to_each_node: Callable[[PRISTreeNode], None]):
        self._root = root_node
        self._callback_when_loop_to_each_node = callback_when_loop_to_each_node
    def _InOrderAlgor(self, tree_node: PRISTreeNode = None):
        if tree_node:
            self._InOrderAlgor(tree_node.left)
            self._callback_when_loop_to_each_node(tree_node)
            self._InOrderAlgor(tree_node.right)
    def InOrderAlgor(self):
        print("[InOrderOfTree]")
        self._InOrderAlgor(self._root)
    def _PreOrderAlgor(self, tree_node: PRISTreeNode = None):
        if tree_node:
            self._callback_when_loop_to_each_node(tree_node)
            self._PreOrderAlgor(tree_node.left)
            self._PreOrderAlgor(tree_node.right)
    def PreOrderAlgor(self):
        print("[PreOrderOfTree]")
        self._PreOrderAlgor(self._root)
    def _PostOrderAlgor(self, tree_node: PRISTreeNode = None):
        if tree_node:
            self._PostOrderAlgor(tree_node.left)
            self._PostOrderAlgor(tree_node.right)
            self._callback_when_loop_to_each_node(tree_node)
    def PostOrderAlgor(self):
        print("[PostOrderOfTree]")
        self._PostOrderAlgor(self._root)

def print_node_info(node: PRISTreeNode):
    print(node)
def get_value(node: PRISTreeNode):
    node.run_strategy()
    print_node_info(node)
    # print(node.result)
