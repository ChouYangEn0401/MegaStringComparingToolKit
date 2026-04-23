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

