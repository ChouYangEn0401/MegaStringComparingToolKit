from typing import Literal
import pandas as pd

from isd_str_sdk.core.contexts import TwoSeriesComparisonContext


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
PURPLE = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _print_summary(results: list[bool]) -> None:
    total = len(results)
    passed = sum(results)
    failed = total - passed
    if failed == 0:
        print(f"{GREEN}ALL PASS! ({passed}/{total}){RESET}")
    else:
        print(f"{RED}Some tests failed ({failed}/{total}){RESET}")


def run_matching_test(
        strategy_class, tests,
        print_mode: Literal["show_all", "wrong_answer", "none"] = "show_all",
        col1: str = "a", col2: str = "b",
        standard: float = 0.5,
):
    """
    比對策略（str_matching）測試器。

    Parameters
    ----------
    strategy_class : Type
        要測試的比對策略 class，例如 FuzzyRatioStrategy。

    tests : List[Tuple[str, str, bool]]
        測試資料，每筆是 (left_value, right_value, expected_bool)。

    print_mode : Literal["show_all", "wrong_answer", "none"]
        顯示模式：
            - "show_all"：全部顯示
            - "wrong_answer"：只顯示錯誤結果
            - "none"：完全不顯示

    col1, col2 : str
        傳給策略的欄位名稱，預設 "a" / "b"。

    standard : float
        策略的門檻值，預設 0.5。

    Returns
    -------
    results : List[bool]
        每筆測試 result.success 是否符合預期，用於後續統計或自動化。

    Examples
    --------
    >>> from isd_str_sdk import run_matching_test
    >>> from isd_str_sdk.str_matching.strategies.fuzzy_matching import FuzzyRatioStrategy
    >>> run_matching_test(FuzzyRatioStrategy, [
    ...     ("MIT", "MIT", True),
    ...     ("Apple", "Orange", False),
    ... ])
    """

    strategy = strategy_class(col1, col2, standard=standard)
    print(f"\n===== Matching TDD: {strategy_class.__name__} (standard={standard}) =====")

    results = []
    for left, right, expected in tests:
        ctx = TwoSeriesComparisonContext(
            row1=pd.Series({col1: left}),
            row2=pd.Series({col2: right}),
        )

        result = strategy.evaluate(ctx)
        success = result.success
        score_str = f"{result.score:.4f}" if result.score is not None else "N/A"
        correctness = (success == expected)
        results.append(correctness)

        show = print_mode == "show_all" or (print_mode == "wrong_answer" and not correctness)
        if show:
            mark = f"{GREEN}✓{RESET}" if correctness else f"{RED}✗{RESET}"
            print(
                f"{mark} {BOLD}{left!r}{RESET} {PURPLE}vs{RESET} {BOLD}{right!r}{RESET} | "
                f"score: {YELLOW}{score_str}{RESET} | "
                f"got: {YELLOW}{success}{RESET} | expected: {CYAN}{expected}{RESET}"
            )

    _print_summary(results)
    return results


def run_cleaning_test(
        processor_class, tests,
        print_mode: Literal["show_all", "wrong_answer", "none"] = "show_all",
):
    """
    字串清理處理器（str_cleaning）測試器。

    Parameters
    ----------
    processor_class : Type
        要測試的字串處理器 class（繼承自 StrProcessorBase），
        例如 StrFunc_Lowercase。

    tests : List[Tuple[str, str]]
        測試資料，每筆是 (input_str, expected_str)。

    print_mode : Literal["show_all", "wrong_answer", "none"]
        顯示模式：
            - "show_all"：全部顯示
            - "wrong_answer"：只顯示錯誤結果
            - "none"：完全不顯示

    Returns
    -------
    results : List[bool]
        每筆測試輸出是否符合預期，用於後續統計或自動化。

    Examples
    --------
    >>> from isd_str_sdk import run_cleaning_test
    >>> from isd_str_sdk.str_cleaning.strategies.base_str_processors import StrFunc_Lowercase
    >>> run_cleaning_test(StrFunc_Lowercase, [
    ...     ("HELLO", "hello"),
    ...     ("  ABC  ", "  abc  "),
    ... ])
    """

    print(f"\n===== Cleaning TDD: {processor_class.__name__} =====")

    results = []
    for input_str, expected in tests:
        output = processor_class(input_str)._handle()
        correctness = (output == expected)
        results.append(correctness)

        show = print_mode == "show_all" or (print_mode == "wrong_answer" and not correctness)
        if show:
            mark = f"{GREEN}✓{RESET}" if correctness else f"{RED}✗{RESET}"
            print(
                f"{mark} {BOLD}IN :{RESET} {input_str!r}\n"
                f"    {PURPLE}OUT:{RESET} {YELLOW}{output!r}{RESET}\n"
                f"    {PURPLE}EXP:{RESET} {CYAN}{expected!r}{RESET}\n"
            )

    _print_summary(results)
    return results


# ── Backward-compatible aliases ───────────────────────────────────────────────
run_strategy_test     = run_matching_test
run_str_processor_test = run_cleaning_test
