from typing import List, Any, Type
from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.base.IComparisonContext import IComparisonContextFamily
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain

class PreprocessedFuzzyRatioStrategy(Strategy[TwoSeriesComparisonContext]):
    DEFAULT_PROCESSORS = []
    def __init__(self, df1: str, df2: str, standard: Any, processors: List[Type[StrProcessorBase]] = None, **kwargs):
        super().__init__(df1, df2, standard)
        self.chain = StrProcessorsChain(processors or self.DEFAULT_PROCESSORS)
    def _normalization(self, text) -> str:
        return self.chain.run(str(text))
    def evaluate(self, context: IComparisonContextFamily) -> StrategyResult:
        ...
