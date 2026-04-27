# 字串比對策略總覽

本文件依難易度由淺入深介紹三層 API。**新手直接看 Level 1 就夠用。**

---

## ⭐ Level 1 — 最簡單（兩個 list 丟進去，直接拿結果）

```python
from isd_str_sdk.str_matching import match

results = match(
    list1=["MIT", "Stanford", "Apple Inc."],
    list2=["M.I.T.", "Stanford University", "Apple"],
    strategy="FUZZY",   # 策略名稱（見下方策略速查表）
    threshold=0.5,      # 低於此分數的配對不會出現
)

# results 是一個 list of (str1, best_match, score)
for s1, s2, score in results:
    print(f"{s1!r}  →  {s2!r}  (score={score})")
```

**輸出：**
```
'MIT'        →  'M.I.T.'                (score=0.6667)
'Stanford'   →  'Stanford University'  (score=0.7273)
'Apple Inc.' →  'Apple'               (score=0.8)
```

`match()` 的規則：對 `list1` 中每個字串，從 `list2` 挑 **score 最高**的那個，只要 `score >= threshold` 就加入結果。

### 策略速查（Level 1 常用）

| 策略名稱 | 適合情境 | score 說明 |
|---|---|---|
| `"FUZZY"` | 一般模糊比對、容許打字錯誤 | 字元相似度 0.0–1.0 |
| `"Levenshtein"` | 字元增刪改的距離，比 FUZZY 嚴格 | 0.0–1.0 |
| `"JaroWinkler"` | 前綴相同的字串加分，適合人名/縮寫 | 0.0–1.0 |
| `"JACCARD"` | 字詞集合重疊，順序不重要 | 0.0–1.0 |
| `"LetterLCS"` | 字元最長共同子序列，適合亂序縮寫 | 0.0–1.0 |
| `"WordLCS"` | 字詞最長共同子序列 | 0.0–1.0 |
| `"EXACT"` | 完全一致才算成功 | `1.0` 或 `0.0` |
| `"PREPROCESSED_EXACT"` | 先正規化（去停止詞/大小寫/符號）再精確比對 | `1.0` 或 `0.0` |

也可以直接傳**策略類別**：

```python
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy

results = match(["MIT"], ["M.I.T."], strategy=FuzzyRatioStrategy, threshold=0.5)
```

---

## 🥈 Level 2 — 單對字串比對（隱藏 context，仍保留策略概念）

```python
from isd_str_sdk.str_matching import MatchingStrategyAdapter

adapter = MatchingStrategyAdapter("FUZZY", standard=0.8)
result = adapter.run("hello world", "hello wrold")

print(result.success)  # True  (score >= 0.8 → 成功)
print(result.score)    # ~0.9
```

`StrategyResult` 物件包含：
- `.success` — `bool`，`score >= standard` 為 `True`
- `.score` — `float`，相似度分數

### 需要 `standard` 的情境

`standard` 是門檻：`score >= standard` 時 `result.success == True`。

```python
adapter = MatchingStrategyAdapter("JACCARD", standard=0.5)
r = adapter.run("apple banana cherry", "apple banana mango")
# score = 2/4 = 0.5 → success = True
```

### 傳策略類別（IDE 補全友善）

```python
from isd_str_sdk.str_matching.strategies.structure_matching import JaccardStrategy

adapter = MatchingStrategyAdapter(JaccardStrategy, standard=0.5)
r = adapter.run("apple banana", "apple cherry")
print(r.score)   # 0.333
```

### 有額外參數的策略（`special_params`）

`TwoSideInStringStrategy` 需要指定比對方向：

```python
from isd_str_sdk.str_matching.strategies.structure_matching import TwoSideInStringStrategy

adapter = MatchingStrategyAdapter(
    TwoSideInStringStrategy,
    standard=None,
    strategy_parameters={"strategy_mode": "a_in_b"},  # val1 是否包含於 val2
)
r = adapter.run("hello", "hello world")
print(r.success)  # True
```

`strategy_mode` 選項：

| mode | 行為 |
|---|---|
| `"any"`（預設）| val1 ⊂ val2 **或** val2 ⊂ val1 其一成立 |
| `"a_in_b"` | 只看 val1 是否包含於 val2 |
| `"b_in_a"` | 只看 val2 是否包含於 val1 |

---

## 🥉 Level 3 — 直接操作策略類別（專家 / 客製化）

適合需要整合到 pipeline、批次 DataFrame 處理、或開發新策略的場景。

### 基本用法

```python
import pandas as pd
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching.strategies.structure_matching import JaccardStrategy

ctx = TwoSeriesComparisonContext(
    row1=pd.Series({"col_a": "apple banana cherry"}),
    row2=pd.Series({"col_b": "apple banana mango"}),
)

s = JaccardStrategy("col_a", "col_b", standard=0.5)
r = s.evaluate(ctx)

print(r.score)    # 0.5   (|{apple,banana}| / |{apple,banana,cherry,mango}|)
print(r.success)  # True
print(r.run(ctx)) # 等同 r.success（.run() 是 .evaluate() 的 bool 包裝）
```

### Context 說明

`TwoSeriesComparisonContext` 是一個 dataclass，包裝兩個 `pd.Series`，策略透過欄位名稱取值：

```python
TwoSeriesComparisonContext(
    row1=pd.Series({"col_a": "值A"}),  # 第一個字串
    row2=pd.Series({"col_b": "值B"}),  # 第二個字串
)
```

初始化策略時傳入的 `df1` / `df2` 就是這兩個欄位名稱：

```python
JaccardStrategy(df1="col_a", df2="col_b", standard=0.5)
```

### None 輸入的行為

`LetterLCSStrategy` 與 `WordLCSStrategy` 若任一欄為 `None`，回傳 `StrategyResult(success=False, score=-1.0)`。

---

## 全策略清單

### 精確比對

| 策略鍵 | 類別 | 說明 |
|---|---|---|
| `EXACT` | `ExactMatchStrategy` | 嚴格字串相等 |
| `PREPROCESSED_EXACT` | `PreprocessedExactMatchStrategy` | 正規化 pipeline 後精確比對 |

`PREPROCESSED_EXACT` 預設正規化流程：停止詞 → 國外名稱 → 小寫 → 機構名稱 → 保留英數 → 大寫 → 字典序排序

### 模糊比對

| 策略鍵 | 類別 | 底層 |
|---|---|---|
| `FUZZY` | `FuzzyRatioStrategy` | RapidFuzz `fuzz.ratio` |
| `Levenshtein` | `LevenshteinStrategy` | `Levenshtein.normalized_similarity` |
| `JaroWinkler` | `JaroWinklerStrategy` | `JaroWinkler.normalized_similarity` |

### 結構式比對

| 策略鍵 | 類別 | 說明 | score |
|---|---|---|---|
| `IN` | `InStringStrategy` | ⚠️ 已棄用 | `1.0/0.0` |
| `TwoSideInStringStrategy` | `TwoSideInStringStrategy` | 雙向 in-string，支援 mode | `1.0/0.0` |
| `TwoSideInWith3WordsStringStrategy` | `TwoSideInWith3WordsStringStrategy` | 雙向 in-string 且長度 ≥ 3 | `1.0/0.0` |
| `LetterLCS` | `LetterLCSStrategy` | 字元 LCS | `0.0~1.0` |
| `WordLCS` | `WordLCSStrategy` | 字詞 LCS | `0.0~1.0` |
| `JACCARD` | `JaccardStrategy` | 集合 Jaccard 相似度 | `0.0~1.0` |

### 其他

| 策略鍵 | 說明 |
|---|---|
| `Embedding` | sentence-transformers 語義相似度（需另行安裝） |
| `PRIS_Tree` | PRIS 決策樹走訪策略 |
| `AND` / `OR` / `NotAND` / `NotOR` | 邏輯門策略（接受子策略結果組合） |
| `NewJACCARDStrategy` | 實驗性新版 Jaccard |

