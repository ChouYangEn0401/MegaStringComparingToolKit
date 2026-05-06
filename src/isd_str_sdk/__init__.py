"""
isd_str_sdk — ISD String Processing & Comparison Toolkit
=========================================================

Quick start
-----------
>>> import isd_str_sdk as sdk

# Matching — Level 1 (two lists, find best match):
>>> sdk.match(["MIT"], ["M.I.T."], strategy="FUZZY", threshold=0.5)

# Matching — Level 2 (single pair):
>>> sdk.MatchingStrategyAdapter("FUZZY", standard=0.5).run("MIT", "M.I.T.")

# Cleaning:
>>> sdk.CleaningStrategyAdapter("StrFunc_NormalizeWhitespace").run("  hello  ")

# Chain multiple cleaning steps:
>>> chain = sdk.StrProcessorsChain([...])

# TDD helpers:
>>> sdk.run_matching_test(MyStrategy, [("a", "a", True), ("a", "b", False)])
>>> sdk.run_cleaning_test(StrFunc_Lowercase, [("HELLO", "hello")])
"""

from isd_str_sdk.str_matching import match, MatchingStrategyAdapter
from isd_str_sdk.str_matching.adapters import STRATEGY_TABLE as MATCHING_STRATEGY_TABLE
from isd_str_sdk.str_cleaning import CleaningStrategyAdapter, NOPARS_STRATEGY_TABLE as CLEANING_STRATEGY_TABLE
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.TDD import run_matching_test, run_cleaning_test

__all__ = [
    # Matching
    "match",
    "MatchingStrategyAdapter",
    "MATCHING_STRATEGY_TABLE",
    # Cleaning
    "CleaningStrategyAdapter",
    "CLEANING_STRATEGY_TABLE",
    "StrProcessorsChain",
    # TDD
    "run_matching_test",
    "run_cleaning_test",
]
