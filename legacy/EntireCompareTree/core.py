"""
在這個範例中，我透過
    1. Strategy Pattern：封裝了不同的運算行為。
    2. Composite Pattern：允許Node節點透過不同簡易函數組合成，使他有辦法使用再複雜的樹狀結構中，也允許他有畫圖支援功能。
    3. Dependency Injection (DI) / Inversion of Control (IoC)：
        通過將 Context 介面注入到 Strategy 中，反轉控制權。
        現在，Strategy 不再自己去獲取資料，而是由外部（你的 execute 邏輯）將資料以正確的格式送進來。
"""
from typing import Union
import time

from ...src.isd_str_sdk.base.AbstractNode import Node
from .base.ComparisonEngine import ComparisonEngine
from .base.GUITreeTraversalApp import GUITreeTraversalApp
from .nodes import CompositeNode, LeafNode, PRISLeafNode
from .stras import *
from legacy.PRISTree.PRISTreeNodeBase import PRISTreeNode

# 將字串映射到對應的策略類別
strategy_map = {
    # operator
    "OR": OrStrategy,
    "AND": AndStrategy,
    "NotOR": NotOrStrategy,
    "NotAND": NotAndStrategy,
    "**MultipleColumn_all_EXACT": None,
    # exact compare
    "EXACT": ExactMatchStrategy,
    "IN": InStringStrategy,
    # structural compare
    "LetterLCS": LetterLCSStrategy,
    "WordLCS": WordLCSStrategy,
    "JACCARD": JaccardStrategy,
    # fuzzy compare
    "FUZZY": FuzzyRatioStrategy,
    "Levenshtein": LevenshteinStrategy,
    "JaroWinkler": JaroWinklerStrategy,
    # AI compare
    "Embedding": EmbeddingSimilarityStrategy,
    # special compare
    "PRIS_Tree": PRISTreeWalkingStrategy,
    # testing
    "NewJACCARDStrategy": NewJACCARDStrategy,
    "(testing) NewStrategy": NewStrategy,
}
usable_methods_in_moduleDF_combo = [
    "EXACT", "IN",
    "LetterLCS", "WordLCS", "JACCARD", "NewJACCARDStrategy",
    "FUZZY", "Levenshtein", "JaroWinkler",
    "Embedding",
    "(testing) NewStrategy",
]


def build_tree(config_rule: Union[str, Dict, List], parent_params: Dict = None) -> Node:
    """
    根據 config_rule 和父節點參數遞迴地建構並返回樹的根節點。
    """
    parent_params = parent_params or {}

    if isinstance(config_rule, list):
        operator = config_rule[0]  ## 特別針對第0筆的LogicOperator做處理
        node_strategy = strategy_map[operator]()
        composite_node = CompositeNode(strategy=node_strategy)

        for sub_rule in config_rule[1:]:  ## 然後後面物件就建立成樹，其實邏輯頗好
            child_nodes = build_tree(sub_rule, parent_params)
            for child_node in child_nodes:  # type: ignore
                composite_node.add_child(child_node)
        return composite_node

    elif isinstance(config_rule, dict):
        ## 透過每次逐層擴展，會把內部陣列扁平化，但我覺得這樣效能好像不是太好？
        current_params = {**parent_params, **config_rule}

        if "algo" in current_params:
            algo = current_params["algo"]
            strategy_class = strategy_map[algo]
            leaf = LeafNode(strategy=strategy_class(**current_params))  ## 因為扁平化基本上就可以拿到 df1, df2, standard
            return [leaf]  # type: ignore

        nodes = []
        for key in config_rule:
            if "PRIS_Tree" == key:
                nodes.append(
                    PRISLeafNode(strategy=strategy_map["PRIS_Tree"](*[
                        config_rule[key]["df1_col"],
                    ]))
                )
            elif isinstance(config_rule[key], (list, dict)):
                nodes.append(
                    build_tree(config_rule[key], current_params)  ## 就會持續做，然後資料就會被持續扁平化
                )
        return nodes  # type: ignore

    raise ValueError(f"Invalid rule format: {config_rule}")


def try_run(
        df1: pd.DataFrame, df2: pd.DataFrame, config_rule: Dict,
        b_open_gui_window = False, b_debug_mode = False,
        # ### REFACTOR: this code should use relative path, or it may contaminate core lib space ###
        output_file_path = "wsr_report_raw.csv"
        # ### REFACTOR: this code should use relative path, or it may contaminate core lib space ###
):
    path = ""
    if b_open_gui_window:
        # 使用 GUI 模式
        app = GUITreeTraversalApp(config_rule=config_rule, build_tree_callback=build_tree)
        path = app.run_comparison_experiment(df1, df2, output_file_path=output_file_path)
    else:
        # 使用無 GUI 模式
        engine = ComparisonEngine(config_rule=config_rule, build_tree_callback=build_tree)
        path = engine.run_comparison(df1, df2, output_file_path=output_file_path, b_debug_mode=b_debug_mode)

    # 完整報告 DataFrame
    report_df = pd.read_csv(path, usecols=["df1_idx", "df2_idx", "final_result"])

    # 在合併前，強制將鍵值欄位轉換為整數型態
    # 這能確保 'df1_idx' 和 'df2_idx' 與原始 DataFrame 的整數索引資料型態一致
    report_df['df1_idx'] = report_df['df1_idx'].astype(int)
    report_df['df2_idx'] = report_df['df2_idx'].astype(int)

    merged_df = report_df \
        .merge(df1, left_on="df1_idx", right_index=True, how="left", suffixes=("", "_df1")) \
        .merge(df2, left_on="df2_idx", right_index=True, how="left", suffixes=("", "_df2"))
    print(merged_df)

    if b_debug_mode:
        print("Get Important")
    refined_df = merged_df[["df1_idx", "df2_idx", "final_result"]]
    if b_debug_mode:
        print(refined_df)  # 精簡結果
    return refined_df


def try_run_with_tree(
        df1: pd.DataFrame, trees: List[PRISTreeNode], config_rule: Dict,
        b_open_gui_window = False, b_debug_mode = False,
        output_file_path = "wsr_report_raw.csv"
):
    path = ""
    if b_open_gui_window:
        # 使用 GUI 模式
        app = GUITreeTraversalApp(config_rule=config_rule, build_tree_callback=build_tree)
        path = app.run_comparison_experiment(df1, trees, output_file_path=output_file_path)
    else:
        # 使用無 GUI 模式
        engine = ComparisonEngine(config_rule=config_rule, build_tree_callback=build_tree)
        path = engine.run_comparison(df1, trees, output_file_path=output_file_path, b_debug_mode=b_debug_mode)

    # 完整報告 DataFrame
    report_df = pd.read_csv(path, usecols=["df1_idx", "df2_idx", "final_result"])
    df2 = pd.DataFrame([{"df2_idx": i, "AC": tree.get('right'), 'CONSTRAINTS': tree.get('left'), "AcId": tree.Excel_AC_UID} for i, tree in enumerate(trees)])

    # print(df1)
    # print(df2)

    # 在合併前，強制將鍵值欄位轉換為整數型態
    # 這能確保 'df1_idx' 和 'df2_idx' 與原始 DataFrame 的整數索引資料型態一致
    report_df['df1_idx'] = report_df['df1_idx'].astype(int)
    report_df['df2_idx'] = report_df['df2_idx'].astype(int)

    merged_df = report_df \
        .merge(df1, left_on="df1_idx", right_index=True, how="left", suffixes=("", "_df1")) \
        .merge(df2, left_on="df2_idx", right_index=True, how="left", suffixes=("", "_df2"))
    # print(merged_df)

    if b_debug_mode:
        print("Get Important")
    refined_df = merged_df[["df1_idx", "AcId", "final_result"]]
    if b_debug_mode:
        print(refined_df)  # 精簡結果
    return refined_df


def merge_refined_result_with_dataframes(
        report_df, df1, df2,
        df1_prefix="df1_", df2_prefix="df2_"
) -> pd.DataFrame:
    # 過濾出 True 的結果
    refined_df = report_df[report_df["final_result"] == True].copy()

    # 修正：在合併前，強制將鍵值欄位轉換為整數型態
    refined_df['df1_idx'] = refined_df['df1_idx'].astype(int)
    refined_df['df2_idx'] = refined_df['df2_idx'].astype(int)

    # 對 df1, df2 加上 prefix
    df1_prefixed = df1.add_prefix(df1_prefix)
    df2_prefixed = df2.add_prefix(df2_prefix)

    # 合併時的 index 要正確對齊
    df1_prefixed.index.name = "df1_idx"
    df2_prefixed.index.name = "df2_idx"

    # 合併資料
    merged = (
        refined_df
        .merge(df1_prefixed, left_on="df1_idx", right_index=True, how="left")
        .merge(df2_prefixed, left_on="df2_idx", right_index=True, how="left")
    )

    print(merged.head())  # 測試看結果
    return merged

def merge_refined_result_with_dataframe_pathes(
        report_path="report.xlsx", df1_path="df1.xlsx", df2_path="df2.xlsx",
        df1_prefix="df1_", df2_prefix="df2_"
) -> pd.DataFrame:
    # 讀取檔案
    df1 = pd.read_excel(df1_path)
    df2 = pd.read_excel(df2_path)
    return merge_refined_result_with_dataframe(df1, df2, report_path, df1_prefix, df2_prefix)
def merge_refined_result_with_dataframe(
        df1: pd.DataFrame, df2: pd.DataFrame, report_path="report.xlsx",
        df1_prefix="df1_", df2_prefix="df2_"
) -> pd.DataFrame:
    # 讀取檔案
    if report_path.endswith(".xlsx"):
        report_df = pd.read_excel(report_path)
    elif report_path.endswith(".csv"):
        report_df = pd.read_csv(report_path)
    return merge_refined_result_with_dataframes(report_df, df1, df2, df1_prefix, df2_prefix)


def __sample_df():
    df1 = pd.DataFrame({
        'A': [1, 2, 3, 4],
        'B': [5, 6, 7, 8],
        'C': ['apple', 'banana', 'cherry', 'date'],
        'D': [9.1, 10.2, 11.3, 12.4]
    })

    df2 = pd.DataFrame({
        'A': [1, 2, 3, 5],
        'B': [5, 6, 9, 9],
        'C': ['aple', 'blueberry', 'cherry', 'date'],
        'D': [9.1, 10.5, 11.3, 12.6]
    })

    df1_selected = ["A", "B", "C", "D"]
    df2_selected = ["A", "B", "C", "D"]
    return df1[df1_selected], df2[df2_selected]

def main_outer_caller(filtered_df1, filtered_df2, config, b_open_gui_window, in_process_temp_csv_path) -> pd.DataFrame:
    start_time = time.time()
    df_out = try_run(
        filtered_df1, filtered_df2,
        config, b_open_gui_window=b_open_gui_window,
        output_file_path=in_process_temp_csv_path
    )
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"執行時間：{elapsed:.4f} 秒")
    return merge_refined_result_with_dataframes(df_out, filtered_df1, filtered_df2)

