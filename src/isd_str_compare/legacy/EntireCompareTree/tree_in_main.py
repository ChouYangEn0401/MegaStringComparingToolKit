import pandas as pd

from src.lib.sql_query_helper.TreeBilder import main_builder


if __name__ == "__main__":
    df = pd.read_excel("ExampleAcTreeTable.xlsx")
    ac = df.rename(columns={'ACType': 'NodeType', 'Type': 'HierarchyType'})
    main_builder(ac, debug_mode=True)


