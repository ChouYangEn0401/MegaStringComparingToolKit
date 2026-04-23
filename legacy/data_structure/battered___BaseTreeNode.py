from abc import ABC, abstractmethod
class TreeNodeBase(ABC):
    @property
    def depth(self):
        raise NotImplementedError
    @property
    def width(self):
        raise NotImplementedError
    def __repr__(self):
        raise NotImplementedError

class BinaryTreeNodeBase(TreeNodeBase):
    @property
    def depth(self):
        return self.__tree_depth(self)
    @property
    def width(self):
        return self.__tree_width(self)
    def __tree_depth(self, node):
        if not node:
            return 0
        return 1 + max(self.__tree_depth(node.left), self.__tree_depth(node.right))
    def __tree_width(self, node):
        if not node:
            return 0
        if not node.left and not node.right:
            return 1
        return self.__tree_width(node.left) + self.__tree_width(node.right)

    def __init__(self):
        super().__init__()
        self.left: [BinaryTreeNodeBase] = None
        self.right: [BinaryTreeNodeBase] = None
    def __repr__(self):
        return f"TreeNode(left={self.left}, right='{self.right}')"


