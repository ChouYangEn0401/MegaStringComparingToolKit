# ISD String Comparing Toolkit

輕量的 Python 字串處理函式庫，提供可組合的**字串清理**處理器與多種**字串比對**策略，廣泛使用於 ISD 系列專案中。

- 安裝需求：Python ≥ 3.11，依賴 `rapidfuzz`、`regex`、`pandas`（見 `pyproject.toml`）。

```bash
pip install .        # 一般安裝
pip install -e .     # 開發模式
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
依賴：Python ≥ 3.11、`rapidfuzz`、`regex`、`pandas`

---

## 字串清理

> 完整函式清單與說明：[docs/all_cleaning_list.md](docs/all_cleaning_list.md)

### 透過 CleaningStrategyAdapter（最簡單的用法）

```python
from isd_str_sdk.str_cleaning import CleaningStrategyAdapter

CleaningStrategyAdapter("StrFunc_NormalizeWhitespace").run("  Hello   World  ")
# -> "Hello World"

CleaningStrategyAdapter("StrFunc_Lowercase").run("HELLO WORLD")
# -> "hello world"

CleaningStrategyAdapter("StrFunc_RemoveHtmlTags").run("<b>hello</b>")
# -> "hello"
```

### 常用函式速查

| 函式名稱 | 效果 |
|---|---|
| `StrFunc_NormalizeWhitespace` | 正規化空白 + 去前後空白（**最常用**） |
| `StrFunc_Lowercase` / `StrFunc_Uppercase` | 大小寫轉換 |
| `StrFunc_KeepEnglishLetterAndDigits` | 只保留英數字元 |
| `StrFunc_RemoveHtmlTags` | 移除 HTML 標籤 |
| `StrFunc_RemoveUpperCaseStopwords` | 移除全大寫停止詞（THE / OF / AND…） |
| `StrFunc_AscendDictionaryOrder` | 字詞升序排列 |

### 鏈式組合多個步驟

```python
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.str_cleaning.strategies.base_str_processors import (
    StrFunc_NormalizeWhitespace, StrFunc_Lowercase, StrFunc_KeepEnglishWordsAndSpaces
)

chain = StrProcessorsChain([
    StrFunc_NormalizeWhitespace,
    StrFunc_Lowercase,
    StrFunc_KeepEnglishWordsAndSpaces,
])
chain.run("  HELLO 123 WORLD!  ")
# -> "hello  world"
```

---

## 字串比對

> 完整策略清單與範例：[docs/all_matching_list.md](docs/all_matching_list.md)

### Level 1 — 兩個 list，直接配對

```python
from isd_str_sdk.str_matching import match

results = match(
    list1=["MIT", "Stanford", "Apple Inc."],
    list2=["M.I.T.", "Stanford University", "Apple"],
    strategy="FUZZY",
    threshold=0.5,
)

for s1, s2, score in results:
    print(f"{s1!r}  ->  {s2!r}  ({score})")
# 'MIT'        ->  'M.I.T.'              (0.6667)
# 'Stanford'   ->  'Stanford University' (0.7273)
# 'Apple Inc.' ->  'Apple'              (0.8)
```

`strategy` 可用值：`"FUZZY"` / `"EXACT"` / `"Levenshtein"` / `"JaroWinkler"` / `"JACCARD"` / `"LetterLCS"` / `"WordLCS"` / `"PREPROCESSED_EXACT"`

也可以直接傳策略類別（有 IDE 補全）：

```python
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy
results = match(["MIT"], ["M.I.T."], strategy=FuzzyRatioStrategy, threshold=0.5)
```

### Level 2 — 單對字串比對

```python
from isd_str_sdk.str_matching import MatchingStrategyAdapter

adapter = MatchingStrategyAdapter("JACCARD", standard=0.5)
r = adapter.run("apple banana cherry", "apple banana mango")
print(r.success)  # True  (score 0.5 >= standard 0.5)
print(r.score)    # 0.5
```

`standard` 是閾值：`score >= standard` 時 `r.success == True`。

---

## 測試

```bash
pytest tests/ -q
# 185 passed, 4 xfailed
```

4 件 `xfailed` 是 `StrFunc_NormalizeParentheses`（已知的 `isd_py_framework_sdk` 相依 bug，測試正確標記為預期失敗）。

## NLP 額外套件（可選）

`EmbeddingSimilarityStrategy` 依賴 `sentence-transformers`（該套件會進一步安裝如 `torch`、`transformers` 等大型依賴），因此本專案將其列為 extras（可選套件），預設安裝不會自動包含。若你需要執行基於 embeddings 的比對策略，請在安裝時顯式要求 `nlp` extras。

安裝範例：

- 開發（可編輯安裝）：

```powershell
pip install -e .[nlp]
```

- 從本地 wheel 一次安裝並包含 extras（請替換路徑與檔名）：

```powershell
pip install "isd-str-sdk[nlp] @ file:///C:/Users/629/Desktop/周暘恩/Modules/MegaStringComparingToolKit/dist/isd_str_sdk-<version>-py3-none-any.whl"
```

- 若套件已上架 PyPI，直接安裝帶 extras：

```bash
pip install "isd-str-sdk[nlp]"
```

如果只安裝 wheel（`pip install path\\to\\file.whl`）而沒有指定 extras，pip 不會自動安裝可選依賴。你也可以先安裝主套件，再另外安裝 `sentence-transformers`：

```bash
pip install sentence-transformers
```

注意：`sentence-transformers` 通常會安裝 `torch`（體積大），安裝時間較久，且可能需要為 GPU/CPU 選擇合適版本；在需要時可使用 conda 或官方安裝指引以獲得更穩定的體驗。

---

## 依賴說明（isd-py-framework-sdk）

本專案依賴 `isd-py-framework-sdk`（v0.4.5）。若你的環境無法自動取得該套件，可從下列位置下載 wheel：

https://github.com/ChouYangEn0401/ISDPythonFrameworkSDK/releases/download/v0.4.5/isd_py_framework_sdk-0.4.5-py3-none-any.whl

通常情況下，使用 `pip install .` 或安裝本專案的 wheel 時，安裝流程會自動安裝相依套件（`pyproject.toml` / `requirements.txt` 已包含相依的公開 URL），因此一般使用者不需額外處理。

## 開發者指引

新增清理函式：繼承 `StrProcessorBase`（無參數）或 `StrProcessorWithParamBase`（有參數），實作 `_handle()`，於 `str_cleaning/__init__.py` 的 `NOPARS_STRATEGY_TABLE` / `STRATEGY_TABLE` 登錄。

新增比對策略：繼承 `Strategy[TwoSeriesComparisonContext]`，實作 `evaluate(context) -> StrategyResult`，於 `str_matching/adapters.py` 的 `STRATEGY_TABLE` 登錄。

TDD harness（快速驗證策略）：

```python
from isd_str_sdk.TDD.run_strategy_tests import run_strategy_test
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy

run_strategy_test(FuzzyRatioStrategy, [
    ("MIT", "MIT", True),
    ("Apple", "Orange", False),
], print_mode="wrong_answer")
```

架構詳細說明請見 [docs/all_cleaning_list.md](docs/all_cleaning_list.md) 與 [docs/all_matching_list.md](docs/all_matching_list.md)。

---

Authors: 周暘恩, Anthony Chou — MIT License
