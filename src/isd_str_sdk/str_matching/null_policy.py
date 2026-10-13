"""
Null / 空值處理策略（NullPolicy）
================================

所有「兩欄字串比對」策略在真正算分之前，都會先經過同一個 NullPolicy。
它回答一個很瑣碎、但每個資料集都會遇到的問題：

    「一邊（或兩邊）是空的，到底算不算配對成功？」

背景
----
pandas 從 Excel / SQL 讀進來的空格是 ``float('nan')`` / ``pd.NA`` / ``NaT``，
**不是** ``None``。舊版策略只檢查 ``is None``，所以 NaN 會被 ``str()`` 成
``"nan"`` 這個字串進到 tokenizer，兩個空格就會以 1.0 的分數「成功配對」。
這就是 ACA 專案裡 ``FAULT`` hotfix 要修的假分數問題。

三種模式
--------
``NullMode.FAIL``（預設）
    任一側是 null → ``StrategyResult(success=False, score=null_score)``。
    「缺資料不該配對」，這是最保守、也是絕大多數權控比對想要的行為。

``NullMode.MATCH_IF_BOTH``
    兩側都是 null → ``success=True, score=1.0``；只有一側 null → 同 FAIL。
    對應「空白跟空白能不能比」的需求：可以，但只在兩邊都空時。

``NullMode.AS_TEXT``
    完全不攔截，把 null 轉成文字（``"nan"`` / ``"None"`` / ``"<NA>"``）照常比對。
    這是 0.4.5 以前的 legacy 行為，保留給需要逐字比對這些字面的情境。

什麼算 null？
------------
* 永遠算：``None``、``float('nan')``、``numpy.nan``、``pd.NA``、``pd.NaT``
* 可選（``empty_is_null=True``）：``""`` 與只有空白的字串
* 可選（``null_like={...}``）：strip + lower 後等於集合內任一字串的文字，
  例如 ``{"nan", "none", "null", "n/a", "-"}``。
  對應「``None`` 文字跟 ``None`` 文字能不能比」：預設能（它們只是字串），
  把 ``"none"`` 放進 ``null_like`` 之後就會被當 null 處理。

用法
----
直接建構::

    from isd_str_sdk.str_matching.null_policy import NullPolicy, NullMode
    s = WordLCSStrategy("a", "b", standard=0.9,
                        null_policy=NullPolicy(mode=NullMode.MATCH_IF_BOTH))

透過 config dict（GUI / JSON 設定走這條）::

    s = WordLCSStrategy("a", "b", standard=0.9, strategy_parameters={
        "null_mode": "match_if_both",
        "empty_is_null": True,
        "null_like": "nan, none, n/a",   # 逗號分隔字串或 list 都可以
    })

不給任何參數時就是 ``NullPolicy()``，即 ``FAIL`` 模式、空字串不算 null、
沒有 null_like 文字。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, FrozenSet, Iterable, Mapping, Optional

from isd_str_sdk.base.AbstractStrategy import StrategyResult


class NullMode(str, Enum):
    FAIL = "fail"
    MATCH_IF_BOTH = "match_if_both"
    AS_TEXT = "as_text"

    @classmethod
    def coerce(cls, value: "NullMode | str | None") -> "NullMode":
        if value is None or value == "":
            return cls.FAIL
        if isinstance(value, cls):
            return value
        try:
            return cls(str(value).strip().lower())
        except ValueError as e:
            raise ValueError(
                f"Unknown null_mode {value!r}; expected one of "
                f"{[m.value for m in cls]}"
            ) from e


def _is_missing_scalar(value: Any) -> bool:
    """None / NaN / pd.NA / NaT 判定，不依賴 pandas import（pandas 為可選）。"""
    if value is None:
        return True
    # float('nan') / numpy.float64('nan')
    if isinstance(value, float):
        return math.isnan(value)
    # pd.NA、pd.NaT、numpy.datetime64('NaT') 等：它們都把自己標成「missing」
    # 透過 pandas.isna 判斷最準，但避免硬依賴；用 duck-typing 兜底。
    try:  # pragma: no cover - 走到這裡代表有 pandas
        import pandas as pd  # noqa: WPS433
        result = pd.isna(value)
        # pd.isna 對 list/array 會回陣列，這裡只處理 scalar
        if isinstance(result, bool):
            return result
        try:
            return bool(result)  # numpy.bool_
        except (TypeError, ValueError):
            return False
    except Exception:  # pandas 不在、或 value 不是 scalar
        return False


@dataclass(frozen=True)
class NullPolicy:
    mode: NullMode = NullMode.FAIL
    empty_is_null: bool = False
    null_like: FrozenSet[str] = field(default_factory=frozenset)
    null_score: float = -1.0

    # ── construction helpers ────────────────────────────────────────────────
    PARAM_KEYS = ("null_mode", "empty_is_null", "null_like", "null_score")

    @classmethod
    def from_params(cls, params: Optional[Mapping[str, Any]]) -> "NullPolicy":
        """從 strategy_parameters 這類 dict 建構；不認識的 key 一律忽略。"""
        if not params:
            return cls()
        mode = NullMode.coerce(params.get("null_mode"))
        empty = _to_bool(params.get("empty_is_null", False))
        null_like = _to_token_set(params.get("null_like", ()))
        score = params.get("null_score", -1.0)
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = -1.0
        return cls(mode=mode, empty_is_null=empty, null_like=null_like, null_score=score)

    @classmethod
    def from_kwargs(cls, kwargs: Mapping[str, Any]) -> "NullPolicy":
        """
        策略建構子統一呼叫這個：

        * ``null_policy=NullPolicy(...)`` 直接給物件 → 原樣使用
        * 否則從 ``strategy_parameters`` dict 解析
        * 兩者皆無 → 預設 ``NullPolicy()``
        """
        explicit = kwargs.get("null_policy")
        if isinstance(explicit, NullPolicy):
            return explicit
        if explicit is not None:
            raise TypeError(f"null_policy must be a NullPolicy, got {type(explicit).__name__}")
        return cls.from_params(kwargs.get("strategy_parameters"))

    # ── core API ────────────────────────────────────────────────────────────
    def is_null(self, value: Any) -> bool:
        if _is_missing_scalar(value):
            return True
        if isinstance(value, str):
            text = value.strip()
            if self.empty_is_null and text == "":
                return True
            if self.null_like and text.lower() in self.null_like:
                return True
        return False

    def intercept(self, raw1: Any, raw2: Any) -> Optional[StrategyResult]:
        """
        在算分前呼叫。回傳 ``StrategyResult`` 代表「已決定，不要再算」，
        回傳 ``None`` 代表「兩邊都有值，請照常比對」。
        """
        if self.mode is NullMode.AS_TEXT:
            return None
        n1, n2 = self.is_null(raw1), self.is_null(raw2)
        if not n1 and not n2:
            return None
        if self.mode is NullMode.MATCH_IF_BOTH and n1 and n2:
            return StrategyResult(success=True, score=1.0)
        return StrategyResult(success=False, score=self.null_score)

    @staticmethod
    def to_text(value: Any) -> str:
        """統一的 null → 文字轉換（只在 AS_TEXT 或已確認非 null 時使用）。"""
        if value is None:
            return ""
        return str(value)

    # ── metadata for UIs ────────────────────────────────────────────────────
    @staticmethod
    def param_meta() -> dict:
        """
        與 ``adapters.STRATEGY_PARAM_META`` 同 schema，供 GUI 動態產生欄位。
        這些 key 對所有兩欄比對策略都適用。
        """
        return {
            "null_mode": {
                "mode": "select",
                "level": "optional",
                "options": [m.value for m in NullMode],
                "default": NullMode.FAIL.value,
                "type": "str",
                "label": "Null handling",
            },
            "empty_is_null": {
                "mode": "select",
                "level": "optional",
                "options": ["False", "True"],
                "default": False,
                "type": "bool",
                "label": "Treat empty string as null",
            },
            "null_like": {
                "mode": "input",
                "level": "optional",
                "default": "",
                "type": "str",
                "label": "Null-like texts (comma separated)",
            },
        }


# ── small coercion helpers ──────────────────────────────────────────────────
def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("1", "true", "yes", "on", "y")


def _to_token_set(value: Any) -> FrozenSet[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        items: Iterable[str] = value.split(",")
    else:
        items = value
    return frozenset(str(x).strip().lower() for x in items if str(x).strip() != "")


DEFAULT_NULL_POLICY = NullPolicy()

__all__ = ["NullMode", "NullPolicy", "DEFAULT_NULL_POLICY"]
