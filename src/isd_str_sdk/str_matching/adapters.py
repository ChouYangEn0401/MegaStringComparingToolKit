from isd_str_sdk.str_matching.strategies.undone.quantity_groups import NewJACCARDStrategy
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext, TwoSeriesComparisonContextWithStrategyPars

from isd_str_sdk.str_matching.strategies.logic_gate import OrStrategy, AndStrategy, NotOrStrategy, NotAndStrategy
from isd_str_sdk.str_matching.strategies.exact_matching import ExactMatchStrategy
from isd_str_sdk.str_matching.strategies.structure_matching import InStringStrategy, TwoSideInStringStrategy, TwoSideInWith3WordsStringStrategy
from isd_str_sdk.str_matching.strategies.structure_matching import LetterLCSStrategy, WordLCSStrategy, JaccardStrategy
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy, LevenshteinStrategy, JaroWinklerStrategy
import warnings
import os

# Optional NLP strategy: allow disabling via environment, and tolerate any import error
if os.environ.get("ISD_DISABLE_NLP", "").lower() in ("1", "true", "yes", "on"):
    EmbeddingSimilarityStrategy = None
else:
    try:
        from isd_str_sdk.str_matching.strategies.nlp_matching import EmbeddingSimilarityStrategy
    except Exception as _e:  # catch anything (ImportError, AttributeError, OSError from compiled deps, etc.)
        warnings.warn(
            f"Optional NLP strategy unavailable: {type(_e).__name__}: {_e}",
            ImportWarning,
        )
        EmbeddingSimilarityStrategy = None
from isd_str_sdk.str_matching.strategies.hybrid_matching import PreprocessedExactMatchStrategy, SpacingAndOrderFreeExactStrategy
from isd_str_sdk.str_matching.strategies.undone.OnDenStrategy import OnDevStrategy
from isd_str_sdk.str_matching.strategies.undone.abbrev_matching import AbbrevExactMatchStrategy  # undone


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
    # "PRIS_Tree": PRISTreeWalkingStrategy,
    
    # testable api
    "_on_dev_strategy_": OnDevStrategy,

    # [UPGRADE] testing
    "NewJACCARDStrategy": NewJACCARDStrategy,

    # [UPGRADE] precleaned matching method
    "PREPROCESSED_EXACT": PreprocessedExactMatchStrategy,
    # 0.4.9：空格與詞序都不分（PREPROCESSED_EXACT 的超集）
    "SPACING_ORDER_FREE_EXACT": SpacingAndOrderFreeExactStrategy,

    # undone strategy
    # "AbbrevExactMatchStrategy": AbbrevExactMatchStrategy
}

# Remove any strategies that couldn't be imported (optional deps like sentence-transformers)
STRATEGY_TABLE = {k: v for k, v in STRATEGY_TABLE.items() if v is not None}


from typing import Union, Type, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
#  Strategy parameter metadata
#  Schema per key: {
#    "mode"   : "input" | "select",          # free-text vs dropdown
#    "level"  : "necessary" | "optional",    # required or not
#    "options": [...],                        # only for "select"
#    "default": ...,                          # sensible fallback
#    "label"  : str,                          # human-readable name shown in UI
#  }
# ─────────────────────────────────────────────────────────────────────────────
STRATEGY_PARAM_META: Dict[str, Dict[str, Any]] = {
    "TwoSideInStringStrategy": {
        "strategy_mode": {
            "mode": "select",
            "level": "necessary",
            "options": ["any", "a_in_b", "b_in_a"],
            "default": "any",
            "label": "Match direction",
        }
    },
    "_on_dev_strategy_": {
        "keyword": {
            "mode": "input",
            "level": "necessary",
            "default": "",
            "label": "Keyword",
        }
    },
    "NewJACCARDStrategy": {
        "split_segment": {
            "mode": "input",
            "level": "necessary",
            "default": " ; ",
            "type": "str",
            "label": "Split segment",
        },
        "strategy_mode": {
            "mode": "select",
            "level": "necessary",
            "options": ["score_mode", "amount_mode"],
            "default": "score_mode",
            "type": "str",
            "label": "Strategy mode",
        },
        "scoring_method": {
            "mode": "select",
            "level": "optional",
            "options": ["union_base", "set1_base", "set2_base"],
            "default": "union_base",
            "type": "str",
            "label": "Scoring method",
        },
        "extra_debug_print": {
            "mode": "select",
            "level": "optional",
            "options": ["False", "True"],
            "default": False,
            "type": "bool",
            "label": "Debug print",
        },
    },
    # ── 0.4.9 ────────────────────────────────────────────────────────────
    "SPACING_ORDER_FREE_EXACT": {
        "max_gaps": {
            "mode": "input",
            "level": "optional",
            "default": 12,
            "type": "int",
            "label": "Max gaps to enumerate (2^n combos)",
        },
    },
}


# Strategies that compare two columns and therefore honour NullPolicy
# (logic gates compare children results, not cells, so they are excluded).
_TWO_COLUMN_STRATEGY_KEYS = {
    "EXACT", "IN", "TwoSideInStringStrategy", "TwoSideInWith3WordsStringStrategy",
    "LetterLCS", "WordLCS", "JACCARD", "FUZZY", "Levenshtein", "JaroWinkler",
    "Embedding", "PREPROCESSED_EXACT",
    "SPACING_ORDER_FREE_EXACT",
}


def get_strategy_param_meta(name: str, include_null_policy: bool = True) -> Dict[str, Any]:
    """Return parameter metadata for a strategy by name.

    Returns an ordered dict: {param_key: spec_dict}. Strategy-specific keys come
    first; for two-column strategies the three NullPolicy keys (``null_mode``,
    ``empty_is_null``, ``null_like``) are appended so a GUI built on this
    registry lets the user decide how empty cells are treated. Pass
    ``include_null_policy=False`` to get only the strategy's own keys.

    Falls back to ``get_advanced_settings()`` on the class if the static
    registry has no entry (supports future self-describing strategies).
    """
    own: Dict[str, Any] = {}
    if name in STRATEGY_PARAM_META:
        own = dict(STRATEGY_PARAM_META[name])
    else:
        cls = STRATEGY_TABLE.get(name)
        if cls is not None and hasattr(cls, "get_advanced_settings"):
            try:
                own = dict(cls.__new__(cls).get_advanced_settings())
            except Exception:
                own = {}
    if include_null_policy and name in _TWO_COLUMN_STRATEGY_KEYS:
        from isd_str_sdk.str_matching.null_policy import NullPolicy
        for key, spec in NullPolicy.param_meta().items():
            own.setdefault(key, spec)
    return own


# ### REFACTOR: mvp simple one, we may need a much more stable and clean ###
class MatchingStrategyAdapter:
    """
    字串比對策略的統一入口（Level 2 API）。

    strategy 可傳字串 key 或策略類別本身：
        MatchingStrategyAdapter("FUZZY", standard=0.8)
        MatchingStrategyAdapter(FuzzyRatioStrategy, standard=0.8)

    special_params 用於需要額外建構參數的策略（例如 TwoSideInStringStrategy 需要
    strategy_parameters={"strategy_mode": "a_in_b"}）。
    """

    def __init__(self, strategy: Union[str, Type], standard: float, **special_params):
        if isinstance(strategy, str):
            strategy_cls = STRATEGY_TABLE[strategy]
        else:
            strategy_cls = strategy
        self.strategy = strategy_cls("str1", "str2", standard, **special_params)

    def run(self, str1: str, str2: str):
        assert type(str1) == str, "`str1` Is Not String Type !!"
        assert type(str2) == str, "`str2` Is Not String Type !!"

        import pandas as pd
        ctx = TwoSeriesComparisonContext(
            row1=pd.Series({"str1": str1}),
            row2=pd.Series({"str2": str2}),
        )
        return self.strategy.evaluate(ctx)



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

