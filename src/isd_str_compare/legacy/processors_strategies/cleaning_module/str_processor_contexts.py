import pandas as pd
from pathlib import Path
from enum import IntFlag, auto
from typing import Dict

from src.lib.processors_strategies.base.processor_base import IStrProcessorContext


class UnionLetterExcelACTableContext(IStrProcessorContext):

    # ========= Enum =========
    class ACTableType(IntFlag):
        STOPWORD = auto()    # 基本權控【停止詞】
        SYMBOL = auto()      # 基本權控【符號統一】
        ENCODING = auto()    # 基本權控【編碼詞統一】
        FOREIGN = auto()     # 基本權控【外語字母統一】
        COMPANY = auto()     # 專案權控【專利權人 - 公司詞】
        SCHOOL = auto()      # 專案權控【校名權控 - 學校詞】
        ORG = auto()         # 專案權控【校名權控 - 機構詞】
        HOSPITAL = auto()    # 專案權控【校名權控 - 醫院詞】

    # ========= 類型對應 =========
    TYPE_MAPPING = {
        "基本權控【停止詞】": ACTableType.STOPWORD,
        "基本權控【符號統一】": ACTableType.SYMBOL,
        "基本權控【編碼詞統一】": ACTableType.ENCODING,
        "基本權控【外語字母統一】": ACTableType.FOREIGN,
        "專案權控【專利權人 - 公司詞】": ACTableType.COMPANY,
        "專案權控【校名權控 - 學校詞】": ACTableType.SCHOOL,
        "專案權控【校名權控 - 機構詞】": ACTableType.ORG,
        "專案權控【校名權控 - 醫院詞】": ACTableType.HOSPITAL,
    }

    # ========= Singleton =========
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self.__class__._initialized:
            return

        super().__init__()
        self._tables: Dict[
            UnionLetterExcelACTableContext.ACTableType,
            Dict[str, str]
        ] = {}

        self._cache: Dict[
            UnionLetterExcelACTableContext.ACTableType,
            Dict[str, str]
        ] = {}

        self._data_init()
        self.__class__._initialized = True

    # ========= Load & Compress =========
    def _data_init(self) -> None:
        df = pd.read_excel(
            Path(__file__).parent / "權控分析_資料前處理_統一詞彙用權控表.xlsx"
        )

        df = df[df["啟用狀態"] == 1]

        # 初始化每種類型的 table
        self._tables = {
            t: {} for t in UnionLetterExcelACTableContext.ACTableType
        }

        for _, row in df.iterrows():
            kind = self.TYPE_MAPPING.get(row["種類"])
            if kind is None:
                continue

            self._tables[kind][row["權控前"]] = row["權控後"]

    # ========= Public API =========
    def get_data(
        self,
        mask: "UnionLetterExcelACTableContext.ACTableType"
    ) -> Dict[str, str]:

        # DP cache
        if mask in self._cache:
            return self._cache[mask]

        merged: Dict[str, str] = {}

        for t in UnionLetterExcelACTableContext.ACTableType:
            if t & mask:
                merged.update(self._tables.get(t, {}))

        self._cache[mask] = merged
        return merged


if __name__ == "__main__":
    print("#### 1")
    ctx = UnionLetterExcelACTableContext()
    print("#### 2")
    # 單一種類
    company = ctx.get_data(
        UnionLetterExcelACTableContext.ACTableType.COMPANY
    )
    print(len(company), company)
    print("#### 3")
    # 多種類混合
    school_org = ctx.get_data(
        UnionLetterExcelACTableContext.ACTableType.SCHOOL
        | UnionLetterExcelACTableContext.ACTableType.ORG
    )
    print(len(school_org), school_org)
    print("#### 4")
    # 全部
    all_types = ctx.get_data(
        sum(UnionLetterExcelACTableContext.ACTableType)
    )
    print(len(all_types), all_types)

