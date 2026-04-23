from enum import auto, Enum

from src.lib.processors_strategies.cleaning_module.str_processor_contexts import UnionLetterExcelACTableContext


def callable_function1():
    print("功能1 執行")

def callable_function2(param):
    print(f"功能2 執行，參數是: {param}")

def callable_function3(param):
    print(f"功能3 執行，參數是: {param}")

import re
import regex
from typing import List
import string

from src.lib.processors_strategies.base.processor_base import StrProcessorWithListStrParam, StrProcessorWithListTupleStrParam
from src.lib.processors_strategies.base.processor_base import StrProcessorBase, StrProcessorWithParamBase
from src.lib.processors_strategies.base.processor_base import enforce_types, enforce_types_with_pars_check
from src.hyper_framework.exceptions.exceptions import WrongOptionException


class StrFuncNoop(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str
class StrFuncWithPars_CaseConvert(StrProcessorWithParamBase):
    @enforce_types(str, str)
    def _handle(self, mode: str) -> str:
        if mode in ['upper', "大寫"]:
            return StrFunc_Uppercase(self.input_str).get_result()
        elif mode in ['lower', "小寫"]:
            return StrFunc_Lowercase(self.input_str).get_result()
        else:
            raise WrongOptionException(mode)
class StrFunc_Lowercase(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str.lower()
class StrFunc_Uppercase(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str.upper()
class StrFunc_Capitalize(StrProcessorWithParamBase):
    @enforce_types(str, str)
    def _handle(self, mode: str) -> str:
        if mode in ['sentence', "句子"]:
            return StrFunc_SentenceCapitalization(self.input_str).get_result()
        elif mode in ['words', "每個字詞片段"]:
            return StrFunc_WordsCapitalization(self.input_str).get_result()
        else:
            raise WrongOptionException(mode)
class StrFunc_MultipleKeepLogic(StrProcessorWithListStrParam):
    def _handle_runner(self, keep_options: list[str]) -> str:
        keep_chars = ""
        if "英文" in keep_options:
            keep_chars += "a-zA-Z"
        if "數字" in keep_options:
            keep_chars += "0-9"
        if "符號" in keep_options:
            # 用 string.punctuation 或自定義符號集
            keep_chars += re.escape(string.punctuation)
        if "字間空白" in keep_options:
            keep_chars += " "

        # 句首末空白是否保留？
        keep_edge_spaces = "句首末空白" in keep_options

        # 組合 regex pattern 來保留字元
        pattern = f"[{keep_chars}]"
        filtered_str = ''.join(re.findall(pattern, self.input_str))

        # 是否保留原始句首末空白
        if keep_edge_spaces:
            # 把原本的前後空白補回來（根據原始輸入）
            left_space = self.input_str[:len(self.input_str) - len(self.input_str.lstrip())]
            right_space = self.input_str[len(self.input_str.rstrip()):]
            filtered_str = f"{left_space}{filtered_str.strip()}{right_space}"
        else:
            filtered_str = filtered_str.strip()
        return filtered_str
class StrFunc_SentenceCapitalization(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str.capitalize()
class StrFunc_WordsCapitalization(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return ' '.join([s.capitalize() for s in self.input_str.split(" ")])
class StrFunc_KeepEnglishLetter(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留英文字母 a-z A-Z，移除其他字元
        return ''.join(re.findall(r'[a-zA-Z]+', self.input_str))
class StrFunc_KeepEnglishWordsAndSpaces(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留英文字母 a-z A-Z，移除其他字元
        return ''.join(re.findall(r'[a-zA-Z ]+', self.input_str))
class StrFunc_KeepDigits(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留數字字元 0-9，移除其他字元
        return ''.join(re.findall(r'\d+', self.input_str))
class StrFunc_KeepEnglishLetterAndDigits(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留英文字母 a-z A-Z 與數字字元 0-9，移除其他字元
        return ''.join(re.findall(r'[a-zA-Z0-9]+', self.input_str))
class StrFunc_RemoveAllSymbols(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 移除符號，只保留英文字母與數字
        # 這裡用 \w 匹配字母、數字和底線，然後移除底線
        filtered = re.findall(r'\w+', self.input_str)
        # 把底線移除
        return ''.join(filtered).replace('_', '')
class StrFuncWithPars_RemoveSpecificSymbol(StrProcessorWithParamBase):
    @enforce_types_with_pars_check(str, str, list)
    def _handle(self, params: List[str]) -> str:
        # 假設 params 是要去除的符號清單，比如 ['!', '@', '#']
        symbols_to_remove = set(str(p) for p in params)
        # 逐字檢查 input_str，去掉指定符號
        result = ''.join(ch for ch in self.input_str if ch not in symbols_to_remove)
        return result
class StrFunc_NormalizeSpacingBetweenWords(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 將連續多個空白字元替換成一個空白
        return re.sub(r'\s+', ' ', self.input_str)
class StrFunc_NormalizeUnicodeSpacing(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 將所有 Unicode 空白（\p{Zs}）、控制字元（\p{Cc}）、格式字符（\p{Cf}）等連續替換成單一空白
        return regex.sub(r'[\p{Z}\p{Cc}\p{Cf}]+', ' ', self.input_str)
class StrFunc_StripSymbols(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 去除字串前後所有空白符號（空白、tab、換行等）
        return self.input_str.strip()
class callable_func_spellcheck(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_pinyin_check(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_pinyin_check_2(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_spellcheck_2(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_org_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_company_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_school_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_location_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_foreign_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_special_word_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_encoding_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class callable_func_other_standardize(StrProcessorBase):
    def _handle(self) -> str:
        pass
class StrFunc_SortWordsWithDictionaryOrder(StrProcessorWithParamBase):
    @enforce_types(str, str)
    def _handle(self, mode: str) -> str:
        if mode in ['ascend', "升序"]:
            return StrFunc_AscendDictionaryOrder(self.input_str).get_result()
        elif mode in ['descend', "降序"]:
            return StrFunc_DescendDictionaryOrder(self.input_str).get_result()
        else:
            raise WrongOptionException(f"Invalid mode: {mode}")
class StrFunc_AscendDictionaryOrder(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        words = self.input_str.split()
        words.sort()  # 預設升序排序
        return ' '.join(words)
class StrFunc_DescendDictionaryOrder(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        words = self.input_str.split()
        words.sort(reverse=True)  # 降序排序
        return ' '.join(words)
class StrFunc_RemoveHtmlTags(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return re.sub(r'</?[^>]+>', '', self.input_str)
class StrFunc_CleanEscapedSymbols(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        text = self.input_str
        text = text.replace("\\'", "'")
        text = text.replace('\\"', '"')
        text = text.replace('\\\\', '\\')
        text = text.replace('\"', '')
        text = text.replace('\'', '')
        return text
class StrFunc_ReplaceInputToNothing(StrProcessorWithListStrParam):
    def _handle_runner(self, replace_string: list[str]) -> str:
        # replace_string 是使用者希望直接刪掉的文字
        result_ = self.input_str
        for a in replace_string:
            result_ = result_.replace(a, "")
        return result_
class StrFunc_ReplaceInputToSomething(StrProcessorWithListTupleStrParam):
    def _handle_runner(self, replace_string: list[tuple[str, str]]) -> str:
        # replace_string 是使用者希望直接刪掉的文字
        print(replace_string, type(replace_string))
        result_ = self.input_str
        for (a, b) in replace_string:
            result_ = result_.replace(a, b)
        return result_
class StrFunc_NormalizeParentheses(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        text = self.input_str

        # 所有需要被視為「開括號」的符號
        OPEN_PARENS = ['(', '（', '[', '［', '{', '｛', '<', '＜']
        # 所有需要被視為「閉括號」的符號
        CLOSE_PARENS = [')', '）', ']', '］', '}', '｝', '>', '＞']

        result = []
        for ch in text:
            if ch in OPEN_PARENS:
                result.append('(')
            elif ch in CLOSE_PARENS:
                result.append(')')
            else:
                result.append(ch)

        return ''.join(result)
class StrFunc_NormalizeWhitespace(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        text = self.input_str
        # 將所有 Unicode 空白、制表符、換行等全部視為空白
        # \p{Z} = 所有 Unicode 空白（含全形空白）
        # \s  = whitespace（含 tab）
        # Cc = 控制字符
        text = regex.sub(r'[\p{Z}\s\p{Cc}]+', ' ', text)
        return text.strip()
class StrFunc_KeepEnglishParenthesesAndSpaces(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return ''.join(re.findall(r'[a-zA-Z() ]+', self.input_str))
# class StrFunc_UnionByExcelACTable(StrProcessorWithContextBase[IStrProcessorContext]):
class StrFunc_UnionByExcelACTable(StrProcessorWithParamBase):
    @enforce_types_with_pars_check(str, str, UnionLetterExcelACTableContext.ACTableType)
    def _handle(self, mask: "UnionLetterExcelACTableContext.ACTableType") -> str:  # ### TEMP: untested ###
        UnionLetterExcelACTableContext().get_data(mask)
        ...
        return None
class StrFunc_ExcelACTable_Base(StrProcessorBase):
    class ReplaceUnit(Enum):
        WORD = auto()
        LETTER = auto()

    ACTABLE_MASK = None              # 子類指定
    REPLACE_UNIT = ReplaceUnit.WORD  # 預設 word

    @enforce_types(str, str)
    def _handle(self) -> str:
        ctx = UnionLetterExcelACTableContext()
        mapping = ctx.get_data(self.ACTABLE_MASK)

        if not mapping:
            return self.input_str

        if self.REPLACE_UNIT == StrFunc_ExcelACTable_Base.ReplaceUnit.LETTER:
            return self._replace_by_letter(mapping)

        return self._replace_by_word(mapping)

    # ========= Replace strategies =========

    def _replace_by_letter(self, mapping: dict[str, str]) -> str:
        result = self.input_str
        for src, tgt in mapping.items():
            result = result.replace(src, tgt)
        return result

    def _replace_by_word(self, mapping: dict[str, str]) -> str:
        """
        將 input_str 拆成 word segment（以空白分隔），
        每個 word 如果在 mapping 裡就替換。
        """
        words = self.input_str.split()  # 以空白切分
        new_words = [mapping.get(word, word) for word in words]  # 對每個 segment 做 mapping
        return " ".join(new_words)

class StrFunc_ExcelACTable_UnionLetter_STOPWORD(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.STOPWORD
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.WORD
class StrFunc_ExcelACTable_UnionLetter_SYMBOL(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.SYMBOL
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.LETTER
class StrFunc_ExcelACTable_UnionLetter_ENCODING(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.ENCODING
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.WORD
class StrFunc_ExcelACTable_UnionLetter_FOREIGN(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.FOREIGN
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.LETTER
class StrFunc_ExcelACTable_UnionLetter_COMPANY(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.COMPANY
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.WORD
class StrFunc_ExcelACTable_UnionLetter_SCHOOL(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.SCHOOL
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.WORD
class StrFunc_ExcelACTable_UnionLetter_ORG(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.ORG
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.WORD
class StrFunc_ExcelACTable_UnionLetter_HOSPITAL(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = UnionLetterExcelACTableContext.ACTableType.HOSPITAL
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.WORD
class StrFunc_ExcelACTable_UnionLetter_ALLOrg(StrFunc_ExcelACTable_Base):
    ACTABLE_MASK = (
        UnionLetterExcelACTableContext.ACTableType.SCHOOL |
        UnionLetterExcelACTableContext.ACTableType.ORG |
        UnionLetterExcelACTableContext.ACTableType.HOSPITAL |
        UnionLetterExcelACTableContext.ACTableType.COMPANY
    )
    REPLACE_UNIT = StrFunc_ExcelACTable_Base.ReplaceUnit.WORD

class StrFunc_RemoveUpperCaseStopwords(StrProcessorBase):
    """
    移除字串中所有全大寫的常用停止詞、冠詞、介系詞等。
    """
    # 擴充至極限的常用大寫停止詞清單
    STOPWORDS = [
        # 冠詞 (Articles)
        "A", "AN", "THE",
        # 連詞 (Conjunctions)
        "AND", "BUT", "OR", "NOR", "FOR", "YET", "SO", "BOTH", "EITHER", "NEITHER",
        # 介系詞 (Prepositions)
        "ABOUT", "ABOVE", "AFTER", "AGAINST", "ALONG", "AMID", "AMONG", "AROUND", "AT",
        "BEFORE", "BEHIND", "BELOW", "BENEATH", "BESIDE", "BETWEEN", "BEYOND", "BY",
        "DOWN", "DURING", "EXCEPT", "FOR", "FROM", "IN", "INSIDE", "INTO", "LIKE",
        "NEAR", "OF", "OFF", "ON", "ONTO", "OUT", "OVER", "PAST", "SINCE", "THROUGH",
        "THROUGHOUT", "TO", "TOWARD", "UNDER", "UNTIL", "UP", "UPON", "WITH", "WITHIN", "WITHOUT",
        # 代名詞 (Pronouns)
        "I", "YOU", "HE", "SHE", "IT", "WE", "THEY", "THEM", "THEIR", "OUR", "YOUR", "HIS", "HER",
        "US", "MY", "MINE", "YOURS", "OURS", "THEIRS", "ME", "HIM", "ITS",
        # 助動詞/繫動詞 (Auxiliary/Linking Verbs)
        "AM", "IS", "ARE", "WAS", "WERE", "BE", "BEEN", "BEING", "HAVE", "HAS", "HAD", "DO", "DOES", "DID",
        "CAN", "COULD", "SHALL", "SHOULD", "WILL", "WOULD", "MAY", "MIGHT", "MUST",
        # 其他常用虛詞 (Others)
        "THESE", "THOSE", "THIS", "THAT", "SUCH", "NO", "NOT", "ONLY", "VERY", "JUST", "THAN"
    ]

    @enforce_types(str, str)
    def _handle(self) -> str:
        # 使用 \b 確保精確匹配單字
        # 使用 set(self.STOPWORDS) 確保唯一性並提升效能
        pattern = r'\b(' + '|'.join(set(self.STOPWORDS)) + r')\b'

        # 1. 執行替換
        # 2. 用 split() 切開後重新 join()，這能處理：
        #    - 刪除後產生的雙空格
        #    - 句首或句尾產生的空格
        result = re.sub(pattern, '', self.input_str)
        return ' '.join(result.split())



# ### mvp ### #
# ### REFACTOR: mvp simple one, we may need a much more stable and clean ###
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
    def __init__(self, strategy_name: str):
        self.strategy = (NOPARS_STRATEGY_TABLE[strategy_name] or NOPARS_STRATEGY_TABLE[strategy_name])

    def run(self, input_str: str, pars: dict = None):
        assert type(input_str) == str, "`input_str` Is Not String Type !!"

        result = self.strategy(input_str).get_result()
        return result
# ### REFACTOR: mvp simple one, we may need a much more stable and clean ###


if __name__ == "__main__":
    str_ = "aaaa"
    print(StrFunc_Lowercase(str_).get_result())
    print(StrFunc_Uppercase(str_).get_result())
    # print(StrFunc_Capitalize(99).get_result())

