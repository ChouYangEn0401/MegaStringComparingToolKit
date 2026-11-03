"""
策略參數的小工具（0.4.9）。

新策略的參數有兩種給法，效果相同：

* 直接當建構子的 keyword：``RegexExtractExactStrategy("a", "b", None, pattern=r"\\d{4}")``
* 放在 ``strategy_parameters`` dict（GUI / JSON 設定走這條，值可以是字串）：
  ``RegexExtractExactStrategy("a", "b", None, strategy_parameters={"pattern": r"\\d{4}"})``

兩邊都有時 keyword 優先。``None`` 與空字串視為「沒給」，回到預設值。
"""
from __future__ import annotations

import math
from typing import Any, Iterable, List, Mapping, Optional

_MISSING = object()


def get_param(kwargs: Mapping[str, Any], name: str, default: Any = None) -> Any:
    """依序找 ``kwargs[name]`` → ``kwargs["strategy_parameters"][name]`` → ``default``。"""
    value = kwargs.get(name, _MISSING)
    if value is _MISSING or value is None or (isinstance(value, str) and value == ""):
        params = kwargs.get("strategy_parameters") or {}
        value = params.get(name, _MISSING) if isinstance(params, Mapping) else _MISSING
    if value is _MISSING or value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    return value


def to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("1", "true", "t", "yes", "y", "on")


def to_choice(value: Any, options: Iterable[str], name: str, owner: str) -> str:
    options = list(options)
    text = str(value).strip().lower()
    if text not in options:
        raise ValueError(f"[{owner}] {name}={value!r} 不是可用的選項；可用：{options}")
    return text


def to_int(value: Any, name: str, owner: str, minimum: Optional[int] = None) -> int:
    """整數參數：``4`` / ``4.0`` / ``"4"`` 都收，``4.5`` / ``"abc"`` 直接 ValueError（不截斷）。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"[{owner}] {name}={value!r} 必須是整數") from None
    if not math.isfinite(number) or number != int(number):
        raise ValueError(f"[{owner}] {name}={value!r} 必須是整數")
    result = int(number)
    if minimum is not None and result < minimum:
        raise ValueError(f"[{owner}] {name}={value!r} 不可小於 {minimum}")
    return result


def to_optional_seconds(value: Any, name: str, owner: str) -> Optional[float]:
    """秒數；``None`` / ``"none"`` / ``0`` / 負數 = 不設上限。"""
    if value is None or (isinstance(value, str) and value.strip().lower() in ("", "none", "off")):
        return None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"[{owner}] {name}={value!r} 必須是秒數") from None
    if not math.isfinite(seconds) or seconds <= 0:
        return None
    return seconds


def to_name_list(value: Any) -> List[str]:
    """``"a, b"`` 或 ``["a", "b"]`` → ``["a", "b"]``（去空白、去空項、保留順序）。"""
    if value is None:
        return []
    items = value.split(",") if isinstance(value, str) else list(value)
    return [str(x).strip() for x in items if str(x).strip() != ""]


def threshold_or_one(standard: Any) -> float:
    """``standard`` 是有限數字就用它，否則（``None`` 等）視為 1.0（要全中）。"""
    if isinstance(standard, bool):
        return 1.0
    try:
        number = float(standard)
    except (TypeError, ValueError):
        return 1.0
    return number if math.isfinite(number) else 1.0
