# 字串清理函式總覽

本文件由淺入深介紹所有清理函式。**初學者看前兩節就夠。**

---

## ⭐ 快速上手 — 一行搞定最常用清理

```python
from isd_str_sdk.str_cleaning import CleaningStrategyAdapter

# 空白正規化（最常用）
CleaningStrategyAdapter("StrFunc_NormalizeWhitespace").run("  Hello   World  ")
# -> "Hello World"

# 轉小寫
CleaningStrategyAdapter("StrFunc_Lowercase").run("HELLO WORLD")
# -> "hello world"

# 移除 HTML 標籤
CleaningStrategyAdapter("StrFunc_RemoveHtmlTags").run("<b>hello</b> <i>world</i>")
# -> "hello world"

# 只保留英文字母與數字
CleaningStrategyAdapter("StrFunc_KeepEnglishLetterAndDigits").run("abc 123!@#")
# -> "abc123"
```

---

## 🧹 全部無參數清理函式

用法：`CleaningStrategyAdapter("函式名稱").run("輸入字串")`  
或直接：`StrFunc_Xxx("輸入字串").get_result()`

### 大小寫

| 函式名稱 | 說明 | 輸入 → 輸出 |
|---|---|---|
| `StrFuncNoop` | 不做任何處理 | `"hello"` → `"hello"` |
| `StrFunc_Lowercase` | 全部轉小寫 | `"HELLO World"` → `"hello world"` |
| `StrFunc_Uppercase` | 全部轉大寫 | `"hello world"` → `"HELLO WORLD"` |
| `StrFunc_SentenceCapitalization` | 句首大寫，其餘小寫 | `"HELLO WORLD"` → `"Hello world"` |
| `StrFunc_WordsCapitalization` | 每個字詞首字母大寫 | `"hello world foo"` → `"Hello World Foo"` |

### 字元過濾（只留下你要的）

| 函式名稱 | 說明 | 輸入 → 輸出 |
|---|---|---|
| `StrFunc_KeepEnglishLetter` | 只留英文字母 | `"abc 123!"` → `"abc"` |
| `StrFunc_KeepDigits` | 只留數字 | `"abc123def456"` → `"123456"` |
| `StrFunc_KeepEnglishLetterAndDigits` | 只留英文字母與數字 | `"abc 123!"` → `"abc123"` |
| `StrFunc_KeepEnglishWordsAndSpaces` | 只留英文字母與空白 | `"hello 123!"` → `"hello "` |
| `StrFunc_KeepEnglishParenthesesAndSpaces` | 只留英文字母、半形括號、空白 | `"hello (world) 123!"` → `"hello (world) "` |
| `StrFunc_RemoveAllSymbols` | 移除所有符號，保留字母與數字 | `"hello, world!"` → `"helloworld"` |

### 空白處理

| 函式名稱 | 說明 | 輸入 → 輸出 |
|---|---|---|
| `StrFunc_StripSymbols` | 去除字串前後空白 | `"  hello  "` → `"hello"` |
| `StrFunc_NormalizeSpacingBetweenWords` | 連續空白（含 tab/換行）縮為單一空白 | `"hello\t\nworld"` → `"hello world"` |
| `StrFunc_NormalizeUnicodeSpacing` | Unicode 空白字元（全形空白等）轉半形 | `"hello　world"` → `"hello world"` |
| `StrFunc_NormalizeWhitespace` | **最推薦**：Unicode 空白正規化 + 去前後空白（以上三者合體） | `"  hello　 world  "` → `"hello world"` |

### 特殊文字處理

| 函式名稱 | 說明 | 輸入 → 輸出 |
|---|---|---|
| `StrFunc_RemoveHtmlTags` | 移除 HTML 標籤 | `"<b>text</b>"` → `"text"` |
| `StrFunc_CleanEscapedSymbols` | 移除轉義符號與引號（`\"` `\'` `\\`） | `"\\\"hello\\\""` → `"hello"` |
| `StrFunc_RemoveUpperCaseStopwords` | 移除全大寫停止詞（THE / OF / AND…） | `"THE University OF Taiwan"` → `"University Taiwan"` |
| `StrFunc_NormalizeParentheses` | ⚠️ 全形括號→半形（目前有已知 bug，建議避免使用） | `"（hello）"` → `"(hello)"` |

### 排序

| 函式名稱 | 說明 | 輸入 → 輸出 |
|---|---|---|
| `StrFunc_AscendDictionaryOrder` | 字詞按字典序升序排列 | `"banana apple cherry"` → `"apple banana cherry"` |
| `StrFunc_DescendDictionaryOrder` | 字詞按字典序降序排列 | `"apple banana cherry"` → `"cherry banana apple"` |

### 進階：Excel 權控對照表替換（pre_contexted 模組）

這組函式讀取專案內附 Excel（`權控分析_資料前處理_統一詞彙用權控表.xlsx`），按「類型遮罩」批次替換字詞。  
替換模式有兩種：**WORD**（以空白切分後整詞比對）、**LETTER**（逐字元比對）。

| 函式名稱 | 替換模式 | 說明 |
|---|---|---|
| `StrFunc_ExcelACTable_UnionLetter_STOPWORD`  | WORD   | 基本權控：停止詞替換 |
| `StrFunc_ExcelACTable_UnionLetter_SYMBOL`    | LETTER | 基本權控：符號統一（逐字元） |
| `StrFunc_ExcelACTable_UnionLetter_ENCODING`  | WORD   | 基本權控：編碼詞統一 |
| `StrFunc_ExcelACTable_UnionLetter_FOREIGN`   | LETTER | 基本權控：外語字母統一（逐字元） |
| `StrFunc_ExcelACTable_UnionLetter_COMPANY`   | WORD   | 專案權控：公司名詞統一 |
| `StrFunc_ExcelACTable_UnionLetter_SCHOOL`    | WORD   | 專案權控：學校名詞統一 |
| `StrFunc_ExcelACTable_UnionLetter_ORG`       | WORD   | 專案權控：機構詞統一 |
| `StrFunc_ExcelACTable_UnionLetter_HOSPITAL`  | WORD   | 專案權控：醫院詞統一 |
| `StrFunc_ExcelACTable_UnionLetter_ALLOrg`    | WORD   | 所有組織詞統一（SCHOOL+ORG+HOSPITAL+COMPANY 合集） |

> **Excel 檔位置**：`src/isd_str_sdk/str_cleaning/strategies/pre_contexted/權控分析_資料前處理_統一詞彙用權控表.xlsx`  
> 欄位要求：`啟用狀態`（1=啟用）、`種類`（類型名稱）、`權控前`（原詞）、`權控後`（替換詞）。  
> 此模組使用 Singleton 載入，效能佳；首次呼叫後快取結果。

```python
# 使用 Adapter（推薦）
CleaningStrategyAdapter("StrFunc_ExcelACTable_UnionLetter_STOPWORD").run("The University OF Taiwan")
# -> "University Taiwan"  （停止詞被替換為空字串後重新 join）

# 直接呼叫
StrFunc_ExcelACTable_UnionLetter_ALLOrg("Stanford University").get_result()
```

---

## 🔗 鏈式組合（StrProcessorsChain）

多個清理步驟可以串接，**按照陣列順序依序執行**：

```python
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.str_cleaning.strategies.base_str_processors import (
    StrFunc_NormalizeWhitespace,
    StrFunc_Lowercase,
    StrFunc_KeepEnglishWordsAndSpaces,
)

chain = StrProcessorsChain([
    StrFunc_NormalizeWhitespace,      # 步驟 1：空白正規化
    StrFunc_Lowercase,                # 步驟 2：轉小寫
    StrFunc_KeepEnglishWordsAndSpaces,# 步驟 3：只留英文與空白
])

result = chain.run("  Hello 123 World!  ")
# -> "hello  world"
```

動態加入步驟：

```python
chain.add_method(StrFunc_StripSymbols)
```

---

## ⚙️ 有參數清理函式（Param processors）

這類函式需要在 `get_result()` 時傳入參數，`CleaningStrategyAdapter` 也支援透過 `pars=` 傳遞。

用法：`ClassName("輸入字串").get_result(參數)`

### 大小寫轉換

```python
StrFuncWithPars_CaseConvert("hello").get_result("upper")  # -> "HELLO"
StrFuncWithPars_CaseConvert("HELLO").get_result("小寫")   # -> "hello"
# 可用值："upper" / "大寫"、"lower" / "小寫"

StrFunc_Capitalize("hello world").get_result("words")    # -> "Hello World"
StrFunc_Capitalize("hello world").get_result("句子")     # -> "Hello world"
# 可用值："sentence" / "句子"、"words" / "每個字詞片段"
```

### 移除指定符號

```python
StrFuncWithPars_RemoveSpecificSymbol("h@e#llo!").get_result(["@", "#", "!"])
# -> "hello"

# 透過 Adapter
CleaningStrategyAdapter("StrFuncWithPars_RemoveSpecificSymbol").run("h@llo!", pars=["@", "!"])
# -> "hllo"
```

### 字詞排序

```python
StrFunc_SortWordsWithDictionaryOrder("banana apple cherry").get_result("ascend")
# -> "apple banana cherry"
StrFunc_SortWordsWithDictionaryOrder("apple banana cherry").get_result("降序")
# -> "cherry banana apple"
# 可用值："ascend" / "升序"、"descend" / "降序"
```

### 子字串替換

```python
# 刪除指定子字串
StrFunc_ReplaceInputToNothing("the quick brown fox").get_result(["quick ", "brown "])
# -> "the fox"

# 替換為指定字串
StrFunc_ReplaceInputToSomething("foo bar baz").get_result([("foo", "one"), ("bar", "two")])
# -> "one two baz"
```

### 複合保留邏輯

根據語意類型保留字元，支援 OR 組合：

```python
StrFunc_MultipleKeepLogic("hello 123!").get_result(["英文"])           # -> "hello"
StrFunc_MultipleKeepLogic("hello 123!").get_result(["數字"])           # -> "123"
StrFunc_MultipleKeepLogic("hello 123!").get_result(["英文", "數字"])   # -> "hello123"
StrFunc_MultipleKeepLogic("hello 123!").get_result(["英文", "字間空白"]) # -> "hello"
# 可用類型："英文" / "數字" / "符號" / "字間空白" / "句首末空白"
```

### 有參數函式速查表

| 函式名稱 | 參數類型 | 說明 |
|---|---|---|
| `StrFuncWithPars_CaseConvert` | `str` | 指定大小寫方向 |
| `StrFunc_Capitalize` | `str` | 指定首字母大寫模式 |
| `StrFuncWithPars_RemoveSpecificSymbol` | `List[str]` | 移除指定符號清單 |
| `StrFunc_SortWordsWithDictionaryOrder` | `str` | 指定排序方向 |
| `StrFunc_ReplaceInputToNothing` | `List[str]` | 刪除指定子字串清單 |
| `StrFunc_ReplaceInputToSomething` | `List[Tuple[str, str]]` | 批次替換子字串 |
| `StrFunc_MultipleKeepLogic` | `List[str]` | 指定保留字元類型（OR 組合） |

---

## 🏗️ 底層架構（給開發者）

所有清理函式繼承自兩個基底類別：

| 基底類別 | 用途 | 實作方法 |
|---|---|---|
| `StrProcessorBase` | 無參數處理器 | `_handle(self) -> str` |
| `StrProcessorWithParamBase` | 有參數處理器 | `_handle(self, param) -> str` |

呼叫方式統一為 `instance.get_result()` 或 `instance.get_result(param)`。

新增自訂清理函式並登錄到 Adapter：

```python
from isd_str_sdk.base.IStrProcessor import StrProcessorBase
from isd_str_sdk.utils.decorators import enforce_types

class MyCustomCleaner(StrProcessorBase):
    @enforce_types(str, str)
    def _handle(self) -> str:
        return self.input_str.replace("foo", "bar")

# 登錄到 NOPARS_STRATEGY_TABLE（str_cleaning/__init__.py）
NOPARS_STRATEGY_TABLE["MyCustomCleaner"] = MyCustomCleaner
```

