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
    "StrFunc_RemoveUpperCaseStopwords": StrFunc_RemoveUpperCaseStopwords,
    # ── Excel AC Table (pre-contextualised) ──────────────────────────────────
    "StrFunc_ExcelACTable_UnionLetter_STOPWORD":  StrFunc_ExcelACTable_UnionLetter_STOPWORD,
    "StrFunc_ExcelACTable_UnionLetter_SYMBOL":    StrFunc_ExcelACTable_UnionLetter_SYMBOL,
    "StrFunc_ExcelACTable_UnionLetter_ENCODING":  StrFunc_ExcelACTable_UnionLetter_ENCODING,
    "StrFunc_ExcelACTable_UnionLetter_FOREIGN":   StrFunc_ExcelACTable_UnionLetter_FOREIGN,
    "StrFunc_ExcelACTable_UnionLetter_COMPANY":   StrFunc_ExcelACTable_UnionLetter_COMPANY,
    "StrFunc_ExcelACTable_UnionLetter_SCHOOL":    StrFunc_ExcelACTable_UnionLetter_SCHOOL,
    "StrFunc_ExcelACTable_UnionLetter_ORG":       StrFunc_ExcelACTable_UnionLetter_ORG,
    "StrFunc_ExcelACTable_UnionLetter_HOSPITAL":  StrFunc_ExcelACTable_UnionLetter_HOSPITAL,
    "StrFunc_ExcelACTable_UnionLetter_ALLOrg":    StrFunc_ExcelACTable_UnionLetter_ALLOrg,
}

STRATEGY_TABLE = {
    # ── Single-choice param ───────────────────────────────────────────────────
    "StrFuncWithPars_CaseConvert":             StrFuncWithPars_CaseConvert,
    "StrFunc_Capitalize":                      StrFunc_Capitalize,
    "StrFunc_SortWordsWithDictionaryOrder":    StrFunc_SortWordsWithDictionaryOrder,
    # ── List-of-strings param ─────────────────────────────────────────────────
    "StrFuncWithPars_RemoveSpecificSymbol":    StrFuncWithPars_RemoveSpecificSymbol,
    "StrFunc_MultipleKeepLogic":              StrFunc_MultipleKeepLogic,
    "StrFunc_ReplaceInputToNothing":          StrFunc_ReplaceInputToNothing,
    # ── List-of-tuple param ────────────────────────────────────────────────────
    "StrFunc_ReplaceInputToSomething":        StrFunc_ReplaceInputToSomething,
}

# Metadata for the GUI param-dialog builder.
# Format: name -> ("kind", options_or_hint)
#   kind "choice"     — single string; options = list of valid values
#   kind "multi_list" — List[str];     options = checkbox labels
#   kind "list_str"   — List[str];     options = hint string
#   kind "list_pairs" — List[Tuple];   options = hint string
PARAM_META = {
    "StrFuncWithPars_CaseConvert": (
        "choice", ["upper", "lower"],
    ),
    "StrFunc_Capitalize": (
        "choice", ["sentence", "words"],
    ),
    "StrFunc_SortWordsWithDictionaryOrder": (
        "choice", ["ascend", "descend"],
    ),
    "StrFuncWithPars_RemoveSpecificSymbol": (
        "list_str", "Symbols to remove — one per field, e.g.  @  #  !",
    ),
    "StrFunc_MultipleKeepLogic": (
        "multi_list", ["英文", "數字", "符號", "字間空白", "句首末空白"],
    ),
    "StrFunc_ReplaceInputToNothing": (
        "list_str", "Strings to delete — comma-separated, e.g.  Ltd.,  Inc.",
    ),
    "StrFunc_ReplaceInputToSomething": (
        "list_pairs", "Replacement pairs — format  old=new, old2=new2",
    ),
}


class CleaningStrategyAdapter:
    """
    字串清理策略的統一入口。

    - 無參數策略：CleaningStrategyAdapter("StrFunc_Lowercase").run("HELLO")
    - 有參數策略：CleaningStrategyAdapter("StrFuncWithPars_CaseConvert").run("HELLO", pars="lower")
    - 有參數策略：CleaningStrategyAdapter("StrFuncWithPars_RemoveSpecificSymbol").run("h@i", pars=["@"])
    - 有參數策略：CleaningStrategyAdapter("StrFunc_ReplaceInputToSomething").run("hi", pars=[("hi","hello")])

    `pars` should already be the correct Python type for the strategy
    (str / List[str] / List[Tuple[str,str]]) — see PARAM_META for guidance.
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

