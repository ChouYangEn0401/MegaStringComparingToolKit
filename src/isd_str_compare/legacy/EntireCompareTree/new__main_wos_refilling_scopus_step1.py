import time
from typing import Tuple, List, Dict
import pandas as pd

from src.lib.multi_condition_clean.EntireCompareTree.main import try_run, merge_refined_result_with_dataframe_pathes


def ScopusRefilling():
    return {
        "Rules": [
            "OR",
            {
                "ColsCompare": [
                    "AND",
                    {
                        "df1": "DOI",
                        "df2": "DOI",
                        "method": [
                            "OR",
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            },
                        ],
                    },
                    {
                        "df1": "[EDIT] Name",
                        "df2": "[EDIT] Name",
                        "method": [
                            "OR",
                            {
                                "algo": "EXACT",
                                "standard": 1,
                            },
                        ],
                    },
                ]
            },
        ]
    }

def get_pars() -> Tuple[pd.DataFrame, pd.DataFrame, List, List, Dict]:
    ## 3221
    df1 = pd.read_excel("..\\..\\..\\..\\aaaaa\\data\\Cleaned_Raw_Scopus_500DOI.xlsx")
    ## 6403
    df2 = pd.read_excel("..\\..\\..\\..\\aaaaa\\data\\Cleaned_Raw_WoS_500DOI.xlsx")

    df1_selected = ["DOI", "[EDIT] Name"]
    df2_selected = ["DOI", "[EDIT] Name"]
    return df1, df2, df1_selected, df2_selected, ScopusRefilling()

if __name__ == "__main__":
    df1, df2, df1_selected, df2_selected, config = get_pars()

    print(f"======= 開始計時 =======")
    start_time = time.time()
    df_out = try_run(
        df1[df1_selected], df2[df2_selected], config,
        b_open_gui_window=False, b_debug_mode = True,
        output_file_path = "new_refilling_step1.csv",
    )
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"======= 總執行時間：{elapsed:.4f} 秒 =======")

    with pd.ExcelWriter("new_wsr_report.xlsx", engine='openpyxl') as writer:
        df_out.to_excel(writer)

    merge_refined_result_with_dataframe_pathes(
        report_path="new_wsr_report.xlsx",
        df1_path="..\\..\\..\\..\\aaaaa\\data\\Cleaned_Raw_Scopus_500DOI.xlsx",
        df2_path="..\\..\\..\\..\\aaaaa\\data\\Cleaned_Raw_WoS_500DOI.xlsx",
    ).to_excel("new_wsr_Result_Step1.xlsx")

