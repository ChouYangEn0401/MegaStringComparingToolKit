import time
import tkinter as tk
from tkinter import Toplevel
from typing import Dict, List, Callable, Tuple, Any
import pandas as pd
import csv

from src.lib.multi_condition_clean.EntireCompareTree.base.EngineBase import ComparisonEngineBase
from src.hyper_framework.monitor.timer.FunctionTimerObject import LoopedFunction_timer_decorator, LoopedFunctionTimer
from src.lib.multi_condition_clean.EntireCompareTree.draw import TreeVisualizer
from src.lib.multi_condition_clean.EntireCompareTree.executor import TreeExecutor
from src.lib.multi_condition_clean.EntireCompareTree.iterator_framework import UniversalIterator, IterationItem, LoopCoordinator


# 從這裡開始，GUITreeTraversalApp 成為一個專門的「視窗介面控制器」
class GUITreeTraversalApp(ComparisonEngineBase, tk.Tk):
    def __init__(
            self,
            config_rule: Dict,
            build_tree_callback: Callable
    ):
        super().__init__(config_rule=config_rule, build_tree_callback=build_tree_callback, auto_build_tree=False)
        ## UI Setting
        self.title("比對流程控制")
        self.geometry("300x100")

        ## Data Confirmation
        if "Rules" not in config_rule:
            raise ValueError("Config rule must have a 'Rules' key.")
        self.config_rule = config_rule
        self.build_tree_callback = build_tree_callback

        # 在這裡，只建立一次樹和執行器
        self.tree_root = self.build_tree_callback(self.config_rule["Rules"])
        self._executor = TreeExecutor()

        ## Variables
        self._current_df1_batch_windows: List[Toplevel] = []
        self.start_time = time.time()
        self.continue_flag = tk.StringVar(self)
        self.continue_flag.set("wait")

        ## Start Init
        self.__build_widget()

    def __build_widget(self):
        # 在控制視窗上創建「繼續」按鈕
        self.continue_button = tk.Button(self, text="繼續下一組比對", command=self.__on_continue_click)
        self.continue_button.pack(pady=20)

    def __on_continue_click(self):
        """當「繼續」按鈕被點擊時，改變旗標值以解除暫停。"""
        self.continue_flag.set("continue")

    def _print_run_time(self, message):
        print(f"{message}: {time.time() - self.start_time:.2f} sec")
        return self

    def _reset_start_time(self):
        self.start_time = time.time()
        return self

    def run_comparison_experiment(self, source_df, ac_df, output_file_path="wsr_report_raw.csv"):
        print("--- 開始執行規則比對 (GUI 模式) ---")
        self._reset_start_time()

        # 使用 'w' 模式寫入標頭，之後都使用 'a' 模式追加
        with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["df1_idx", "df2_idx", "final_result", "debug_info"])
            self._core_logic(source_df, ac_df, writer)

        self._print_run_time("比對運算")._reset_start_time()

        self.destroy()
        self._print_run_time("程序關閉")._reset_start_time()
        print("--- 規則比對執行完畢 ---")
        return output_file_path

    def on_window_pause_and_wait(self, *args, **kwargs):
        # 強制 Tkinter 更新以顯示所有新創建的視窗
        self.update_idletasks()
        self.update()

        # 將控制視窗置頂並給予焦點，確保使用者能看到並點擊按鈕
        self.deiconify()  # 如果之前被隱藏，則顯示
        self.lift()  # 提升到最頂層
        self.focus_force()  # 強制獲取焦點

        # 暫停執行，等待 continue_flag 改變
        # 在此期間，Tkinter 的事件迴圈仍在運行，所有彈出的視窗都是可互動的
        self.wait_variable(self.continue_flag)

        # 關閉當前批次的所有視窗
        for window in self._current_df1_batch_windows:
            window.destroy()
            del window
        self._current_df1_batch_windows.clear()

        # 重置旗標，為下一輪等待做準備
        self.continue_flag.set("wait")

    def _core_logic(self, source_data, ac_data, writer, b_debug_mode = False):
        iter1 = UniversalIterator.from_dataframe(source_data)
        iter2 = None
        if isinstance(ac_data, pd.DataFrame):
            iter2 = UniversalIterator.from_dataframe(ac_data)
        elif isinstance(ac_data, list):
            iter2 = UniversalIterator.from_list(ac_data)
        len_iter1 = len(iter1)
        len_iter2 = len(iter2)

        # 新增一個緩衝區來暫存結果
        result_buffer = []
        timer = LoopedFunctionTimer(total=len_iter1*len_iter2, inline=True, color='blue')

        # @LoopedFunction_timer_decorator(timer=timer)
        def comparison_callback(item1: IterationItem, item2: IterationItem):
            """
            這是一個回呼函式，負責執行單次比對的核心邏輯。
            """

            timer.start()

            # ### NOTE: ele can be pd.Series or PRISTreeNode ###
            idx1, ele1 = item1.index, item1.data
            idx2, ele2 = item2.index, item2.data

            # 每次比對都設定上下文，但不重建樹
            final_result = self._executor \
                .set_primary_context(ele1, ele2).set_pris_tree_context(ele1, ele2) \
                .compile().execute_tree(self.tree_root)

            if final_result:
                # 建立要寫入的單行數據
                debug_info_str = str({node: node.result for node in self.tree_root.children})
                result_buffer.append([idx1, idx2, final_result, debug_info_str])

                # GUI模式下，如果緩衝區滿了，則寫入檔案並清空
                if len(result_buffer) >= self.BATCH_SIZE:
                    writer.writerows(result_buffer)
                    result_buffer.clear()
                    print(f"已寫入 {self.BATCH_SIZE} 筆資料到檔案...")

            timer.stop()

            self._current_df1_batch_windows.append(
                TreeVisualizer(
                    self, self.tree_root,
                    title=f"比對結果: df1[{idx1}] vs df2[{idx2}] - 最終結果: {final_result}",
                    debug_mode=False
                )
            )
            timer.msg(item2.index + 1 + len_iter2 * (item1.index), bar=True)

        # coordinator = LoopCoordinator([iter1, iter2]) \
        #     .on_item(0, lambda item1: print(f"\n--- 處理 df1[{item1.index}] 的所有比對 ---")) \
        #     .on_item(1, lambda *args, _timer = timer, **kwargs: _timer.start()) \
        #     .on_item(1, comparison_callback) \
        #     .on_item(1, lambda *args, _timer = timer, **kwargs: _timer.stop()) \
        #     .on_item(1, lambda item1, *args, _timer = timer, **kwargs: _timer.msg(item1.index)) \
        #     .on_exit(0, self.on_window_pause_and_wait)
        # coordinator.run()
        coordinator = LoopCoordinator([iter1, iter2]) \
            .on_item(0, lambda item1: print(f"\n--- 處理 df1[{item1.index}] 的所有比對 ---")) \
            .on_item(1, comparison_callback) \
            .on_exit(0, self.on_window_pause_and_wait)
        coordinator.run()
        timer.show_info(b_clean_progress_bar=False)

        # 迴圈結束後，將緩衝區中剩餘的資料寫入檔案
        if result_buffer:
            writer.writerows(result_buffer)
            result_buffer.clear()
            print(f"剩餘的資料已寫入檔案。")