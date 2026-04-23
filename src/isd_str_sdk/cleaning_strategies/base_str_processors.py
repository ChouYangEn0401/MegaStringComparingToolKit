"""
這裡是最原始的字串清理功能，透過繼承最基礎的 StrProcessorBase 實作出來的。
基本上就是單一功能，很類似 simplest command pattern 的實作，沒有任何參數化的功能。
這些功能的實作相對簡單，主要是為了提供一些最基本的字串處理功能，並且作為更複雜的 StrProcessorWithParamBase 的基礎組件。
"""

import re
import regex
from isd_py_framework_sdk.decorators import old_method

from src.isd_str_sdk.utils.decorators import enforce_types
from src.isd_str_sdk.base.IStrProcessor import StrProcessorBase


class StrFuncNoop(StrProcessorBase):
    """不做任何處理，直接回傳原字串。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str
    
class StrFunc_Lowercase(StrProcessorBase):
    """將字串轉換為全小寫。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str.lower()
class StrFunc_Uppercase(StrProcessorBase):
    """將字串轉換為全大寫。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str.upper()
    
class StrFunc_SentenceCapitalization(StrProcessorBase):
    """將字串的首字母大寫，其餘字母小寫。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str.capitalize()
class StrFunc_WordsCapitalization(StrProcessorBase):
    """將字串的每個字詞片段的首字母大寫，其餘字母小寫。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        return ' '.join([s.capitalize() for s in self.input_str.split(" ")])

class StrFunc_KeepEnglishLetter(StrProcessorBase):
    """保留字串中的英文字母 a-Z，移除其他字元。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留英文字母 a-z A-Z，移除其他字元
        return ''.join(re.findall(r'[a-zA-Z]+', self.input_str))
class StrFunc_KeepDigits(StrProcessorBase):
    """保留字串中的數字字元 0-9，移除其他字元。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留數字字元 0-9，移除其他字元
        return ''.join(re.findall(r'\d+', self.input_str))
class StrFunc_KeepEnglishLetterAndDigits(StrProcessorBase):
    """保留字串中的英文字母 a-z A-Z 與數字字元 0-9，移除其他字元。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留英文字母 a-z A-Z 與數字字元 0-9，移除其他字元
        return ''.join(re.findall(r'[a-zA-Z0-9]+', self.input_str))
class StrFunc_KeepEnglishWordsAndSpaces(StrProcessorBase):
    """保留字串中的英文字母 a-z A-Z 與空白字元，移除其他字元。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 保留英文字母 a-z A-Z 與空白字元，移除其他字元
        return ''.join(re.findall(r'[a-zA-Z ]+', self.input_str))
class StrFunc_RemoveAllSymbols(StrProcessorBase):
    """移除字串中的所有符号，只保留英文字母和数字。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 移除符號，只保留英文字母與數字
        # 這裡用 \w 匹配字母、數字和底線，然後移除底線
        filtered = re.findall(r'\w+', self.input_str)
        # 把底線移除
        return ''.join(filtered).replace('_', '')
    
class StrFunc_NormalizeSpacingBetweenWords(StrProcessorBase):
    """將字串中連續多個空白字元（包括全形空白、半形空白、tab、換行等）替換成一個半形空白。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 將連續多個空白字元替換成一個空白
        return re.sub(r'\s+', ' ', self.input_str)
class StrFunc_NormalizeUnicodeSpacing(StrProcessorBase):
    """將字串中連續多個 Unicode 空白字元（包括全形空白、半形空白、tab、換行等）替換成一個半形空白。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 將所有 Unicode 空白（\p{Zs}）、控制字元（\p{Cc}）、格式字符（\p{Cf}）等連續替換成單一空白
        return regex.sub(r'[\p{Z}\p{Cc}\p{Cf}]+', ' ', self.input_str)
class StrFunc_StripSymbols(StrProcessorBase):
    """去除字串前後所有空白符號（空白、tab、換行等）。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        # 去除字串前後所有空白符號（空白、tab、換行等）
        return self.input_str.strip()
    
class StrFunc_AscendDictionaryOrder(StrProcessorBase):
    """將字串中的單詞按照字典順序升序排序。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        words = self.input_str.split()
        words.sort()  # 預設升序排序
        return ' '.join(words)
class StrFunc_DescendDictionaryOrder(StrProcessorBase):
    """將字串中的單詞按照字典順序降序排序。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        words = self.input_str.split()
        words.sort(reverse=True)  # 降序排序
        return ' '.join(words)
    
class StrFunc_RemoveHtmlTags(StrProcessorBase):
    """移除字串中的 HTML 標籤（例如 <b>、</b>、<br> 等）。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        return re.sub(r'</?[^>]+>', '', self.input_str)
    
class StrFunc_CleanEscapedSymbols(StrProcessorBase):
    """將字串中的轉義符號（例如 \\'、\\"、\\\\ 等）還原成原本的符號。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        text = self.input_str
        text = text.replace("\\'", "'")
        text = text.replace('\\"', '"')
        text = text.replace('\\\\', '\\')
        text = text.replace('\"', '')
        text = text.replace('\'', '')
        return text

@old_method("This function have a better version, currently, and may be replaced in the future.")
class StrFunc_NormalizeParentheses(StrProcessorBase):
    """將字串中的全形括號、方括號、大括號等統一替換為半形括號。例如：將（替換為(，）替換為)，[替換為(，]替換為)，{替換為(，}替換為)。"""
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
    """將字串中連續多個空白字元（包括全形空白、半形空白、tab、換行等）替換成一個半形空白，並去除字串前後的空白。"""
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
    """保留字串中的英文字母、半形括號和空白字元，移除其他字元。"""
    @enforce_types(str, str)
    def _handle(self) -> str:
        return ''.join(re.findall(r'[a-zA-Z() ]+', self.input_str))

