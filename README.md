# ISD String Comparing Toolkit

A lightweight Python library providing robust string cleaning and matching strategies used across ISD projects. It supplies:

- composable string cleaning processors (normalization, trimming, symbol handling, domain mappings)
- matching strategies (exact, fuzzy, Levenshtein, Jaro‑Winkler, and hybrid/preprocessed matchers)
- a small TDD harness to iterate new strategy implementations

Requirements
- Python >= 3.11
- See `pyproject.toml` for pinned runtime dependencies: `rapidfuzz`, `regex`, `python-dotenv`, `pandas`.

Installation

```bash
pip install .
# or editable install for development
pip install -e .
```

Quick reference (modules)
- `isd_str_sdk.str_cleaning` — cleaning processors and adapters
- `isd_str_sdk.str_matching` — matching strategy implementations
- `isd_str_sdk.base` — abstract base classes (Strategy, StrProcessor)
- `isd_str_sdk.core` — comparison contexts (e.g. `TwoSeriesComparisonContext`)
- `isd_str_sdk.utils` — helpers (decorators, adapters, exceptions)
- `isd_str_sdk.TDD` — small harness to run strategy unit-like tests

Cleaning strategies (overview)

The cleaning subsystem exposes many small, composable processors. Two main patterns are provided:

- No-parameter processors (callable via `CleaningStrategyAdapter` using the name key)
- Parameterized processors (classes in `strategies/param_str_processors.py`)

Common no-parameter processors (name -> effect)

| Name | Effect |
|---|---|
| `StrFuncNoop` | no-op, returns input unchanged |
| `StrFunc_Lowercase` | lowercase all ASCII letters |
| `StrFunc_Uppercase` | uppercase all ASCII letters |
| `StrFunc_NormalizeWhitespace` | normalize repeated whitespace and trim |
| `StrFunc_NormalizeUnicodeSpacing` | normalize Unicode spacing classes |
| `StrFunc_RemoveHtmlTags` | remove simple HTML tags |
| `StrFunc_KeepEnglishLetterAndDigits` | keep only ASCII letters & digits |
| `StrFunc_AscendDictionaryOrder` / `StrFunc_DescendDictionaryOrder` | sort tokens lexicographically |

Parameterized processors (examples)

| Name | Parameters | Effect |
|---|---:|---|
| `StrFuncWithPars_RemoveSpecificSymbol` | list of symbols to remove | remove each specified symbol |
| `StrFunc_ReplaceInputToSomething` | list of (old, new) tuples | replace occurrences accordingly |
| `StrFuncWithPars_CaseConvert` | `'upper'` / `'lower'` | convert case per argument |

Using cleaning processors

High-level adapter (simple single-step call):

```py
from isd_str_sdk.str_cleaning import CleaningStrategyAdapter

cleaner = CleaningStrategyAdapter("StrFunc_NormalizeWhitespace")
cleaned = cleaner.run("  Hello   WORLD  \n")
print(cleaned)  # -> 'Hello WORLD'
```

Composing a chain of processors:

```py
from isd_str_sdk.base.StrProcessorsChain import StrProcessorsChain
from isd_str_sdk.str_cleaning.strategies.base_str_processors import StrFunc_Lowercase, StrFunc_NormalizeWhitespace

chain = StrProcessorsChain([StrFunc_Lowercase, StrFunc_NormalizeWhitespace])
out = chain.run("  HELLO   World  ")
print(out)  # lowercase then normalize whitespace
```

Matching strategies (overview)

Core implementations live under `str_matching/strategies`.

| Strategy | Purpose |
|---|---|
| `ExactMatchStrategy` | strict equality between two values |
| `FuzzyRatioStrategy` | RapidFuzz ratio → normalized 0.0–1.0 |
| `LevenshteinStrategy` | normalized Levenshtein similarity (0.0–1.0) |
| `JaroWinklerStrategy` | Jaro‑Winkler normalized similarity |
| `PreprocessedExactMatchStrategy` | normalize both values through a `StrProcessorsChain` then exact match |

Basic matcher usage

Strategies follow the `Strategy` interface: instantiate with column names (or keys) and a threshold, then call `.evaluate(context)` where `context` is a `TwoSeriesComparisonContext` containing two pandas Series (row1/row2).

```py
import pandas as pd
from isd_str_sdk.core.contexts import TwoSeriesComparisonContext
from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy

ctx = TwoSeriesComparisonContext(row1=pd.Series({'a': 'MIT'}), row2=pd.Series({'b': 'M.I.T.'}))
strategy = FuzzyRatioStrategy('a', 'b', standard=0.8)
result = strategy.evaluate(ctx)
print(result.success, result.score)  # bool, float
```

Example: preprocessed exact match

```py
from isd_str_sdk.str_matching.strategies.hybrid_matching import PreprocessedExactMatchStrategy
strategy = PreprocessedExactMatchStrategy('a', 'b', standard=True)
result = strategy.evaluate(ctx)
```

TDD harness (develop new strategies)

The `isd_str_sdk.TDD.run_strategy_tests` function provides a small harness for iterating new strategy implementations. It accepts a strategy class and a list of test tuples (left, right, expected_bool) and prints a colored summary.

Quick example (in `src/isd_str_sdk/TDD/run_strategy_tests.py`):

```py
from isd_str_sdk.TDD.run_strategy_tests import run_strategy_test
from myproject.strategies.my_new_strategy import MyStrategyClass

tests = [
		("MIT", "M.I.T.", True),
		("Apple", "Apple Inc.", False),
]
run_strategy_test(MyStrategyClass, tests, print_mode="wrong_answer")
```

Developer notes — architecture & conventions

- `isd_str_sdk.base` contains the abstract contracts you must implement:
	- `Strategy` / `StrategyResult` — matching algorithms should subclass `Strategy` and implement `evaluate(context)` returning `StrategyResult`.
	- `IStrProcessor` / `StrProcessorBase` / `StrProcessorWithParamBase` — cleaning processors implement `_handle()` (or `_handle(...)` for param processors) and expose `get_result()`.
- `isd_str_sdk.core.contexts` defines dataclass context objects used by strategies (`TwoSeriesComparisonContext`, `TwoSeriesComparisonContextWithStrategyPars`). Use these to pass rows and config to `evaluate()`.
- `isd_str_sdk.utils` contains small helpers:
	- `decorators` for runtime type checks on processors
	- `exceptions` for consistent error types
	- `adapters` for wrapping strategy outputs in UI-friendly formats

Recommended workflow for adding a new matcher
1. Implement the algorithm as a subclass of `Strategy` in `str_matching/strategies`.
2. Write unit-like tests using the TDD harness (`TDD/run_strategy_tests.py`).
3. If the algorithm needs preprocessing, either reuse `StrProcessorsChain` or implement a processor and register it in cleaning strategy tables.
4. Keep docstrings that explain parameters and expected context (the codebase has many in-line examples to follow).

High-level language features used
- `dataclasses` for lightweight context containers
- `typing` (generics, Literal, List, Dict) for clearer APIs
- small custom decorators for runtime enforcement of processor arguments
- `rapidfuzz` for fast fuzzy matching
- `regex` (the `regex` package) for Unicode-aware patterns
- `pandas.Series` to represent rows passed to strategies

If you want, I can:
- Add targeted usage examples for a specific strategy (pick one from cleaning or matching).
- Generate unit tests for one of the matching strategies using the TDD harness.
- Produce a developer guide that explains how to register new cleaning processors into `NOPARS_STRATEGY_TABLE` / `STRATEGY_TABLE`.

---
Authors: 周暘恩, Anthony Chou — MIT License
