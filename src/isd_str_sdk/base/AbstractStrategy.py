from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Generic, Optional

from isd_str_sdk.base.IComparisonContext import IComparisonContextFamily


class Strategy(Generic[IComparisonContextFamily], ABC):
    """
    所有運算策略的抽象基類。
    """
    @property
    def IsExactMatch(self) -> bool:
        # ### REFACTOR: 目前還需要想辦法讓他僅針對某class，而不會因為繼承的關係導致繼承者被給予不對的參數 ###
        return False ## 因為大多算法都是模糊匹配，所以我們只針對式的進行覆寫
        # ### REFACTOR: 目前還需要想辦法讓他僅針對某class，而不會因為繼承的關係導致繼承者被給予不對的參數 ###
    @abstractmethod
    def evaluate(self, context: IComparisonContextFamily) -> "StrategyResult":
        pass
    def run(self, context: IComparisonContextFamily) -> bool:
        return self.evaluate(context).success


@dataclass(slots=True)
class StrategyResult:
    success: bool
    score: float | None = None
    children: Optional[List["StrategyResult"]] = None
    # ### NOTE: more features !? ###
    # confidence
    # matched_token_count
    # used_model_version
    # processing_time
    # logs
    # ### NOTE: more features !? ###


class AdvancedStrategy(Strategy[IComparisonContextFamily]):
    """所有運算策略的基類。"""
    @abstractmethod
    def get_advanced_settings(self) -> Dict[str, Dict[str, Any]]:
        """
            the key here is the label and its input category on the ui
            and the extra info may help to provide more info for the ui
            確保這個接口的存在，是為了讓每個策略都能夠提供一個統一的方式來描述它所需要的額外設定，從而讓 UI 能夠根據這些信息動態生成對應的輸入界面。
            或者讓使用者有額外的參數船定進而更加精確的使用想要的模式。
        """
        example = {
            'setting_1': {'mode': 'input', 'level': 'optional/necessary'},
            'setting_2': {'mode': 'select', 'level': 'optional/necessary', 'options': ['option_1', 'option_2', 'option_3']},
        }
        return example



############################################################################################################


####
# 目前發現：
# 1. 我們需要 threashold: float, match_count: int 這兩種參數策略變體
# 2. 另外是我們需要 precleaned 的策略變體，甚至是這邊可能需要用更乾淨的東西建立出來
# 3. 再來是針對 nlp 可能會有多種參數 或者 模型，這邊需要乾淨的街口來統一所有的邏輯
####

from isd_str_sdk.utils.exceptions import MissingParameters
from legacy.EntireCompareTree.contexts import TwoSeriesComparisonContextWithStrategyPars

class NewStrategy(Strategy[TwoSeriesComparisonContextWithStrategyPars], ABC):
    def __init__(self, df1: str, df2: str, standard: float, strategy_parameters, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        try:
            self.keyword = strategy_parameters['keyword']
        except KeyError:
            ## will just broken if not provided with
            raise MissingParameters(['keyword'])

############################################################################################################
