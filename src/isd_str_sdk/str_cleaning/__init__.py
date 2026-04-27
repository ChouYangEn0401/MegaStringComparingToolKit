from isd_str_sdk.str_cleaning.strategies.param_str_processors import *
from isd_str_sdk.str_cleaning.strategies.contexted_str_processors import *


NOPARS_STRATEGY_TABLE = {
    "StrFuncNoop": StrFuncNoop,
    "StrFunc_Lowercase": StrFunc_Lowercase,
    "StrFunc_Uppercase": StrFunc_Uppercase,
    "StrFunc_SentenceCapitalization": StrFunc_SentenceCapitalization,
    "StrFunc_WordsCapitalization": StrFunc_WordsCapitalization,
    "StrFunc_KeepEnglishLetter": StrFunc_KeepEnglishLetter,
    "StrFunc_KeepEnglishWordsAndSpaces": StrFunc_KeepEnglishWordsAndSpaces,
    "StrFunc_KeepDigits": StrFunc_KeepDigits,
    "StrFunc_KeepEnglishLetterAndDigits": StrFunc_KeepEnglishLetterAndDigits,
    "StrFunc_RemoveAllSymbols": StrFunc_RemoveAllSymbols,
    "StrFunc_NormalizeSpacingBetweenWords": StrFunc_NormalizeSpacingBetweenWords,
    "StrFunc_NormalizeUnicodeSpacing": StrFunc_NormalizeUnicodeSpacing,
    "StrFunc_StripSymbols": StrFunc_StripSymbols,
    "StrFunc_AscendDictionaryOrder": StrFunc_AscendDictionaryOrder,
    "StrFunc_DescendDictionaryOrder": StrFunc_DescendDictionaryOrder,
    "StrFunc_RemoveHtmlTags": StrFunc_RemoveHtmlTags,
    "StrFunc_CleanEscapedSymbols": StrFunc_CleanEscapedSymbols,
    "StrFunc_NormalizeParentheses": StrFunc_NormalizeParentheses,
    "StrFunc_NormalizeWhitespace": StrFunc_NormalizeWhitespace,
    "StrFunc_KeepEnglishParenthesesAndSpaces": StrFunc_KeepEnglishParenthesesAndSpaces,
    "StrFunc_ExcelACTable_Base": StrFunc_ExcelACTable_Base,
    "StrFunc_RemoveUpperCaseStopwords": StrFunc_RemoveUpperCaseStopwords,
}
STRATEGY_TABLE = {
    "StrFuncWithPars_RemoveSpecificSymbol": StrFuncWithPars_RemoveSpecificSymbol,
    # "StrFunc_UnionByExcelACTable": StrFunc_UnionByExcelACTable,
}

class CleaningStrategyAdapter:
    """
    字串清理策略的統一入口。

    - 無參數策略：CleaningStrategyAdapter("StrFunc_Lowercase").run("HELLO")
    - 有參數策略：CleaningStrategyAdapter("StrFuncWithPars_RemoveSpecificSymbol").run("h@i", pars=["@"])
    """

    def __init__(self, strategy_name: str):
        if strategy_name in NOPARS_STRATEGY_TABLE:
            self.strategy = NOPARS_STRATEGY_TABLE[strategy_name]
            self._has_pars = False
        elif strategy_name in STRATEGY_TABLE:
            self.strategy = STRATEGY_TABLE[strategy_name]
            self._has_pars = True
        else:
            raise KeyError(strategy_name)

    def run(self, input_str: str, pars=None):
        assert type(input_str) == str, "`input_str` Is Not String Type !!"
        if self._has_pars:
            return self.strategy(input_str).get_result(pars)
        return self.strategy(input_str).get_result()

