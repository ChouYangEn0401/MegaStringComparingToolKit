"""
isd_str_sdk.matching_tools
==========================
Public API for string comparison / similarity functions.

Direct usage:
    from isd_str_sdk.matching_tools import fuzzy_compare
    score = fuzzy_compare("abc", "abd")

Dispatcher usage:
    from isd_str_sdk.matching_tools import matcher
    score = matcher("fuzzy_compare", "abc", "abd")
    score = matcher(fuzzy_compare, "abc", "abd")
"""

from __future__ import annotations

from typing import Callable, Union

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler, Levenshtein

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _lcs_length(a: str, b: str) -> int:
    """Compute the length of the Longest Common Subsequence of *a* and *b*."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
    return dp[m][n]


# ---------------------------------------------------------------------------
# Public comparison functions
# ---------------------------------------------------------------------------

def exact_match(a: str, b: str) -> bool:
    """Return ``True`` if *a* and *b* are identical."""
    return a == b


def lcs_similarity(a: str, b: str) -> float:
    """
    LCS-based similarity normalised by the length of the longer string.

    Returns a value in [0.0, 1.0].
    """
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 1.0
    return _lcs_length(a, b) / max_len


def jaccard_similarity(a: str, b: str) -> float:
    """
    Word-level Jaccard similarity.

    Returns a value in [0.0, 1.0].
    """
    set_a = set(a.split())
    set_b = set(b.split())
    union = len(set_a | set_b)
    if union == 0:
        return 1.0
    return len(set_a & set_b) / union


def fuzzy_compare(a: str, b: str) -> float:
    """
    Levenshtein-based fuzzy ratio (via rapidfuzz).

    Returns a value in [0.0, 1.0].
    """
    return fuzz.ratio(a, b) / 100.0


def fuzzy_partial_compare(a: str, b: str) -> float:
    """
    Partial fuzzy ratio — best alignment of the shorter string against the
    longer one (via rapidfuzz).

    Returns a value in [0.0, 1.0].
    """
    return fuzz.partial_ratio(a, b) / 100.0


def jaro_winkler_similarity(a: str, b: str) -> float:
    """
    Jaro-Winkler similarity (via rapidfuzz).

    Returns a value in [0.0, 1.0].
    """
    return JaroWinkler.normalized_similarity(a, b)


def levenshtein_similarity(a: str, b: str) -> float:
    """
    Normalised Levenshtein similarity (via rapidfuzz).

    Returns a value in [0.0, 1.0].
    """
    return Levenshtein.normalized_similarity(a, b)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

# Registry maps the public function name → the function object.
_MATCHING_REGISTRY: dict[str, Callable] = {
    "exact_match": exact_match,
    "lcs_similarity": lcs_similarity,
    "jaccard_similarity": jaccard_similarity,
    "fuzzy_compare": fuzzy_compare,
    "fuzzy_partial_compare": fuzzy_partial_compare,
    "jaro_winkler_similarity": jaro_winkler_similarity,
    "levenshtein_similarity": levenshtein_similarity,
}


def matcher(
    fn: Union[str, Callable],
    a: str,
    b: str,
    /,
    **kwargs,
):
    """
    Dispatcher for matching functions.

    Parameters
    ----------
    fn:
        Either the *name* of a registered matching function (str) or the
        callable itself.
    a, b:
        The two strings to compare.
    **kwargs:
        Extra keyword arguments forwarded to *fn*.

    Returns
    -------
    The return value of the matching function (bool or float).

    Examples
    --------
    >>> matcher("fuzzy_compare", "abc", "abd")
    0.8
    >>> matcher(fuzzy_compare, "abc", "abd")
    0.8
    """
    if isinstance(fn, str):
        if fn not in _MATCHING_REGISTRY:
            raise KeyError(
                f"Unknown matching function {fn!r}. "
                f"Available: {sorted(_MATCHING_REGISTRY)}"
            )
        fn = _MATCHING_REGISTRY[fn]

    if not callable(fn):
        raise TypeError(f"fn must be a str or callable, got {type(fn).__name__!r}")

    return fn(a, b, **kwargs)


# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

__all__ = [
    "exact_match",
    "lcs_similarity",
    "jaccard_similarity",
    "fuzzy_compare",
    "fuzzy_partial_compare",
    "jaro_winkler_similarity",
    "levenshtein_similarity",
    "matcher",
]
