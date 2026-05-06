"""
test_tdd.py — Quick TDD smoke-test for both str_matching and str_cleaning.

Run directly:
    python tests/test_tdd.py

Or via the top-level import shortcut:
    from isd_str_sdk import run_matching_test, run_cleaning_test
"""

from isd_str_sdk import run_matching_test, run_cleaning_test
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy
from isd_str_sdk.str_cleaning.strategies.base_str_processors import (
    StrFunc_Lowercase,
    StrFunc_NormalizeWhitespace,
)

# ── Matching TDD ──────────────────────────────────────────────────────────────
run_matching_test(FuzzyRatioStrategy, [
    ("ABC", "ABC Inc.", True),
    ("ABC", "XYZ", False),
], print_mode="show_all", standard=0.5)

# ── Cleaning TDD ──────────────────────────────────────────────────────────────
run_cleaning_test(StrFunc_Lowercase, [
    ("HELLO WORLD", "hello world"),
    ("abc", "abc"),
], print_mode="show_all")

run_cleaning_test(StrFunc_NormalizeWhitespace, [
    ("  Hello   World  ", "Hello World"),
    ("already clean", "already clean"),
], print_mode="show_all")

