from typing import Tuple, Dict, Any, Literal
import pandas as pd
from abc import ABC, abstractmethod


class strategy_pars_base(ABC):
    def __init__(self):
        self._config = {}
        self._config_needed_columns = {}  ## 用來快速驗證資料是否提供正確，不然就中斷程序，避免後續問題
        self._build_configs()
    @abstractmethod
    def _build_configs(self):
        pass
        ## Example
        # self._config[0] = {
        #     "Rules": ["OR",
        #         {"ColsCompare": ["AND",
        #             {"df1": "Name", "df2": "Name", "method": ["OR", {"algo": "FUZZY", "standard": 0.97},
        #             {"algo": "JaroWinkler", "standard": 0.97}]}, {"df1": "ResearcherID", "df2": "ResearcherID", "method": ["OR", {"algo": "EXACT", "standard": 0.97}]}
        #         ]},
        #         {"ColsCompare": ["AND",
        #             {"df1": "Name", "df2": "Name", "method": ["OR", {"algo": "FUZZY", "standard": 0.97},
        #             {"algo": "JaroWinkler", "standard": 0.97}]}, {"df1": "OrcId", "df2": "OrcId", "method": ["OR", {"algo": "EXACT", "standard": 0.97}]}
        #         ]}]
        # }
        # self._config_needed_columns[0] = {"df1": ["Name"], "df2": ["Name"]}

    @abstractmethod
    def _get_df1(self, **kwargs):
        return pd.DataFrame({
            'Name': ['apple', 'banana', 'cherry', 'date'],
            'ResearcherID': [1, 2, 3, 4],
            'OrcId': [5, 6, 7, 8],
            'Score': [9.1, 10.2, 11.3, 12.4]
        })
    @abstractmethod
    def _get_df2(self, **kwargs):
        return pd.DataFrame({
            'Name': ['aple', 'blueberry', 'cherry', 'date'],
            'ResearcherID': [1, 2, 3, 5],
            'OrcId': [5, 6, 9, 9],
            'Score': [9.1, 10.5, 11.3, 12.6]
        })
    def _get_df(self, CleaningYear, Dataset_Year, config_key, **kwargs):
        df1 = self._get_df1()
        df2 = self._get_df2()
        ## Example
        # self._check_df_metches_condition(df1, 'df1', config_key)
        # self._check_df_metches_condition(df2, 'df2', config_key)
        return df1, df2

    def _check_df_metches_condition(self, df, df_type: Literal['df1', 'df2'], config_key, b_force_stop = True):
        required_columns = set(self._config_needed_columns.get(config_key, {}).get(df_type, []))
        df_columns = set(df.columns)

        flag = required_columns.issubset(df_columns)
        if b_force_stop and not flag:
            s = "{ " + ', '.join(list(required_columns-df_columns)) + " }"
            raise ValueError(f"DF({df_type}) Does Not Fulfill All Needed Columns({required_columns}), Lacking= {s}")
        return flag

    def _get_config(self, config_key):
        return self._config[config_key]

    def get(self, CleaningYear, Dataset_Year, config_key, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        return (*self._get_df(CleaningYear, Dataset_Year, config_key, **kwargs), self._config[config_key])  # type: ignore
