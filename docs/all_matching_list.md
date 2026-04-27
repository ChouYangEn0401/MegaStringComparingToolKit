# 字串比對策略總覽

> 所有比對策略位於 `isd_str_sdk.str_matching.strategies`。  
> 統一入口為 `MatchingStrategyAdapter`，或直接實例化策略類別後呼叫 `.evaluate(context)`。

---

## Context 說明

所有策略的 `evaluate()` 接受一個 `TwoSeriesComparisonContext`：

```python
import pandas as pd
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext

ctx = TwoSeriesComparisonContext(
    row1=pd.Series({"col_a": "MIT"}),
    row2=pd.Series({"col_b": "M.I.T."}),
)
```

`StrategyResult` 回傳物件包含：
- `result.success` — `bool`，是否超過閾值
- `result.score` — `float`，相似度分數（0.0 ~ 1.0，`-1.0` 表示無效輸入）

---

## 精確比對（Exact Matching）

| 策略鍵 | 類別名稱 | 說明 | score 範圍 |
|---|---|---|---|
| `EXACT` | `ExactMatchStrategy` | 嚴格字串相等比對 | `1.0` 或 `0.0` |
| `PREPROCESSED_EXACT` | `PreprocessedExactMatchStrategy` | 透過清理 pipeline 正規化後再做精確比對 | `1.0` 或 `0.0` |

```python
from isd_str_sdk.str_matching.strategies.exact_matching import ExactMatchStrategy

s = ExactMatchStrategy("col_a", "col_b", standard=None)
r = s.evaluate(ctx)
print(r.success, r.score)
```

`PreprocessedExactMatchStrategy` 預設 pipeline（可自訂）：  
停止詞 → 國外名稱 → 小寫 → 機構名稱 → 保留英數 → 大寫 → 字典序排序

---

## 模糊比對（Fuzzy Matching）

| 策略鍵 | 類別名稱 | 底層算法 | 說明 |
|---|---|---|---|
| `FUZZY` | `FuzzyRatioStrategy` | RapidFuzz `fuzz.ratio` | 字元層級編輯距離相似度 |
| `Levenshtein` | `LevenshteinStrategy` | RapidFuzz `Levenshtein.normalized_similarity` | 正規化 Levenshtein 相似度 |
| `JaroWinkler` | `JaroWinklerStrategy` | RapidFuzz `JaroWinkler.normalized_similarity` | 前綴敏感的 Jaro-Winkler 相似度 |

所有模糊策略的 `score` 均為 `0.0 ~ 1.0`，`standard` 為閾值（`score >= standard` 則 `success = True`）。

```python
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy

s = FuzzyRatioStrategy("col_a", "col_b", standard=0.8)
r = s.evaluate(ctx)
print(r.score)   # e.g. 0.727
```

---

## 結構式比對（Structure Matching）

| 策略鍵 | 類別名稱 | 說明 | `standard` 用途 | score 範圍 |
|---|---|---|---|---|
| `IN` | `InStringStrategy` | ⚠️ 已棄用，val2 是否包含於 val1 | — | `1.0` / `0.0` |
| `TwoSideInStringStrategy` | `TwoSideInStringStrategy` | 雙向 in-string 比對，支援 `strategy_mode` | — | `1.0` / `0.0` |
| `TwoSideInWith3WordsStringStrategy` | `TwoSideInWith3WordsStringStrategy` | 雙向 in-string，且子字串長度 ≥ 3 | — | `1.0` / `0.0` |
| `LetterLCS` | `LetterLCSStrategy` | 字元層級 LCS（最長共同子序列） | 相似度閾值 | `0.0 ~ 1.0` |
| `WordLCS` | `WordLCSStrategy` | 字詞層級 LCS | 相似度閾值 | `0.0 ~ 1.0` |
| `JACCARD` | `JaccardStrategy` | 字詞集合 Jaccard 相似度：`|A∩B| / |A∪B|` | 相似度閾值 | `0.0 ~ 1.0` |

### TwoSideInStringStrategy 的 `strategy_mode`

在建立策略時傳入 `strategy_parameters={"strategy_mode": mode}`：

| mode | 行為 |
|---|---|
| `"any"`（預設）| val1 in val2 **或** val2 in val1 |
| `"a_in_b"` | 僅檢查 val1 是否包含於 val2 |
| `"b_in_a"` | 僅檢查 val2 是否包含於 val1 |

```python
from isd_str_sdk.str_matching.strategies.structure_matching import TwoSideInStringStrategy

s = TwoSideInStringStrategy("col_a", "col_b", standard=None, strategy_parameters={"strategy_mode": "a_in_b"})
r = s.evaluate(ctx)
```

### None 輸入行為

`LetterLCSStrategy` 與 `WordLCSStrategy` 若其中一欄為 `None`，則回傳 `StrategyResult(success=False, score=-1.0)`。

---

## NLP 語義比對（NLP Matching）

| 策略鍵 | 類別名稱 | 說明 |
|---|---|---|
| `Embedding` | `EmbeddingSimilarityStrategy` | 使用 sentence-transformers 向量餘弦相似度 |

> ⚠️ **需要** 安裝 `sentence-transformers` 及預訓練模型，預設不安裝。

---

## 邏輯門策略（Logic Gate）

| 策略鍵 | 類別名稱 | 說明 |
|---|---|---|
| `AND` | `AndStrategy` | 所有子策略全部成功才成功 |
| `OR` | `OrStrategy` | 任一子策略成功即成功 |
| `NotAND` | `NotAndStrategy` | AND 結果取反 |
| `NotOR` | `NotOrStrategy` | OR 結果取反 |

> 邏輯門策略使用 `ChildrenValueComparisonContext`，需要包裝子策略結果，適合複合比較樹場景。

---

## 特殊整合策略

| 策略鍵 | 類別名稱 | 說明 |
|---|---|---|
| `PRIS_Tree` | `PRISTreeWalkingStrategy` | PRIS 優先規則決策樹走訪策略 |

---

## 實驗性策略（Undone / On-Dev）

| 策略鍵 | 說明 |
|---|---|
| `NewJACCARDStrategy` | 新版 Jaccard（實驗中） |
| `_on_dev_strategy_` | 開發佔位策略，僅供測試 |

---

## MatchingStrategyAdapter（統一入口）

```python
from isd_str_sdk.str_matching import MatchingStrategyAdapter

adapter = MatchingStrategyAdapter("FUZZY", standard=0.8)
result = adapter.run(str1="hello", str2="helo")
print(result.success, result.score)
```

**`MatchingStrategyAdapter.run()` 參數：**

| 參數 | 型別 | 說明 |
|---|---|---|
| `str1` | `str` | 第一個字串 |
| `str2` | `str` | 第二個字串 |
| `split_segment` | `str` | 多值分割符號（進階，預設 `" ； "`） |
| `strategy_mode` | `str` | 策略模式（進階，預設 `"amount_mode"`） |
| `extra_debug_print` | `bool` | 是否輸出除錯資訊（預設 `False`） |

---

## 直接使用策略類別（進階）

不透過 adapter，直接使用策略類別：

```python
import pandas as pd
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching.strategies.structure_matching import JaccardStrategy

ctx = TwoSeriesComparisonContext(
    row1=pd.Series({"a": "apple banana cherry"}),
    row2=pd.Series({"b": "apple banana mango"}),
)
s = JaccardStrategy("a", "b", standard=0.5)
r = s.evaluate(ctx)
print(r.score)    # 2/4 = 0.5
print(r.success)  # True
```
