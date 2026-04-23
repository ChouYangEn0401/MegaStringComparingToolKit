import os
import sys
import pandas as pd
from typing import Dict, Callable, Any, List, Tuple
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import csv

from src.hyper_framework.decorators_pack import function_timer
from src.lib.multi_condition_clean.EntireCompareTree.base.EngineBase import ComparisonEngineBase
from src.lib.multi_condition_clean.EntireCompareTree.iterator_framework import UniversalIterator
from src.hyper_framework.monitor.timer.FunctionTimerObject import MultiProcessLoopedFunctionTimer


def _multiprocess_comparison_task(
        idx2: int,  # iter2 的索引 (J) - 高負荷物件的索引
        ele2_data: Any,  # iter2 的資料 (J) - 高負荷物件的資料 (Context)
        batch_of_items1: List[Tuple[int, Any]],  # 批次的 iter1 資料 (I) - 來源資料的批次
        tree_root_config: Any,  # 執行樹根 (self.tree_root)
        executor_cls: type  # 執行器類別 (self._executor.__class__)
) -> List[List[Any]]:
    """
        批次任務函式：
            接收一個 ele2 項目 (Context) 和一批 ele1 項目 (Batch)，在子程序中執行 N*M 的 N 部分。

            1. 因為我們正在透過pickle進行序列化操作，因此會建議能夠用越輕省的資料的話就用越輕省的資料。
                因此這邊的iter2物件，我們直接傳遞內容物而非整個物件過去，以減少序列化的開銷。
            2. 為了避免閉包(func in func)或者類別方法(instance method)造成pickle有失敗序列化的可能，
                這邊就直接把函數抓出來，讓他駔為外部函數，並且把執行氣的類別傳遞給他，以最安全的方式執行。
    """
    try:
        # 在子程序中重新實例化執行器
        executor = executor_cls()
    except Exception as e:
        print(f"[Error] Subprocess Executor initialization failed: {e}", file=sys.stderr)
        return []

    batch_results = []

    # I 迴圈 (在 Process 中執行) - 遍歷 iter1 的批次
    for idx1, ele1_data in batch_of_items1:

        # ele1_data 和 ele2_data 對應於原始程式碼中的 ele1 和 ele2
        # 保持 set_primary_context(ele1, ele2) 的 API 順序
        final_result = executor \
            .set_primary_context(ele1_data, ele2_data).set_pris_tree_context(ele1_data, ele2_data) \
            .compile().execute_tree(tree_root_config)  # 使用 tree_root_config

        if final_result:
            debug_info_str = f"Proc-{os.getpid()}"
            # 結果格式: [df1_idx, df2_idx, final_result, debug_info_str]
            batch_results.append([idx1, idx2, final_result, debug_info_str])

    return batch_results

class ComparisonEngine(ComparisonEngineBase):
    # 預設批次大小，可以在 __init__ 中被 config_rule 覆蓋
    DEFAULT_BATCH_SIZE = 5000
    MAX_PENDING_MULTIPLIER = 2  # 節流限制：待處理 Future 數量是工人數量的倍數

    def __init__(self, config_rule: Dict, build_tree_callback: Callable):
        super().__init__(config_rule=config_rule, build_tree_callback=build_tree_callback, auto_build_tree=True)
        # 從配置中設定批次大小，如果沒有則使用預設值
        self.BATCH_SIZE = config_rule.get('BATCH_SIZE', self.DEFAULT_BATCH_SIZE)

    @function_timer
    def run_comparison(self, source_df: pd.DataFrame, ac_df: pd.DataFrame, output_file_path: str, b_debug_mode=False):
        print("--- 開始執行規則比對 (無GUI 平行運算 模式) ---")

        # 使用 'w' 模式寫入標頭，之後都使用 'a' 模式追加
        # 注意: 在 _core_logic 中，我們在 ProcessPoolExecutor 結束後才關閉檔案
        # 這裡的邏輯需要確保 writer 不會在這裡被關閉，因為我們要傳遞給 _core_logic
        with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["df1_idx", "df2_idx", "final_result", "debug_info"])
            # 將檔案寫入句柄傳遞給核心邏輯
            self._core_logic(source_df, ac_df, writer, b_debug_mode)

        print("--- 規則比對執行完畢 ---")
        return output_file_path

    def _core_logic(self, source_data, ac_data, writer, b_debug_mode=False):
        """
            新核心邏輯：使用多程序、批次、節流模式執行 N*M 比較。
            其中 ac_data (iter2) 為外層上下文迴圈，source_data (iter1) 為內層批次迴圈。
        """

        # 1. 初始化迭代器
        # iter1 (source_data) 現在是內層迴圈 (I loop, 被批次化)。由於 UniversalIterator 返回列表，
        # 故只需初始化一次，可以在外層迴圈中重複迭代。
        iter1_source = source_data
        iter1 = UniversalIterator.from_dataframe(iter1_source)

        # iter2 (ac_data) 現在是外層迴圈 (J loop, Context)
        if isinstance(ac_data, pd.DataFrame):
            iter2 = UniversalIterator.from_dataframe(ac_data)
        elif isinstance(ac_data, list):
            iter2 = UniversalIterator.from_list(ac_data)
        else:
            raise ValueError("[ERROR] ac_data 格式不正確。")
        len_iter1 = len(iter1)
        len_iter2 = len(iter2)
        TOTAL_ITEMS = len_iter1 * len_iter2
        if TOTAL_ITEMS == 0:
            print("資料為空，無需執行比較。")
            return

        # 2. 設定多程序參數 與 計時器
        MAX_WORKERS = os.cpu_count() or 4
        MAX_PENDING_FUTURES = MAX_WORKERS * self.MAX_PENDING_MULTIPLIER
        timer = MultiProcessLoopedFunctionTimer(total=TOTAL_ITEMS, inline=True, color='yellow')
        print(f"啟動多程序比較 (N={len_iter1}, M={len_iter2}, Total={TOTAL_ITEMS:,}, WorkerAmount={MAX_WORKERS:,})")

        # 3. ProcessPoolExecutor 開始
        results_accumulator = []  # 主程序緩衝區，用於收集結果並批量寫入
        executor_cls = self._executor.__class__  # 取得執行器類別，傳遞給子程序

        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as process_executor:
            active_futures = set()  # 追蹤當前正在執行的 Future
            timer.start()

            # 5. 核心邏輯：J 迴圈 (Context) + I 迴圈 (Batch)
            # J 迴圈 (M loop / iter2): 高負荷物件作為上下文
            for item2 in iter2:
                idx2, ele2 = item2.index, item2.data  # 高成本/上下文設定項 (ac_data)
                if b_debug_mode:
                    print(f"\n--- 處理 df2[{idx2}] 的所有比對 (Context設定完成) ---")

                # I 迴圈 (N loop / iter1): 低負荷物件作為批次
                batch_of_items1 = []  # 初始化 iter1 的批次
                for item1 in iter1:
                    idx1, ele1 = item1.index, item1.data
                    batch_of_items1.append((idx1, ele1))

                    # --- 檢查批次是否已滿或內層迴圈結束 ---
                    is_batch_full = len(batch_of_items1) >= self.BATCH_SIZE
                    # 判斷是否為整個 N*M 循環中的最後一個項目
                    is_last_item_overall = (item2.index == len_iter2 - 1 and item1.index == len_iter1 - 1)
                    if is_batch_full or is_last_item_overall:

                        # --- 階段 B-1: 節流檢查與收集 (寫入和清空主程序緩衝區) ---
                        while len(active_futures) >= MAX_PENDING_FUTURES or (len(active_futures) > 0 and is_last_item_overall):

                            # 等待直到有任務完成
                            done, active_futures = wait(active_futures, timeout=0.1, return_when=FIRST_COMPLETED)
                            if not done and is_last_item_overall: break  # 如果整體結束且沒有任務完成，則退出等待

                            # 處理已完成的任務
                            for future in done:
                                try:
                                    # 從 Future 中取出的是批次結果 (List[List[Any]])
                                    batch_results = future.result()
                                    results_accumulator.extend(batch_results)

                                    # 執行批次寫入 (安全操作，在主程序中進行)
                                    if len(results_accumulator) >= self.BATCH_SIZE:
                                        writer.writerows(results_accumulator)
                                        print(f"\n已寫入 {len(results_accumulator):,} 筆資料到檔案...")
                                        results_accumulator.clear()

                                    # 使用一個近似值更新進度條
                                    timer.batched_task_completed(min(len(batch_of_items1), self.BATCH_SIZE), b_show_msg=True, bar=True)
                                except Exception as e:
                                    print(f"\n[Error] Task failed in child process: {e}", file=sys.stderr)

                            if len(active_futures) < MAX_PENDING_FUTURES and not is_last_item_overall: break  # 如果隊列有空間且任務未結束，則退出等待

                        # --- 階段 B-2: 提交新批次任務 ---
                        if batch_of_items1:
                            # 提交整個批次和 J 的上下文資訊
                            future = process_executor.submit(
                                _multiprocess_comparison_task,
                                idx2,  # Context Index (高負荷物件)
                                ele2,  # Context Data (高負荷物件)
                                batch_of_items1,  # Batch of iter1 items
                                self.tree_root,
                                executor_cls
                            )
                            active_futures.add(future)
                            batch_of_items1 = []  # 重置批次

            # 6. 處理所有剩餘的 Future (收尾)
            print("\n## 所有批次任務提交完畢！開始收尾...")
            while active_futures:
                done, active_futures = wait(active_futures, timeout=None, return_when=FIRST_COMPLETED)

                for future in done:
                    try:
                        batch_results = future.result()
                        results_accumulator.extend(batch_results)

                        # 執行批次寫入
                        if len(results_accumulator) >= self.BATCH_SIZE:
                            writer.writerows(results_accumulator)
                            print(f"\n已寫入 {len(results_accumulator):,} 筆資料到檔案...")
                            results_accumulator.clear()

                        # 使用一個近似值更新進度條
                        timer.batched_task_completed(min(len(batch_of_items1), self.BATCH_SIZE), b_show_msg=True, bar=True)
                    except Exception as e:
                        print(f"\n[Error] Task failed in child process during cleanup: {e}", file=sys.stderr)

            # 7. 迴圈結束後，將緩衝區中剩餘的資料寫入檔案
            if results_accumulator:
                writer.writerows(results_accumulator)
                print(f"剩餘的 {len(results_accumulator):,} 筆資料已寫入檔案。")
                results_accumulator.clear()

            timer.stop()

        timer.last_msg(bar=True, color='yellow')
        timer.show_info(b_clean_progress_bar=False)