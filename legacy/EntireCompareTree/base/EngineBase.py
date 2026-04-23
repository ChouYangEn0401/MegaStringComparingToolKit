from abc import abstractmethod
from typing import Dict, Callable

from src.lib.multi_condition_clean.EntireCompareTree.executor import TreeExecutor


class ComparisonEngineBase:
    # 設定批次寫入的大小，這是一個可調整的參數
    BATCH_SIZE = 10000

    def __init__(self, config_rule: Dict, build_tree_callback: Callable, auto_build_tree = False, **kwargs):
        ## Data Confirmation
        if "Rules" not in config_rule:
            raise ValueError("Config rule must have a 'Rules' key.")
        self.config_rule = config_rule
        self.build_tree_callback = build_tree_callback

        ## 在這裡，只建立一次樹和執行器
        self.tree_root = None
        self._get_tree(build_new=auto_build_tree)
        self._executor = TreeExecutor()

        ## make sure it can handle python MRO analysis
        super().__init__(**kwargs)

    def _get_tree(self, build_new=False):
        if build_new:
            self.tree_root = self.build_tree_callback(self.config_rule["Rules"])
        return self.tree_root

    @abstractmethod
    def _core_logic(self, source_data, ac_data, writer, b_debug_mode = False):
        pass