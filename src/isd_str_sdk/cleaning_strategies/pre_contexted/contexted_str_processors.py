from enum import auto, Enum
import re

from isd_str_sdk.utils.decorators import enforce_types
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.cleaning_strategies.pre_contexted._actable_str_processor import UnionLetterExcelACTableContext


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

