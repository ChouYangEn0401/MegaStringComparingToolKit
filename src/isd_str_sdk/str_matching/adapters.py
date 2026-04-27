from isd_str_sdk.str_matching.strategies.undone.quantity_groups import NewJACCARDStrategy
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext, TwoSeriesComparisonContextWithStrategyPars

from isd_str_sdk.str_matching.strategies.logic_gate import OrStrategy, AndStrategy, NotOrStrategy, NotAndStrategy
from isd_str_sdk.str_matching.strategies.exact_matching import ExactMatchStrategy
from isd_str_sdk.str_matching.strategies.structure_matching import InStringStrategy, TwoSideInStringStrategy, TwoSideInWith3WordsStringStrategy
from isd_str_sdk.str_matching.strategies.structure_matching import LetterLCSStrategy, WordLCSStrategy, JaccardStrategy
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy, LevenshteinStrategy, JaroWinklerStrategy
from isd_str_sdk.str_matching.strategies.nlp_matching import EmbeddingSimilarityStrategy
from isd_str_sdk.str_matching.strategies.pris_integration import PRISTreeWalkingStrategy
from isd_str_sdk.str_matching.strategies.hybrid_matching import PreprocessedExactMatchStrategy
from isd_str_sdk.str_matching.strategies.undone.OnDenStrategy import OnDevStrategy
# from isd_str_sdk.str_matching.strategies.undone.abbrev_matching import AbbrevExactMatchStrategy  # broken: depends on isd_str_sdk.matching_tools


# 將字串映射到對應的策略類別
STRATEGY_TABLE = {
    # logic-gate based strategy
    "OR": OrStrategy,
    "AND": AndStrategy,
    "NotOR": NotOrStrategy,
    "NotAND": NotAndStrategy,
    # "**MultipleColumn_all_EXACT": None,

    # exact matching method
    "EXACT": ExactMatchStrategy,

    # structural matching method
    "IN": InStringStrategy,
    "TwoSideInStringStrategy": TwoSideInStringStrategy,
    "TwoSideInWith3WordsStringStrategy": TwoSideInWith3WordsStringStrategy,
    "LetterLCS": LetterLCSStrategy,
    "WordLCS": WordLCSStrategy,
    "JACCARD": JaccardStrategy,

    # fuzzy matching method
    "FUZZY": FuzzyRatioStrategy,
    "Levenshtein": LevenshteinStrategy,
    "JaroWinkler": JaroWinklerStrategy,
    
    # AI matching method
    "Embedding": EmbeddingSimilarityStrategy,

    # special matching method
    "PRIS_Tree": PRISTreeWalkingStrategy,
    
    # testable api
    "_on_dev_strategy_": OnDevStrategy,

    # [UPGRADE] testing
    "NewJACCARDStrategy": NewJACCARDStrategy,

    # [UPGRADE] precleaned matching method
    "PREPROCESSED_EXACT": PreprocessedExactMatchStrategy,

    # undone strategy
    # "AbbrevExactMatchStrategy": AbbrevExactMatchStrategy
}


# ### REFACTOR: mvp simple one, we may need a much more stable and clean ###
class MatchingStrategyAdapter:
    def __init__(self, strategy_name: str, standard: float):
        self.strategy = STRATEGY_TABLE[strategy_name]("str1", "str2", standard)

    def run(
            self,
            ## Public Easy API
            str1: str, str2: str,
            ## Hidden-able Advanced API Settings
            split_segment: str = " ； ", strategy_mode: str = "amount_mode", extra_debug_print: bool = False,
    ):
        assert type(str1) == str, "`str1` Is Not String Type !!"
        assert type(str2) == str, "`str2` Is Not String Type !!"

        import pandas as pd

        # ctx = TwoSeriesComparisonContextWithStrategyPars(
        ctx = TwoSeriesComparisonContext(
            row1=pd.Series({"str1": str1}),
            row2=pd.Series({"str2": str2}),
            # stra_pars={
            #     "split_segment": split_segment,
            #     "strategy_mode": strategy_mode,
            #     "extra_debug_print": extra_debug_print,
            # },
        )

        result = self.strategy.evaluate(ctx)
        return result



if __name__ == "__main__":
    """
        我們會需要一個api接口來處理這個問題，統一函數的呼叫，也方便其他人使用
        *** 急 ***
        *** 急 ***
        *** 急 ***
    """
    import pandas as pd

    while True:
        ctx = TwoSeriesComparisonContextWithStrategyPars(
            row1=pd.Series({'name': input('c_str1--->')+' ； '+input('o_str1--->')}),
            row2=pd.Series({'name': input('c_str2--->')+' ； '+input('o_str2--->')}),
            stra_pars={"split_segment": " ； ", "strategy_mode": "amount_mode", "extra_debug_print": True},
        )

        adapter = MatchingStrategyAdapter("", 0.00)(df1='name', df2='name', standard=1, strategy_parameters=ctx.stra_pars)
        print(adapter.run(ctx), '\n')

