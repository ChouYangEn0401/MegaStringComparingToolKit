from isd_str_sdk.base.AbstractStrategy import Strategy
from isd_str_sdk.utils.exceptions import MissingParameters
from legacy.EntireCompareTree.contexts import TwoSeriesComparisonContextWithStrategyPars

class OnDevStrategy(Strategy[TwoSeriesComparisonContextWithStrategyPars]):
    def __init__(self, df1: str, df2: str, standard: float, strategy_parameters, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        try:
            self.keyword = strategy_parameters['keyword']
        except KeyError:
            ## will just broken if not provided with
            raise MissingParameters(['keyword'])

