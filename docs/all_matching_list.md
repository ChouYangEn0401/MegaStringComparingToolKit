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
| `"PREPROCESSED_EXACT"` | 先正規化（去停止詞/大小寫/符號）再精確比對；空格不分、**詞序要一樣** | `1.0` 或 `0.0` |
| `"SPACING_ORDER_FREE_EXACT"` | 0.4.9：空格與詞序都不分（`PREPROCESSED_EXACT` 的超集） | `1.0` 或 `0.0` |
| `"REGEX_EXTRACT_EXACT"` / `"REGEX_RULE"` / `"REGEX_NAMED_GROUPS"` / `"REGEX_NORMALIZED_EXACT"` | 0.4.9：regex 當比對規則（見下方「Regex 比對」） | 見各款 |

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

> 0.4.6 起適用於**所有**兩欄比對策略：EXACT / PREPROCESSED_EXACT / FUZZY / Levenshtein / JaroWinkler / JACCARD / LetterLCS / WordLCS / Embedding / IN 系列；0.4.9 新增的 SPACING_ORDER_FREE_EXACT 與四款 REGEX_* 也一樣。

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
| `SPACING_ORDER_FREE_EXACT` | `SpacingAndOrderFreeExactStrategy` | 0.4.9：空格與詞序都不分，`PREPROCESSED_EXACT` 的超集 |
| `REGEX_EXTRACT_EXACT` | `RegexExtractExactStrategy` | 0.4.9：regex 擷取後比對 |
| `REGEX_NORMALIZED_EXACT` | `RegexNormalizedExactStrategy` | 0.4.9：regex 規則表正規化後比對 |
| `REGEX_RULE` | `RegexRuleStrategy` | 0.4.9：一欄是 regex 規則 |

`PREPROCESSED_EXACT` 預設正規化流程：停止詞 → 國外名稱 → 小寫 → 機構名稱 → 保留英數 → 大寫 → 字典序排序
（最後一步因為「保留英數」已拿掉空白而不生效，實際是「空格不分、詞序要一樣」；要詞序也不分用 `SPACING_ORDER_FREE_EXACT`）

### 空格與詞序都不分（0.4.9 新增）`SPACING_ORDER_FREE_EXACT`

類別：`SpacingAndOrderFreeExactStrategy`（`strategies/hybrid_matching.py`）。是 `PREPROCESSED_EXACT` 的**超集**：
它比得中的，這一款一定也比得中。

**為什麼要另外做一款、不直接改 `PREPROCESSED_EXACT`**：`PREPROCESSED_EXACT` 的第 7 步（字典序排序）
因為第 5 步（只留英數）已經把空白拿掉、整串只剩一個詞，**永遠不生效**，所以它其實是「空格不分、詞序要一樣」。
把排序移到前面也不行——空格不同的那幾組比不比得中會變成看單詞的字母順序（下表第 4 欄）。
而 `PREPROCESSED_EXACT` 是下游（pyDMS 校名權控 20 段階梯的第 1 段）逐格守著的產出，行為不能動，所以另做一款。

| 左 | 右 | `PREPROCESSED_EXACT` | 只把排序移到前面 | `SPACING_ORDER_FREE_EXACT` |
|---|---|---|---|---|
| Tsinghua University | Tsing Hua University | ✅ | ❌（`HUATSINGUNIVERSITY` ≠ `TSINGHUAUNIVERSITY`） | ✅ |
| National Taiwan University | Taiwan National University | ❌ | ✅ | ✅ |
| Univ Tokyo | Tokyo Univ | ❌ | ✅ | ✅ |
| Hong Kong University | University Hong Kong | ❌ | ✅ | ✅ |
| National Cheng Kung University | National ChengKung University | ✅ | ✅（剛好字母順序相鄰） | ✅ |
| Kyoto University | KYOTO UNIVERSITY. | ✅ | ✅ | ✅ |
| University of Tokyo | Tokyo University | ❌ | ❌ | ❌（停止詞表只把 of 統一成 OF、不刪，多一個詞） |

**做法（暴力列舉空格）**

1. 前四步照 `PREPROCESSED_EXACT`（停止詞 → 國外符號 → 小寫 → 機構詞），以空白切成單詞、每個單詞只留英數、轉大寫 → `w1 … wn`。
2. n−1 個空隙各自「留或拿掉」，共 2^(n−1) 種組合；拿掉的空隙把兩邊的詞黏起來。
3. 每種組合照字母排序、用空白接起來 ＝ 一個代表字串；一個名字得到一組代表字串。
4. 兩個名字有任何一個代表字串相同 → `success=True, score=1`；否則 `score=0`。

「空隙全部拿掉」那一組就是 `PREPROCESSED_EXACT` 的正規化結果，所以超集成立（兩邊都正規化成空字串——例如整串中文——也照舊算中）。

| 參數 | 預設 | 說明 |
|---|---|---|
| `max_gaps` | `12` | 空隙數超過它的名字只用兩種代表字串：「全部拿掉」與「全部留著＋排序」。超集與詞序不分仍成立，「部分空格不同」不保證 |
| `pre_processors` | 前四步 | 取代前處理（keyword，GUI 不列） |

**批次（group / 反查表）**：不要 N×M 兩兩比——

```python
from isd_str_sdk.str_matching.strategies.hybrid_matching import SpacingAndOrderFreeExactStrategy

s = SpacingAndOrderFreeExactStrategy("a", "b", None)
s.representatives("Tsing Hua University")      # frozenset({'HUA TSING UNIVERSITY', 'TSINGHUA UNIVERSITY', ...})
s.build_index(names)                           # {代表字串: [位置, ...]} — 共用代表字串的名字就是同一個 group
s.batch_match(left_names, right_names)         # [(i, j), ...]，跟逐對 evaluate() 的 success 逐格相同（含 NullPolicy）
```

每個名字的代表字串有快取（pickle 時不帶）。這一款**不在任何預設階梯裡**，用不用由呼叫端決定。

### Regex 比對（0.4.9 新增）

以前 regex 只藏在清理步驟內部（寫死的樣式）。這四款讓 regex 變成**使用者設定的比對規則**
（`strategies/regex_matching.py`，用 `regex` 套件：相容 `re` 語法，另支援 `\p{L}` 與逾時）。

| 策略鍵 | 類別 | 一句話 | score |
|---|---|---|---|
| `REGEX_EXTRACT_EXACT` | `RegexExtractExactStrategy` | 兩邊各用 regex 擷取一段（DOI、年份、ISSN、郵遞區號…），比擷取出來的 | `1/0`；`all_set` 為 Jaccard |
| `REGEX_RULE` | `RegexRuleStrategy` | 一欄放 regex 規則、另一欄放文字，規則比得中就算中（權控規則表） | `1/0`；壞規則 `-1` |
| `REGEX_NAMED_GROUPS` | `RegexNamedGroupsStrategy` | 具名群組把字串拆成欄位，逐欄比，`children` 帶每一欄的結果 | 相同欄位比例 |
| `REGEX_NORMALIZED_EXACT` | `RegexNormalizedExactStrategy` | 一張「樣式 → 取代」規則表依序套到兩邊，再完全比對 | `1/0` |

共通：參數可以當 keyword 也可以放 `strategy_parameters`（GUI 送字串也收）；`ignore_case` 讓樣式與擷取值的比較都不分大小寫；
樣式在**建構時**編譯，寫錯直接 `ValueError`（`REGEX_RULE` 例外：規則來自資料，壞的那一格判不中、不讓整批停）；
空值先過 NullPolicy。`get_strategy_param_meta()` 都有登記（自己的參數在前、NullPolicy 三欄在後）。

**`REGEX_EXTRACT_EXACT`**

| 參數 | 預設 | 說明 |
|---|---|---|
| `pattern` | 必填 | 擷取用的 regex |
| `right_pattern` | 同 `pattern` | 右欄用不同的樣式 |
| `group` | `0` | 群組號碼或具名群組名字（兩個樣式都要有） |
| `extract_mode` | `first` | `first` 第一個／`all_list` 全部且順序要同／`all_set` 全部當集合、score＝Jaccard、`score >= standard` 算中（`standard` 非數字＝1.0） |
| `ignore_case` | `False` | |

任一邊什麼都沒擷取到 → `success=False, score=0.0`（兩邊都沒有也一樣）。

```python
s = RegexExtractExactStrategy("a", "b", None, pattern=r"10\.\d{4,9}/\S+", ignore_case=True)
# "Smith 2020, doi:10.1000/ABC.1"  vs  "https://doi.org/10.1000/abc.1"  → 中
```

**`REGEX_RULE`**

| 參數 | 預設 | 說明 |
|---|---|---|
| `rule_side` | `right` | 哪一欄放規則 |
| `match_mode` | `search` | `search` 任一處／`fullmatch` 整串／`match` 從開頭 |
| `ignore_case` | `False` | |
| `strip_rule` | `True` | 規則先去前後空白（Excel 儲存格尾巴的空白） |
| `regex_timeout` | `1.0` 秒 | 單格比對上限，擋 `(a|aa)+$` 這種災難性回溯；`0`／`none` 不設限 |
| `on_invalid` | `fail` | 規則不合法或逾時：`fail` → `success=False, score=-1.0`；`raise` → `ValueError` |

空的規則一律不中（空 regex 會比中所有字串）。編譯過的規則會快取。

**`REGEX_NAMED_GROUPS`**

| 參數 | 預設 | 說明 |
|---|---|---|
| `pattern` | 必填 | 至少一個具名群組 |
| `right_pattern` | 同 `pattern` | 欄位名字要對得上 |
| `groups` | 共有的全部 | 只比哪幾個（逗號分隔） |
| `match_mode` | `search` | 同上 |
| `ignore_case` | `False` | |

整個樣式沒比中 → `score=0.0`；兩邊都沒值的群組不列入計分、只有一邊有值算不同；
`score = 相同數 / 計分數`，`score >= standard` 算中（`standard` 非數字＝1.0）。`children` 照 `groups` 順序，
每欄一個 `StrategyResult`（不列入計分的 `score=None`）。

```python
s = RegexNamedGroupsStrategy("a", "b", 0.7,
        pattern=r"(?P<year>\d{4})\s+Vol\s*(?P<vol>\d+)(?:\((?P<no>\d+)\))?")
s.evaluate(ctx("2021 Vol 12(3)", "2021 Vol 12(4)"))   # score=2/3, success=False（期數對不上）
```

**`REGEX_NORMALIZED_EXACT`**

| 參數 | 預設 | 說明 |
|---|---|---|
| `rules` | 必填 | `[(pattern, replacement), ...]`，或一行一條的字串 `pattern => replacement`（沒有 `=>`＝刪掉；空行、`#` 開頭略過）。可用 `\1`／`\g<name>`，**依序**套用 |
| `collapse_whitespace` | `True` | 套完後連續空白縮成一個、去前後空白 |
| `ignore_case` | `False` | |

```python
s = RegexNormalizedExactStrategy("a", "b", None, rules=r"""
\bUniv\b\.? => University
\bNatl\b\.? => National
""")
s.normalize("Natl. Taiwan Univ.")   # 'National Taiwan University'
```

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

### 邏輯閘（0.4.7 修正）

0.4.6 以前 `AND` / `OR`（以及繼承它們的 `NotAND` / `NotOR`）的 `evaluate()` 讀
`context.children` / `context.original_context`，但 `ChildrenValueComparisonContext`
只有 `children_results`，一執行就 `AttributeError`。0.4.7 起只讀 `children_results`：

```python
from isd_str_sdk.core.contexts import ChildrenValueComparisonContext
from isd_str_sdk.str_matching import STRATEGY_TABLE

ctx = ChildrenValueComparisonContext(children_results=[True, False])  # 子節點先跑完，結果交給閘
STRATEGY_TABLE["AND"]().evaluate(ctx)   # success=False, score=0.5
STRATEGY_TABLE["OR"]().evaluate(ctx)    # success=True,  score=1.0
```

| 閘 | success | score | 沒有子結果時 |
|---|---|---|---|
| `AND` | 全部為真 | 為真的比例 | success=True, score=0.0 |
| `OR` | 任一為真 | 任一為真 → 1.0，否則 0.0 | success=False, score=0.0 |
| `NotAND` / `NotOR` | `AND` / `OR` 翻轉 | 與 `AND` / `OR` 相同 | 翻轉 |

`children_results` 的每一項可以是 `bool` 或 `StrategyResult`（取 `.success`）；回傳的
`StrategyResult.children` 為 `None`。語意與 ACA / pyDMS 的 `sdk_compat.py`
（`FixedAndStrategy` 等）逐一相同，下游升到 0.4.7 之後那層 shim 可以不裝。

### 共同詞個數門檻（0.4.8 修正）

`strategies/undone/quantity_groups.py` 裡有三處門檻是「**共同詞個數**」（以空白或 `split_segment`
切開之後兩邊都有的詞數），不是相似度比例：

| 類別 | 判斷 | score |
|---|---|---|
| `NumberJaccardStrategy` | 共同詞數 ≥ `standard` | Jaccard 比例 |
| `FourJaccardRapidFuzzyScoreStrategy` | 共同詞數 ≥ `standard` | RapidFuzz ratio / 100 |
| `NewJACCARDStrategy`（`strategy_mode="amount_mode"`） | 共同詞數 ≥ `standard` | 共同詞數 |

0.4.7 以前這幾處寫 `int(standard)`：傳 `0.75` 會被截成 `0`，`共同詞數 >= 0` 永遠成立 → 每一對都命中。
0.4.8 起**非整數的門檻在建構時直接 `ValueError`**（`0.75`、`4.5`、`"0.75"`、`None`、`"abc"`、NaN、inf），
整數值照收並轉成 `int`（`4`、`4.0`、`"4"`、`"4.0"` 都當 4）：

```python
from isd_str_sdk.str_matching.strategies.undone.quantity_groups import FourJaccardRapidFuzzyScoreStrategy

FourJaccardRapidFuzzyScoreStrategy("a", "b", standard=4)     # OK：至少 4 個共同詞
FourJaccardRapidFuzzyScoreStrategy("a", "b", standard=0.75)  # ValueError：這是共同詞個數，0.75 是設定寫錯
```

* `NewJACCARDStrategy` 的 `score_mode` 門檻是相似度比例，**不受影響**；`amount_mode` 的 `None` / `""`
  維持舊行為（門檻 0）。
* `NumberJaccardStrategy` / `FourJaccardRapidFuzzyScoreStrategy` 不在 `STRATEGY_TABLE` 裡，要用類別本身
  （`MatchingStrategyAdapter(FourJaccardRapidFuzzyScoreStrategy, 4)`）。
* 下游原本傳 `0.75` 的設定，升到 0.4.8 會在建構時報錯——那份設定要改成整數的共同詞個數。
