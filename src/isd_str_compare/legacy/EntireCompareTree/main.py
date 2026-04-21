"""
在這個範例中，我透過
    1. Strategy Pattern：封裝了不同的運算行為。
    2. Composite Pattern：允許Node節點透過不同簡易函數組合成，使他有辦法使用再複雜的樹狀結構中，也允許他有畫圖支援功能。
    3. Dependency Injection (DI) / Inversion of Control (IoC)：
        通過將 Context 介面注入到 Strategy 中，反轉控制權。
        現在，Strategy 不再自己去獲取資料，而是由外部（你的 execute 邏輯）將資料以正確的格式送進來。
"""
import time

from src.lib.multi_condition_clean.EntireCompareTree.stras import *
from src.lib.multi_condition_clean.EntireCompareTree.core import __sample_df, try_run, merge_refined_result_with_dataframe_pathes


def __test_001(b_open_gui_window):
    from src.lib.multi_condition_clean.EntireCompareTree.testable_configs import default_001

    config = default_001()
    # config = default_001_edit_order()
    # config = PRIS_Tree()

    df1, df2 = __sample_df()

    start_time = time.time()
    df_out = try_run(
        df1, df2,
        config, b_open_gui_window=b_open_gui_window,
        output_file_path="report.csv"
    )
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"執行時間：{elapsed:.4f} 秒")

def __test_002(b_open_gui_window):
    from src.lib.multi_condition_clean.EntireCompareTree.testable_configs import TestRealData

    df1 = pd.read_excel("比對2_Cleaned.xlsx")
    df2 = pd.read_excel("比對1_Cleaned.xlsx")

    df1_selected = ["[EDIT] Title"]
    df2_selected = ["[EDIT] Title"]
    config = TestRealData()

    start_time = time.time()
    df_out = try_run(
        df1[df1_selected], df2[df2_selected],
        config, b_open_gui_window=b_open_gui_window,
        output_file_path="wsr_report_raw.csv"
    )
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"執行時間：{elapsed:.4f} 秒")

    save_file_path = "比對12結果.xlsx"
    # print(df_out.head(10))
    # print(f"Save File Into {save_file_path}")
    # df_out.to_excel(save_file_path)

    merge_refined_result_with_dataframe_pathes(
        report_path=save_file_path,
        df1_path="比對2_Cleaned.xlsx",
        df2_path="比對1_Cleaned.xlsx",
    ).to_excel("比對12合併後完整結果.xlsx")

def __test_003(b_open_gui_window):
    from src.lib.multi_condition_clean.EntireCompareTree.testable_configs import test_003_error_tracing

    df1 = pd.read_excel("WoS_df1.xlsx")
    df2 = pd.read_excel("Scopus_df2.xlsx")

    df1_selected = ["DOI", "[EDIT] Name"]
    df2_selected = ["DOI", "[EDIT] Name"]

    config = test_003_error_tracing()
    # config = default_001_edit_order()
    # config = PRIS_Tree()

    start_time = time.time()
    df_out = try_run(
        df1[df1_selected], df2[df2_selected],
        config, b_open_gui_window=b_open_gui_window,
        output_file_path="error_checking.csv"
    )
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"執行時間：{elapsed:.4f} 秒")

def __test_004(b_open_gui_window = False):
    from src.extra_tools.Org1Compare.core import _address_org1_ac_process
    _address_org1_ac_process(tree_table_filepath ="ExampleAcTreeTable.xlsx", all_address_filepath ="ExampleAddress.xlsx", config_file="PRISACA_CompareConfig.json", b_open_gui_window = b_open_gui_window)


if __name__ == "__main__":
    # filtered_df1, filtered_df2, config = pars_0909_test().get(1, 0)
    # df = main_outer_caller(filtered_df1, filtered_df2, config, False, "local_test.csv")
    # df.to_excel(f"tests\\out\\test_OUT.xlsx")
    # exit()

    pass
    ## Example
    # filtered_df1, filtered_df2, config = pars002()
    # main_outer_caller(filtered_df1, filtered_df2, config, False, "local_test.csv").to_excel(f"tests\\out\\{Y}_OUT.xlsx")

    # __test_001(True) ## PASS
    # __test_002(False) ## PASS
    # __test_003(True) ## PASS
    # __test_004(False) ## PASS

