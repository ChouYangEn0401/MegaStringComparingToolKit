import pandas as pd

from src.lib.multi_condition_clean.EntireCompareTree.base.ConfigBase import strategy_pars_base


class pars001(strategy_pars_base):
    def __init__(self):
        super().__init__()
    def _build_configs(self):
        self._config = {
            "Rules":["OR",
               {"ColsCompare":["AND",
                  {"df1":"Name","df2":"Name","method":["OR",{"algo":"FUZZY","standard":0.97},{"algo":"JaroWinkler","standard":0.97}]},
                  {"df1":"ResearcherID","df2":"ResearcherID","method":["OR",{"algo":"EXACT","standard":0.97}]}
               ]},
               {"ColsCompare":["AND",
                  {"df1":"Name","df2":"Name","method":["OR",{"algo":"FUZZY","standard":0.97},{"algo":"JaroWinkler","standard":0.97}]},
                  {"df1":"OrcId","df2":"OrcId","method":["OR",{"algo":"EXACT","standard":0.97}]}
               ]}]
        }
    def _get_df(self, CleaningYear, Dataset_Year, config_key, **kwargs):
        df1 = pd.DataFrame({
            'Name': ['apple', 'banana', 'cherry', 'date'],
            'ResearcherID': [1, 2, 3, 4],
            'OrcId': [5, 6, 7, 8],
            'Score': [9.1, 10.2, 11.3, 12.4]
        })
        df2 = pd.DataFrame({
            'Name': ['aple', 'blueberry', 'cherry', 'date'],
            'ResearcherID': [1, 2, 3, 5],
            'OrcId': [5, 6, 9, 9],
            'Score': [9.1, 10.5, 11.3, 12.6]
        })
        return df1, df2






