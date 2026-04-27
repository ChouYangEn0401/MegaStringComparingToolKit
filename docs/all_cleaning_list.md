# 字串清理函式總覽

> 所有清理函式位於 `isd_str_sdk.str_cleaning.strategies`。  
> 使用方式有兩種：**直接實例化**，或透過 **CleaningStrategyAdapter**（僅限無參數策略及有參數策略各自的方式）。

---

## 無參數清理函式（No-param processors）

位於 `strategies/base_str_processors.py`（部分來自 `contexted_str_processors.py`）。

用法：`ClassName("輸入字串").get_result()`

| 函式名稱 | 說明 | 範例輸入 → 輸出 |
|---|---|---|
| `StrFuncNoop` | 不做任何處理，原樣回傳 | `"hello"` → `"hello"` |
| `StrFunc_Lowercase` | 轉為全小寫 | `"HELLO"` → `"hello"` |
| `StrFunc_Uppercase` | 轉為全大寫 | `"hello"` → `"HELLO"` |
| `StrFunc_SentenceCapitalization` | 句首大寫，其餘小寫 | `"hello world"` → `"Hello world"` |
| `StrFunc_WordsCapitalization` | 每個字詞首字母大寫 | `"hello world"` → `"Hello World"` |
| `StrFunc_KeepEnglishLetter` | 只保留英文字母 a-z A-Z | `"abc123!"` → `"abc"` |
| `StrFunc_KeepDigits` | 只保留數字 0-9 | `"abc123def"` → `"123"` |
| `StrFunc_KeepEnglishLetterAndDigits` | 保留英文字母與數字 | `"abc 123!"` → `"abc123"` |
| `StrFunc_KeepEnglishWordsAndSpaces` | 保留英文字母與空白 | `"hello 123!"` → `"hello "` |
| `StrFunc_RemoveAllSymbols` | 移除所有符號，保留字母與數字 | `"hello, world!"` → `"helloworld"` |
| `StrFunc_NormalizeSpacingBetweenWords` | 連續空白（含 tab/換行）縮減為單一空白 | `"hello   world"` → `"hello world"` |
| `StrFunc_NormalizeUnicodeSpacing` | Unicode 空白字元（全形空白等）正規化為半形 | `"hello　world"` → `"hello world"` |
| `StrFunc_StripSymbols` | 去除字串前後空白 | `"  hello  "` → `"hello"` |
| `StrFunc_AscendDictionaryOrder` | 字詞按字典序升序排列 | `"banana apple"` → `"apple banana"` |
| `StrFunc_DescendDictionaryOrder` | 字詞按字典序降序排列 | `"apple banana"` → `"banana apple"` |
| `StrFunc_RemoveHtmlTags` | 移除 HTML 標籤 | `"<b>text</b>"` → `"text"` |
| `StrFunc_CleanEscapedSymbols` | 移除轉義符號（`\"` `\'` `\\`）與引號 | `"\\\"hello\\\""` → `"hello"` |
| `StrFunc_NormalizeParentheses` | ⚠️ 括號正規化（含全形→半形）**已標記為舊版，目前有已知 bug** | `"（hello）"` → `"(hello)"` |
| `StrFunc_NormalizeWhitespace` | 正規化空白（含 Unicode）並去除前後空白 | `"  hello   world  "` → `"hello world"` |
| `StrFunc_KeepEnglishParenthesesAndSpaces` | 保留英文字母、半形括號、空白 | `"hello (world) 123!"` → `"hello (world) "` |
| `StrFunc_ExcelACTable_Base` | Excel 對照表替換基礎類別（需搭配 AC table 子類使用） | — |
| `StrFunc_RemoveUpperCaseStopwords` | 移除全大寫英文停止詞（冠詞、介詞、連詞等） | `"THE University OF Taiwan"` → `"University Taiwan"` |

> **注意**：`StrFunc_NormalizeParentheses` 標記了 `@old_method` decorator，目前 `isd_py_framework_sdk` 的 `OldWarning` 未定義，呼叫時會拋出 `NameError`。

---

## 有參數清理函式（Param processors）

位於 `strategies/param_str_processors.py`。

用法：`ClassName("輸入字串").get_result(參數)`

| 函式名稱 | 參數類型 | 說明 | 範例 |
|---|---|---|---|
| `StrFuncWithPars_CaseConvert` | `str`：`"upper"` / `"大寫"` / `"lower"` / `"小寫"` | 指定大小寫轉換方向 | `.get_result("upper")` → 全大寫 |
| `StrFunc_Capitalize` | `str`：`"sentence"` / `"句子"` / `"words"` / `"每個字詞片段"` | 指定首字母大寫模式 | `.get_result("words")` → 每詞大寫 |
| `StrFuncWithPars_RemoveSpecificSymbol` | `List[str]`：要移除的符號清單 | 移除清單中指定的每個符號 | `.get_result(["@", "#"])` |
| `StrFunc_SortWordsWithDictionaryOrder` | `str`：`"ascend"` / `"升序"` / `"descend"` / `"降序"` | 字詞排序方向 | `.get_result("descend")` |
| `StrFunc_ReplaceInputToNothing` | `List[str]`：要刪除的子字串清單 | 將清單中每個子字串從輸入中刪除 | `.get_result(["and", "or"])` |
| `StrFunc_ReplaceInputToSomething` | `List[Tuple[str, str]]`：`(舊字串, 新字串)` 清單 | 批次替換子字串 | `.get_result([("MIT", "N.T.U.")])` |
| `StrFunc_MultipleKeepLogic` | `List[str]`：保留類型 — `"英文"` `"數字"` `"符號"` `"字間空白"` `"句首末空白"` | 指定要保留的字元類型（OR 組合） | `.get_result(["英文", "數字"])` |

---

## CleaningStrategyAdapter（統一入口）

```python
from isd_str_sdk.str_cleaning import CleaningStrategyAdapter

# 無參數策略
adapter = CleaningStrategyAdapter("StrFunc_Lowercase")
result = adapter.run("HELLO WORLD")           # -> "hello world"

# 有參數策略（傳入 pars）
adapter = CleaningStrategyAdapter("StrFuncWithPars_RemoveSpecificSymbol")
result = adapter.run("h@ello!", pars=["@", "!"])  # -> "hello"
```

---

## StrProcessorChain / StrProcessorsChain（鏈式組合）

```python
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.str_cleaning.strategies.base_str_processors import (
    StrFunc_Lowercase, StrFunc_NormalizeWhitespace, StrFunc_StripSymbols
)

chain = StrProcessorsChain([
    StrFunc_NormalizeWhitespace,
    StrFunc_Lowercase,
    StrFunc_StripSymbols,
])
result = chain.run("  HELLO   World  ")  # -> "hello world"

# 動態新增
chain.add_method(StrFunc_KeepEnglishLetter)
```
