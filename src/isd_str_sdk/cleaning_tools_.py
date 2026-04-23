"""
isd_str_sdk.cleaning_tools
==========================
Public API for string cleaning / normalisation functions.

Each function is a plain callable that accepts a string and returns a string.
No class boilerplate — the legacy Strategy-pattern classes live on in
``isd_str_compare.legacy`` and are untouched.

Direct usage:
    from isd_str_sdk.cleaning_tools import lowercase, normalize_whitespace
    s = lowercase("MIT University")
    s = normalize_whitespace("  hello   world  ")

Dispatcher usage:
    from isd_str_sdk.cleaning_tools import cleaner
    s = cleaner("lowercase", "MIT University")
    s = cleaner(lowercase, "MIT University")
"""

from __future__ import annotations

import re
import string
from typing import Callable, Union

import regex  # third-party; handles Unicode property classes (\p{Z} etc.)

# ---------------------------------------------------------------------------
# Case conversion
# ---------------------------------------------------------------------------

def lowercase(s: str) -> str:
    """Convert *s* to lower case."""
    return s.lower()


def uppercase(s: str) -> str:
    """Convert *s* to upper case."""
    return s.upper()


def capitalize_sentence(s: str) -> str:
    """Capitalise the first character of *s* (all others unchanged)."""
    return s.capitalize()


def capitalize_words(s: str) -> str:
    """Capitalise the first character of every whitespace-separated word."""
    return " ".join(word.capitalize() for word in s.split(" "))


# ---------------------------------------------------------------------------
# Keep / filter characters
# ---------------------------------------------------------------------------

def keep_english_letters(s: str) -> str:
    """Keep only ASCII letters (a-z, A-Z)."""
    return "".join(re.findall(r"[a-zA-Z]+", s))


def keep_english_words_and_spaces(s: str) -> str:
    """Keep ASCII letters and spaces."""
    return "".join(re.findall(r"[a-zA-Z ]+", s))


def keep_digits(s: str) -> str:
    """Keep only digit characters (0-9)."""
    return "".join(re.findall(r"\d+", s))


def keep_english_letters_and_digits(s: str) -> str:
    """Keep only ASCII letters and digits."""
    return "".join(re.findall(r"[a-zA-Z0-9]+", s))


def keep_english_parentheses_and_spaces(s: str) -> str:
    """Keep only ASCII letters, parentheses ``()`` and spaces."""
    return "".join(re.findall(r"[a-zA-Z() ]+", s))


# ---------------------------------------------------------------------------
# Symbol removal
# ---------------------------------------------------------------------------

def remove_all_symbols(s: str) -> str:
    """Remove all non-alphanumeric characters (underscores included)."""
    return "".join(re.findall(r"\w+", s)).replace("_", "")


def remove_specific_symbols(s: str, symbols: list[str]) -> str:
    """
    Remove all characters listed in *symbols* from *s*.

    Example
    -------
    >>> remove_specific_symbols("hello!", ["!"])
    'hello'
    """
    symbols_set = set(str(sym) for sym in symbols)
    return "".join(ch for ch in s if ch not in symbols_set)


def remove_html_tags(s: str) -> str:
    """Strip HTML/XML tags from *s*."""
    return re.sub(r"</?[^>]+>", "", s)


def clean_escaped_symbols(s: str) -> str:
    """
    Unescape common escape sequences and remove bare quote characters.

    Handles: ``\\'``, ``\\"``, ``\\\\``, bare ``"`` and ``'``.
    """
    text = s
    text = text.replace("\\'", "'")
    text = text.replace('\\"', '"')
    text = text.replace("\\\\", "\\")
    text = text.replace('"', "")
    text = text.replace("'", "")
    return text


# ---------------------------------------------------------------------------
# Replacement helpers
# ---------------------------------------------------------------------------

def remove_substrings(s: str, substrings: list[str]) -> str:
    """
    Delete every string in *substrings* from *s*.

    Example
    -------
    >>> remove_substrings("hello world", ["world"])
    'hello '
    """
    result = s
    for sub in substrings:
        result = result.replace(sub, "")
    return result


def replace_substrings(s: str, replacements: list[tuple[str, str]]) -> str:
    """
    Apply a sequence of ``(old, new)`` replacement pairs to *s*.

    Example
    -------
    >>> replace_substrings("hello world", [("world", "there")])
    'hello there'
    """
    result = s
    for old, new in replacements:
        result = result.replace(old, new)
    return result


# ---------------------------------------------------------------------------
# Whitespace & spacing normalisation
# ---------------------------------------------------------------------------

def strip(s: str) -> str:
    """Strip leading and trailing whitespace from *s*."""
    return s.strip()


def normalize_spacing(s: str) -> str:
    """Collapse any run of whitespace characters to a single space."""
    return re.sub(r"\s+", " ", s)


def normalize_unicode_spacing(s: str) -> str:
    """
    Collapse all Unicode spacing / control / format characters to a single
    ASCII space (uses ``regex`` for Unicode property support).
    """
    return regex.sub(r"[\p{Z}\p{Cc}\p{Cf}]+", " ", s)


def normalize_whitespace(s: str) -> str:
    """
    Collapse all Unicode whitespace, tab, newline, and control characters to a
    single space, then strip leading/trailing whitespace.
    """
    return regex.sub(r"[\p{Z}\s\p{Cc}]+", " ", s).strip()


# ---------------------------------------------------------------------------
# Parentheses normalisation
# ---------------------------------------------------------------------------

_OPEN_PARENS = set("(（[［{｛<＜")
_CLOSE_PARENS = set(")）]］}｝>＞")


def normalize_parentheses(s: str) -> str:
    """
    Normalise all bracket variants to ASCII ``(`` / ``)``.

    Full-width, square, curly, and angle brackets are all converted.
    """
    result: list[str] = []
    for ch in s:
        if ch in _OPEN_PARENS:
            result.append("(")
        elif ch in _CLOSE_PARENS:
            result.append(")")
        else:
            result.append(ch)
    return "".join(result)


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def sort_words_ascending(s: str) -> str:
    """Sort whitespace-separated words in *s* in ascending lexicographic order."""
    return " ".join(sorted(s.split()))


def sort_words_descending(s: str) -> str:
    """Sort whitespace-separated words in *s* in descending lexicographic order."""
    return " ".join(sorted(s.split(), reverse=True))


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_CLEANING_REGISTRY: dict[str, Callable] = {
    "lowercase": lowercase,
    "uppercase": uppercase,
    "capitalize_sentence": capitalize_sentence,
    "capitalize_words": capitalize_words,
    "keep_english_letters": keep_english_letters,
    "keep_english_words_and_spaces": keep_english_words_and_spaces,
    "keep_digits": keep_digits,
    "keep_english_letters_and_digits": keep_english_letters_and_digits,
    "keep_english_parentheses_and_spaces": keep_english_parentheses_and_spaces,
    "remove_all_symbols": remove_all_symbols,
    "remove_specific_symbols": remove_specific_symbols,
    "remove_html_tags": remove_html_tags,
    "clean_escaped_symbols": clean_escaped_symbols,
    "remove_substrings": remove_substrings,
    "replace_substrings": replace_substrings,
    "strip": strip,
    "normalize_spacing": normalize_spacing,
    "normalize_unicode_spacing": normalize_unicode_spacing,
    "normalize_whitespace": normalize_whitespace,
    "normalize_parentheses": normalize_parentheses,
    "sort_words_ascending": sort_words_ascending,
    "sort_words_descending": sort_words_descending,
}


def cleaner(
    fn: Union[str, Callable],
    s: str,
    /,
    *args,
    **kwargs,
) -> str:
    """
    Dispatcher for cleaning functions.

    Parameters
    ----------
    fn:
        Either the *name* of a registered cleaning function (str) or the
        callable itself.
    s:
        The input string to process.
    *args, **kwargs:
        Extra positional / keyword arguments forwarded to *fn* (needed for
        parameterised functions such as ``remove_specific_symbols``).

    Returns
    -------
    str — the cleaned string.

    Examples
    --------
    >>> cleaner("lowercase", "MIT University")
    'mit university'
    >>> cleaner(lowercase, "MIT University")
    'mit university'
    >>> cleaner("remove_specific_symbols", "hello!", ["!"])
    'hello'
    """
    if isinstance(fn, str):
        if fn not in _CLEANING_REGISTRY:
            raise KeyError(
                f"Unknown cleaning function {fn!r}. "
                f"Available: {sorted(_CLEANING_REGISTRY)}"
            )
        fn = _CLEANING_REGISTRY[fn]

    if not callable(fn):
        raise TypeError(f"fn must be a str or callable, got {type(fn).__name__!r}")

    return fn(s, *args, **kwargs)


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

__all__ = [
    # case
    "lowercase",
    "uppercase",
    "capitalize_sentence",
    "capitalize_words",
    # keep / filter
    "keep_english_letters",
    "keep_english_words_and_spaces",
    "keep_digits",
    "keep_english_letters_and_digits",
    "keep_english_parentheses_and_spaces",
    # removal
    "remove_all_symbols",
    "remove_specific_symbols",
    "remove_html_tags",
    "clean_escaped_symbols",
    "remove_substrings",
    "replace_substrings",
    # whitespace
    "strip",
    "normalize_spacing",
    "normalize_unicode_spacing",
    "normalize_whitespace",
    # structure
    "normalize_parentheses",
    # sorting
    "sort_words_ascending",
    "sort_words_descending",
    # dispatcher
    "cleaner",
]
