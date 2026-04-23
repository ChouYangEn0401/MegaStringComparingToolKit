from src.isd_str_sdk.str_cleaning.strategies.base_str_processors import *


class StrFuncWithPars_CaseConvert(StrProcessorWithParamBase):
    """根據參數選擇轉換為全大寫或全小寫。"""
    @enforce_types(str, str)
    def _handle(self, mode: str) -> str:
        if mode in ['upper', "大寫"]:
            return StrFunc_Uppercase(self.input_str).get_result()
        elif mode in ['lower', "小寫"]:
            return StrFunc_Lowercase(self.input_str).get_result()
        else:
            raise WrongOptionException(mode)
        
class StrFunc_Capitalize(StrProcessorWithParamBase):
    """根據參數選擇句子式或每個字詞片段式的首字母大寫。"""
    @enforce_types(str, str)
    def _handle(self, mode: str) -> str:
        if mode in ['sentence', "句子"]:
            return StrFunc_SentenceCapitalization(self.input_str).get_result()
        elif mode in ['words', "每個字詞片段"]:
            return StrFunc_WordsCapitalization(self.input_str).get_result()
        else:
            raise WrongOptionException(mode)
            
class StrFunc_MultipleKeepLogic(StrProcessorWithListStrParam):
    """根據參數選擇要保留哪些類型的字元，例如英文、數字、符號、字間空白等。"""
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

class StrFuncWithPars_RemoveSpecificSymbol(StrProcessorWithParamBase):
    """根據參數選擇要去除的特定符號。"""
    @enforce_types_with_pars_check(str, str, list)
    def _handle(self, params: List[str]) -> str:
        # 假設 params 是要去除的符號清單，比如 ['!', '@', '#']
        symbols_to_remove = set(str(p) for p in params)
        # 逐字檢查 input_str，去掉指定符號
        result = ''.join(ch for ch in self.input_str if ch not in symbols_to_remove)
        return result

class StrFunc_SortWordsWithDictionaryOrder(StrProcessorWithParamBase):
    """根據參數選擇以字典序升序或降序排列字串中的字詞片段。"""
    @enforce_types(str, str)
    def _handle(self, mode: str) -> str:
        if mode in ['ascend', "升序"]:
            return StrFunc_AscendDictionaryOrder(self.input_str).get_result()
        elif mode in ['descend', "降序"]:
            return StrFunc_DescendDictionaryOrder(self.input_str).get_result()
        else:
            raise WrongOptionException(f"Invalid mode: {mode}")
        
class StrFunc_ReplaceInputToNothing(StrProcessorWithListStrParam):
    """根據參數選擇要去除的特定子串列表，將字串中的這些子串全部刪除。"""
    def _handle_runner(self, replace_string: list[str]) -> str:
        # replace_string 是使用者希望直接刪掉的文字
        result_ = self.input_str
        for a in replace_string:
            result_ = result_.replace(a, "")
        return result_
    
class StrFunc_ReplaceInputToSomething(StrProcessorWithListTupleStrParam):
    """
    根據參數選擇要替換的特定子串列表，將字串中的這些子串替換為使用者指定的其他子串。
    例如，使用者提供 [("old1", "new1"), ("old2", "new2")]，
    則會將字串中的 "old1" 替換為 "new1"，"old2" 替換為 "new2"。
    """
    def _handle_runner(self, replace_string: list[tuple[str, str]]) -> str:
        # replace_string 是使用者希望直接刪掉的文字
        print(replace_string, type(replace_string))
        result_ = self.input_str
        for (a, b) in replace_string:
            result_ = result_.replace(a, b)
        return result_

