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

### 空值處理（NullPolicy）

> 0.4.6 起適用於**所有**兩欄比對策略：EXACT / PREPROCESSED_EXACT / FUZZY / Levenshtein / JaroWinkler / JACCARD / LetterLCS / WordLCS / Embedding / IN 系列。

**為什麼需要它**：pandas 讀 Excel 空格得到 `float('nan')`，舊版只擋 `None`，`"nan"` 會被當成字串進 tokenizer，
兩個空格就以 1.0 分「配對成功」。NullPolicy 在算分前統一攔截。

**什麼算 null**

| 類別 | 預設 | 開關 |
|---|---|---|
| `None`、`float('nan')`、`numpy.nan`、`pd.NA`、`pd.NaT` | 永遠是 null | — |
| `""` 與只有空白的字串 | 不是 | `empty_is_null=True` |
| `"nan"`、`"none"`、`"n/a"`、`"-"` 等文字 | 不是（它們只是字串） | `null_like={"nan","none",...}`（不分大小寫、會 strip） |

**三種模式**

| `null_mode` | 任一側 null | 兩側皆 null | 適用 |
|---|---|---|---|
| `fail`（預設） | `success=False, score=-1.0` | 同左 | 權控比對：缺資料不該配對 |
| `match_if_both` | `success=False, score=-1.0` | `success=True, score=1.0` | 「空白跟空白能不能比」→ 可以 |
| `as_text` | 不攔截 | 不攔截 | 0.4.5 以前的 legacy 行為；要逐字比對 `"nan"` 字面時 |

**三種給法**

```python
from isd_str_sdk.str_matching import NullPolicy, NullMode, MatchingStrategyAdapter
from isd_str_sdk.str_matching.strategies.structure_matching import WordLCSStrategy

# 1. 物件
WordLCSStrategy("a", "b", standard=0.9, null_policy=NullPolicy(mode=NullMode.MATCH_IF_BOTH, empty_is_null=True))

# 2. strategy_parameters dict（GUI / JSON 設定走這條；值可以是字串）
WordLCSStrategy("a", "b", standard=0.9, strategy_parameters={
    "null_mode": "match_if_both", "empty_is_null": "true", "null_like": "nan, none, n/a",
})

# 3. Level 2 adapter（**special_params 就是建構子 kwargs；adapter.run 只接受 str）
MatchingStrategyAdapter("WordLCS", standard=0.9, strategy_parameters={"null_like": "nan, n/a"})
```

`null_score`（預設 `-1.0`）可改成 `0.0`，讓「null 失敗」與「比對 0 分」在報表上不區分。

**行為變更提醒（0.4.5 → 0.4.6）**

* `EXACT`：`None == None` / 兩個 NaN 以前會成功（score 1），現在預設失敗。要舊行為用 `match_if_both`。
* `FUZZY` / `JACCARD`：`None` 以前會變成 `"None"` 字串參與比對，現在預設失敗。
* `Levenshtein` / `JaroWinkler` / `TwoSideIn*`：`None` 以前被 `or ""` 變空字串（兩個 None → 1.0），現在預設失敗。
* `LetterLCS` / `WordLCS`：`None` 行為不變（本來就 -1.0）；**新增** NaN / pd.NA 也 -1.0。
* 空字串 `""` 的既有行為全部不變（除非開 `empty_is_null`）。

`NullPolicy.param_meta()` 回傳與 `STRATEGY_PARAM_META` 同 schema 的欄位描述。
`get_strategy_param_meta(name)` 對所有兩欄策略會**自動附上**這三個欄位（策略自己的參數排前面；logic gate 不附），
所以用這個 registry 動態產生設定 UI 的程式，不改一行就能讓使用者自己決定空值怎麼算。
只想拿策略本身的參數：`get_strategy_param_meta(name, include_null_policy=False)`。

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

