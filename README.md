# ISD String Comparing Toolkit

輕量的 Python 字串處理函式庫，提供可組合的**字串清理**處理器與多種**字串比對**策略，廣泛使用於 ISD 系列專案中。

- 安裝需求：Python ≥ 3.11，依賴 `rapidfuzz`、`regex`、`pandas`（見 `pyproject.toml`）。

```bash
pip install .
# 或開發模式
pip install -e .
```

---

## 模組結構

| 模組 | 用途 |
|---|---|
| `isd_str_sdk.str_cleaning` | 字串清理處理器與 `CleaningStrategyAdapter` |
| `isd_str_sdk.str_matching` | 字串比對策略與 `MatchingStrategyAdapter` |
| `isd_str_sdk.base` | 抽象基底類別（`Strategy`、`StrProcessorBase`） |
| `isd_str_sdk.core` | 比對 Context 物件（`TwoSeriesComparisonContext`） |
| `isd_str_sdk.utils` | 工具函式（decorator、型別檢查、例外） |
| `isd_str_sdk.TDD` | 策略開發用測試 harness |

---

## 字串清理

> 完整函式清單與說明：[docs/all_cleaning_list.md](docs/all_cleaning_list.md)

### 透過 CleaningStrategyAdapter（最簡單）

```python
from isd_str_sdk.str_cleaning import CleaningStrategyAdapter

# 無參數策略
cleaner = CleaningStrategyAdapter("StrFunc_NormalizeWhitespace")
print(cleaner.run("  Hello   WORLD  "))       # -> "Hello WORLD"

# 有參數策略
cleaner = CleaningStrategyAdapter("StrFuncWithPars_RemoveSpecificSymbol")
print(cleaner.run("h@llo!", pars=["@", "!"]))  # -> "hllo"
```

### 直接使用處理器類別

```python
from isd_str_sdk.str_cleaning.strategies.base_str_processors import StrFunc_Lowercase

result = StrFunc_Lowercase("HELLO WORLD").get_result()
print(result)  # -> "hello world"
```

### 鏈式組合（StrProcessorsChain）

```python
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.str_cleaning.strategies.base_str_processors import (
    StrFunc_Lowercase,
    StrFunc_NormalizeWhitespace,
    StrFunc_KeepEnglishWordsAndSpaces,
)

chain = StrProcessorsChain([
    StrFunc_NormalizeWhitespace,
    StrFunc_Lowercase,
    StrFunc_KeepEnglishWordsAndSpaces,
])
print(chain.run("  Hello 123 World!  "))  # -> "hello  world"
```

---

## 字串比對

> 完整策略清單與說明：[docs/all_matching_list.md](docs/all_matching_list.md)

### 透過 MatchingStrategyAdapter（最簡單）

```python
from isd_str_sdk.str_matching import MatchingStrategyAdapter

# 模糊比對，閾值 0.8
adapter = MatchingStrategyAdapter("FUZZY", standard=0.8)
result = adapter.run(str1="hello world", str2="hello wrold")
print(result.success, result.score)  # True, ~0.9

# Jaccard 集合相似度
adapter = MatchingStrategyAdapter("JACCARD", standard=0.5)
result = adapter.run(str1="apple banana cherry", str2="apple banana mango")
print(result.score)   # 0.5
```

### 直接使用策略類別

```python
import pandas as pd
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching.strategies.fuzzy_matching import JaroWinklerStrategy

ctx = TwoSeriesComparisonContext(
    row1=pd.Series({"a": "MIT"}),
    row2=pd.Series({"b": "MIT University"}),
)
s = JaroWinklerStrategy("a", "b", standard=0.85)
r = s.evaluate(ctx)
print(r.success, r.score)
```

---

## 測試

```bash
pytest tests/ -q
# 預期：185 passed, 4 xfailed
```

4 件 `xfailed` 測試為 `StrFunc_NormalizeParentheses`，原因是 `isd_py_framework_sdk` 的 `@old_method` decorator 存在已知 bug（`OldWarning` 未定義），已在測試中標記為預期失敗。

---

## 開發者說明

### 新增清理處理器

繼承 `StrProcessorBase`（無參數）或 `StrProcessorWithParamBase`（有參數），實作 `_handle()` 方法，再於 `str_cleaning/__init__.py` 的 `NOPARS_STRATEGY_TABLE` 或 `STRATEGY_TABLE` 登錄。

### 新增比對策略

繼承 `Strategy[TwoSeriesComparisonContext]`，實作 `evaluate(context)` 回傳 `StrategyResult`，再於 `str_matching/adapters.py` 的 `STRATEGY_TABLE` 登錄。

### TDD harness

```python
from isd_str_sdk.TDD.run_strategy_tests import run_strategy_test
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy

tests = [
    ("MIT", "MIT", True),
    ("Apple", "Orange", False),
]
run_strategy_test(FuzzyRatioStrategy, tests, print_mode="wrong_answer")
```

---

Authors: 周暘恩, Anthony Chou — MIT License
