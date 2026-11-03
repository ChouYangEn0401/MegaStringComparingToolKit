"""
Regex 比對策略（0.4.9）
======================

以前 regex 在這個套件裡只出現在清理步驟內部（「只留英數」之類寫死的樣式）。
這一組把 regex 變成**使用者可以設定的比對規則**，四種用法各一款：

==============================  =========================================================
``RegexExtractExactStrategy``   兩邊各用 regex **擷取**一段（年份、DOI、ISSN、代碼…）再比
``RegexRuleStrategy``           一欄放 **regex 規則**、另一欄放文字：規則比得中文字就算中
``RegexNamedGroupsStrategy``    用具名群組把字串**拆成欄位**，逐欄比、給「幾成欄位相同」的分數
``RegexNormalizedExactStrategy`` 一張 **(樣式 → 取代)** 規則表套到兩邊，再完全比對
==============================  =========================================================

共同點
------
* 參數可以直接當 keyword 給，也可以放 ``strategy_parameters``（GUI / JSON 走這條），見 ``_params.py``。
* ``ignore_case``：樣式比對不分大小寫，比較擷取出來的值時也不分大小寫（``casefold``）。
  樣式裡也可以用 inline flag，例如 ``(?i)``。
* 樣式在**建構時**就編譯，寫錯直接 ``ValueError``（訊息指出哪一條）——設定錯不該跑到一半才炸。
  例外是 ``RegexRuleStrategy``：它的樣式來自資料，壞掉的那一格只判不中，不讓整批停下來。
* 用的是 ``regex`` 套件（相容 ``re`` 語法，另支援 ``\\p{L}`` 這類 Unicode 類別與逾時）。
* 空值一律先過 ``NullPolicy``（預設任一側 null → ``success=False, score=-1.0``）。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import regex

from isd_str_sdk.base.AbstractStrategy import Strategy, StrategyResult
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching.null_policy import NullPolicy
from isd_str_sdk.str_matching.strategies._params import (
    get_param,
    threshold_or_one,
    to_bool,
    to_choice,
    to_name_list,
    to_optional_seconds,
)

_MATCH_MODES = ("search", "fullmatch", "match")


class _RegexStrategyBase(Strategy[TwoSeriesComparisonContext]):
    """欄位、NullPolicy、參數讀取、編譯與值正規化的共用部分。"""

    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        self.df1_col = df1
        self.df2_col = df2
        self.standard = standard
        self.null_policy = NullPolicy.from_kwargs(kwargs)
        self._kwargs = kwargs
        self.ignore_case = to_bool(self._param("ignore_case", False))

    # ── 參數 ──────────────────────────────────────────────────────────────
    def _param(self, name: str, default: Any = None) -> Any:
        return get_param(self._kwargs, name, default)

    def _required(self, name: str) -> Any:
        value = self._param(name)
        if value is None:
            raise ValueError(f"[{type(self).__name__}] 缺少必要參數 {name!r}")
        return value

    @property
    def _flags(self) -> int:
        return regex.IGNORECASE if self.ignore_case else 0

    def _compile(self, pattern: Any, what: str) -> "regex.Pattern":
        try:
            return regex.compile(str(pattern), self._flags)
        except regex.error as e:
            raise ValueError(f"[{type(self).__name__}] {what} 不是合法的 regex：{pattern!r}（{e}）") from e

    # ── 值 ────────────────────────────────────────────────────────────────
    def _texts(self, context: TwoSeriesComparisonContext) -> Tuple[Optional[StrategyResult], str, str]:
        raw1 = context.row1.get(self.df1_col)
        raw2 = context.row2.get(self.df2_col)
        handled = self.null_policy.intercept(raw1, raw2)
        if handled is not None:
            return handled, "", ""
        return None, NullPolicy.to_text(raw1), NullPolicy.to_text(raw2)

    def _norm(self, value: Optional[str]) -> Optional[str]:
        """擷取值的比較形式：去前後空白；``ignore_case`` 時 casefold；空字串 → None。"""
        if value is None:
            return None
        value = value.strip()
        if self.ignore_case:
            value = value.casefold()
        return value or None

    @staticmethod
    def _matcher(pattern: "regex.Pattern", mode: str):
        return {"search": pattern.search, "fullmatch": pattern.fullmatch, "match": pattern.match}[mode]


# ═══════════════════════════════════════════════════════════════════════════
# 1. 擷取後比對
# ═══════════════════════════════════════════════════════════════════════════

class RegexExtractExactStrategy(_RegexStrategyBase):
    r"""
    兩邊各用 regex 擷取一段，比擷取出來的東西（``"REGEX_EXTRACT_EXACT"``）。

    用在「整串不一樣，但裡面某一段相同就是同一筆」：引文裡的 DOI、地址裡的郵遞區號、
    題名尾巴的年份、``ISSN 1234-567X``……

    參數
    ----
    pattern : str（必填）
        擷取用的 regex。
    right_pattern : str, 選填
        右欄用不同的樣式（例如左邊是 ``doi:10.1/xyz``、右邊是 URL）；預設同 ``pattern``。
    group : int | str, 預設 0
        取哪一個群組：0 = 整段比中、1 = 第一個括號、或具名群組的名字。兩個樣式都要有這個群組。
    extract_mode : ``"first"`` | ``"all_list"`` | ``"all_set"``, 預設 ``"first"``
        * ``first``：各取第一個比中的，相同才算中（score 1 / 0）。
        * ``all_list``：各取全部比中的（依出現順序），整串清單相同才算中（score 1 / 0）。
        * ``all_set``：各取全部比中的當集合，score = Jaccard，``score >= standard`` 算中
          （``standard`` 不是數字時視為 1.0，即集合要完全相同）。
    ignore_case : bool, 預設 False

    擷取值會去前後空白，空字串不算擷取到。**任一邊什麼都沒擷取到 → ``success=False, score=0.0``**
    （兩邊都沒有也一樣：沒東西可以證明它們相同）。

    例::

        s = RegexExtractExactStrategy("a", "b", None, pattern=r"10\.\d{4,9}/\S+", ignore_case=True)
        # "Smith 2020, doi:10.1000/ABC.1"  vs  "https://doi.org/10.1000/abc.1"  → 中
    """

    _MODES = ("first", "all_list", "all_set")

    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        super().__init__(df1, df2, standard, **kwargs)
        owner = type(self).__name__
        self.pattern = self._compile(self._required("pattern"), "pattern")
        right = self._param("right_pattern")
        self.right_pattern = self.pattern if right is None else self._compile(right, "right_pattern")
        self.extract_mode = to_choice(self._param("extract_mode", "first"), self._MODES, "extract_mode", owner)
        self.group = self._resolve_group(self._param("group", 0))

    @property
    def IsExactMatch(self) -> bool:
        return self.extract_mode != "all_set"

    def _resolve_group(self, group: Any) -> Any:
        if isinstance(group, str) and group.strip().lstrip("-").isdigit():
            group = int(group.strip())
        elif isinstance(group, float) and group.is_integer():
            group = int(group)
        for which, pattern in (("pattern", self.pattern), ("right_pattern", self.right_pattern)):
            ok = (0 <= group <= pattern.groups) if isinstance(group, int) else (group in pattern.groupindex)
            if not ok:
                raise ValueError(f"[{type(self).__name__}] {which} 沒有群組 {group!r}")
        return group

    def extract(self, pattern: "regex.Pattern", text: str) -> List[str]:
        """依 ``extract_mode`` 擷取（first 最多一個）；已正規化、去掉空值。"""
        if self.extract_mode == "first":
            for m in pattern.finditer(text):
                value = self._norm(m.group(self.group))
                if value is not None:
                    return [value]
            return []
        values = (self._norm(m.group(self.group)) for m in pattern.finditer(text))
        return [v for v in values if v is not None]

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        handled, text1, text2 = self._texts(context)
        if handled is not None:
            return handled
        got1 = self.extract(self.pattern, text1)
        got2 = self.extract(self.right_pattern, text2)
        if not got1 or not got2:
            return StrategyResult(success=False, score=0.0)
        if self.extract_mode == "all_set":
            set1, set2 = set(got1), set(got2)
            score = len(set1 & set2) / len(set1 | set2)
            return StrategyResult(success=score >= threshold_or_one(self.standard), score=score)
        flag = got1 == got2
        return StrategyResult(success=flag, score=1 if flag else 0)


# ═══════════════════════════════════════════════════════════════════════════
# 2. regex 樣式當規則
# ═══════════════════════════════════════════════════════════════════════════

class RegexRuleStrategy(_RegexStrategyBase):
    r"""
    一欄是 regex 規則、另一欄是文字：規則比得中文字就算中（``"REGEX_RULE"``）。

    權控表常見的形狀：右表每一列是一條規則（``^National Taiwan Univ(ersity)?\b``），
    左表是要歸類的原始字串。N×M 跑下去，就是「每一筆文字被哪幾條規則認領」。

    參數
    ----
    rule_side : ``"right"`` | ``"left"``, 預設 ``"right"``
        哪一欄放規則（``right`` = ``df2`` 那一欄）。
    match_mode : ``"search"`` | ``"fullmatch"`` | ``"match"``, 預設 ``"search"``
        ``search`` = 文字裡任何一處比中即可；``fullmatch`` = 要整串比中；``match`` = 從開頭比中。
    ignore_case : bool, 預設 False
    strip_rule : bool, 預設 True
        規則先去前後空白（Excel 儲存格尾巴多一個空白很常見；要比對空白請寫 ``\s`` 或 ``[ ]``）。
    regex_timeout : float 秒, 預設 1.0
        單一格的比對上限；規則來自資料，寫出災難性回溯的樣式（例如 ``(a|aa)+$``）時不會卡死整批。
        ``none`` / ``0`` = 不設上限。
    on_invalid : ``"fail"`` | ``"raise"``, 預設 ``"fail"``
        規則不是合法的 regex、或比對逾時：``fail`` = 那一格判不中（``success=False, score=-1.0``，
        跟 null 同一個分數，表示「沒辦法判」）；``raise`` = 直接丟 ``ValueError``。

    **空的規則一律不中**（空 regex 會比中所有字串，幾乎一定是資料漏填）——
    除非 NullPolicy 另有設定（例如 ``empty_is_null`` + ``match_if_both``）。
    編譯過的規則會快取，同一條規則不重複編譯。
    """

    _SIDES = ("right", "left")
    _ON_INVALID = ("fail", "raise")
    _CACHE_LIMIT = 50_000

    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        super().__init__(df1, df2, standard, **kwargs)
        owner = type(self).__name__
        self.rule_side = to_choice(self._param("rule_side", "right"), self._SIDES, "rule_side", owner)
        self.match_mode = to_choice(self._param("match_mode", "search"), _MATCH_MODES, "match_mode", owner)
        self.strip_rule = to_bool(self._param("strip_rule", True))
        self.regex_timeout = to_optional_seconds(self._param("regex_timeout", 1.0), "regex_timeout", owner)
        self.on_invalid = to_choice(self._param("on_invalid", "fail"), self._ON_INVALID, "on_invalid", owner)
        self._cache: Dict[str, Any] = {}

    @property
    def IsExactMatch(self) -> bool:
        return True

    def __getstate__(self):
        state = self.__dict__.copy()
        state["_cache"] = {}
        return state

    def _rule(self, text: str) -> Any:
        """編譯一條規則；不合法時回傳 ``regex.error``（也快取，不重複嘗試）。"""
        cached = self._cache.get(text)
        if cached is not None:
            return cached
        try:
            compiled: Any = regex.compile(text, self._flags)
        except regex.error as e:
            compiled = e
        if len(self._cache) >= self._CACHE_LIMIT:
            self._cache.clear()
        self._cache[text] = compiled
        return compiled

    def _invalid(self, rule: str, reason: str) -> StrategyResult:
        if self.on_invalid == "raise":
            raise ValueError(f"[{type(self).__name__}] 規則 {rule!r} {reason}")
        return StrategyResult(success=False, score=self.null_policy.null_score)

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        handled, text1, text2 = self._texts(context)
        if handled is not None:
            return handled
        rule, target = (text2, text1) if self.rule_side == "right" else (text1, text2)
        if self.strip_rule:
            rule = rule.strip()
        if rule == "":
            return StrategyResult(success=False, score=0.0)
        compiled = self._rule(rule)
        if isinstance(compiled, regex.error):
            return self._invalid(rule, f"不是合法的 regex（{compiled}）")
        try:
            hit = self._matcher(compiled, self.match_mode)(target, timeout=self.regex_timeout)
        except TimeoutError:
            return self._invalid(rule, f"比對超過 {self.regex_timeout} 秒")
        flag = hit is not None
        return StrategyResult(success=flag, score=1 if flag else 0)


# ═══════════════════════════════════════════════════════════════════════════
# 3. 具名群組逐欄比
# ═══════════════════════════════════════════════════════════════════════════

class RegexNamedGroupsStrategy(_RegexStrategyBase):
    r"""
    用具名群組把兩邊拆成欄位，逐欄比（``"REGEX_NAMED_GROUPS"``）。

    一欄裡其實塞了好幾個欄位時用它：``"2021 Vol 12(3) pp 45-67"``、
    ``"Dept Chem, Natl Taiwan Univ, Taipei 10617, Taiwan"``……
    樣式寫成 ``(?P<year>\d{4})\s+Vol\s*(?P<vol>\d+)\((?P<no>\d+)\)``，就能分別知道年、卷、期對不對得上。

    參數
    ----
    pattern : str（必填）
        至少要有一個具名群組。
    right_pattern : str, 選填
        右欄用不同的樣式（欄位名字要對得上）；預設同 ``pattern``。
    groups : str | list, 選填
        只比哪幾個群組（逗號分隔）；預設比兩個樣式共有的全部具名群組。
    match_mode : ``"search"`` | ``"fullmatch"`` | ``"match"``, 預設 ``"search"``
    ignore_case : bool, 預設 False

    計分
    ----
    * 任一邊整個樣式沒比中 → ``success=False, score=0.0``。
    * 每一個群組：值去前後空白後相同 → 相同；**兩邊都沒值（群組沒參與）→ 不列入計分**；
      只有一邊有值 → 不同。
    * ``score = 相同的群組數 / 列入計分的群組數``，``score >= standard`` 算中
      （``standard`` 不是數字時視為 1.0，即全部相同才中）。都沒有可計分的群組 → ``score=0.0``。
    * ``StrategyResult.children``：照 ``groups`` 的順序，每個群組一個 ``StrategyResult``
      （相同 1、不同 0、不列入計分 ``score=None``），報表可以直接看出是哪一欄對不上。
    """

    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        super().__init__(df1, df2, standard, **kwargs)
        owner = type(self).__name__
        self.pattern = self._compile(self._required("pattern"), "pattern")
        right = self._param("right_pattern")
        self.right_pattern = self.pattern if right is None else self._compile(right, "right_pattern")
        self.match_mode = to_choice(self._param("match_mode", "search"), _MATCH_MODES, "match_mode", owner)
        shared = [g for g in self.pattern.groupindex if g in self.right_pattern.groupindex]
        wanted = to_name_list(self._param("groups"))
        if wanted:
            missing = [g for g in wanted if g not in shared]
            if missing:
                raise ValueError(f"[{owner}] 樣式裡沒有（或左右不共有）這些具名群組：{missing}")
            self.groups: List[str] = wanted
        else:
            self.groups = shared
        if not self.groups:
            raise ValueError(f"[{owner}] pattern 至少要有一個具名群組，例如 (?P<year>\\d{{4}})")

    def fields(self, pattern: "regex.Pattern", text: str) -> Optional[Dict[str, Optional[str]]]:
        """拆出 ``groups`` 的值（已正規化）；整個樣式沒比中回 ``None``。"""
        m = self._matcher(pattern, self.match_mode)(text)
        if m is None:
            return None
        return {g: self._norm(m.group(g)) for g in self.groups}

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        handled, text1, text2 = self._texts(context)
        if handled is not None:
            return handled
        f1 = self.fields(self.pattern, text1)
        f2 = self.fields(self.right_pattern, text2)
        if f1 is None or f2 is None:
            return StrategyResult(success=False, score=0.0)
        children: List[StrategyResult] = []
        same = counted = 0
        for g in self.groups:
            v1, v2 = f1[g], f2[g]
            if v1 is None and v2 is None:
                children.append(StrategyResult(success=True, score=None))
                continue
            counted += 1
            eq = v1 == v2
            same += eq
            children.append(StrategyResult(success=eq, score=1 if eq else 0))
        if counted == 0:
            return StrategyResult(success=False, score=0.0, children=children)
        score = same / counted
        return StrategyResult(success=score >= threshold_or_one(self.standard), score=score, children=children)


# ═══════════════════════════════════════════════════════════════════════════
# 4. 正規化規則表後完全比對
# ═══════════════════════════════════════════════════════════════════════════

def _parse_rules(rules: Any, owner: str) -> List[Tuple[str, str]]:
    """
    規則表可以是：

    * ``[(pattern, replacement), ...]``（``replacement`` 省略 = 刪掉）
    * 字串，一行一條：``pattern => replacement``；沒有 ``=>`` 的那一行 = 刪掉；
      空行與 ``#`` 開頭的行略過。
    """
    parsed: List[Tuple[str, str]] = []
    if isinstance(rules, str):
        for line in rules.splitlines():
            if line.strip() == "" or line.lstrip().startswith("#"):
                continue
            if "=>" in line:
                pattern, replacement = line.split("=>", 1)
                parsed.append((pattern.strip(), replacement.strip()))
            else:
                parsed.append((line.strip(), ""))
        return parsed
    for i, rule in enumerate(rules):
        if isinstance(rule, str):
            parsed.append((rule, ""))
        elif isinstance(rule, Sequence) and 1 <= len(rule) <= 2:
            parsed.append((str(rule[0]), str(rule[1]) if len(rule) == 2 else ""))
        else:
            raise ValueError(f"[{owner}] 第 {i + 1} 條規則要是 (pattern, replacement)：{rule!r}")
    return parsed


class RegexNormalizedExactStrategy(_RegexStrategyBase):
    r"""
    把一張「樣式 → 取代」規則表依序套到兩邊，再完全比對（``"REGEX_NORMALIZED_EXACT"``）。

    內建清理步驟不夠用、又不想為一個專案寫一支新的清理函式時用它：縮寫展開
    （``\bUniv\b\.? => University``）、去掉不重要的前綴（``^Dept\.? of [^,]+,\s* =>``）、
    把 ``Taipei 10617`` 的郵遞區號拿掉……規則表本身就是設定，可以放 JSON 跟著工作流走。

    參數
    ----
    rules : list | str（必填）
        ``[(pattern, replacement), ...]``，或一行一條的字串 ``pattern => replacement``
        （沒有 ``=>`` = 刪掉；空行與 ``#`` 開頭略過）。``replacement`` 可以用 ``\1`` / ``\g<name>``。
        **依序**套用，前一條的結果是下一條的輸入。
    collapse_whitespace : bool, 預設 True
        全部套完之後，把連續空白縮成一個並去前後空白。
    ignore_case : bool, 預設 False
        樣式不分大小寫，最後比較也不分大小寫。

    score：相同 1、不同 0。``normalize(text)`` 可以單獨呼叫，看某個字串最後變成什麼。
    """

    def __init__(self, df1: str, df2: str, standard: Any, **kwargs):
        super().__init__(df1, df2, standard, **kwargs)
        owner = type(self).__name__
        rules = _parse_rules(self._required("rules"), owner)
        if not rules:
            raise ValueError(f"[{owner}] rules 是空的")
        self.rules: List[Tuple["regex.Pattern", str]] = [
            (self._compile(p, f"第 {i + 1} 條規則"), r) for i, (p, r) in enumerate(rules)
        ]
        self.collapse_whitespace = to_bool(self._param("collapse_whitespace", True))

    @property
    def IsExactMatch(self) -> bool:
        return True

    def normalize(self, text: str) -> str:
        for pattern, replacement in self.rules:
            text = pattern.sub(replacement, text)
        if self.collapse_whitespace:
            text = " ".join(text.split())
        return text.casefold() if self.ignore_case else text

    def evaluate(self, context: TwoSeriesComparisonContext) -> StrategyResult:
        handled, text1, text2 = self._texts(context)
        if handled is not None:
            return handled
        flag = self.normalize(text1) == self.normalize(text2)
        return StrategyResult(success=flag, score=1 if flag else 0)


__all__ = [
    "RegexExtractExactStrategy",
    "RegexRuleStrategy",
    "RegexNamedGroupsStrategy",
    "RegexNormalizedExactStrategy",
]
