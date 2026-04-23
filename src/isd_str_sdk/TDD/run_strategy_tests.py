from typing import Literal
import pandas as pd

from legacy.EntireCompareTree.contexts import TwoSeriesComparisonContextWithStrategyPars


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
WHITE = "\033[97m"
PURPLE = "\033[95m"
RESET = "\033[0m"
BOLD = "\033[1m"

def run_strategy_test(
        strategy_class, tests,
        print_mode: Literal["show_all", "wrong_answer"],
        col1="a", col2="b",
        split_segment: str = " ； ", strategy_mode: str = "amount_mode", extra_debug_print: bool = False,
):
    """
        通用化策略測試器。

        Parameters
        ----------
        strategy_class : Type
            要測試的策略 class，例如 AbbrevExactMatchStrategy。

        tests : List[Tuple[str, str, bool]]
            測試資料，每筆是 (left_value, right_value, expected_bool)。

        print_mode : Literal["show_all", "wrong_answer", "none"]
            顯示模式：
                - "show_all"：全部顯示
                - "wrong_answer"：只顯示錯誤結果
                - "none"：完全不顯示

        col1, col2 : str
            傳給策略的欄位名稱。

        split_segment, strategy_mode, extra_debug_print
            會直接傳到 stra_pars。

        Returns
        -------
        results : List[bool]
            每筆測試 result.success 的結果，用於後續統計或自動化。
    """

    strategy = strategy_class(col1, col2)
    print(f"\n===== Testing {strategy_class.__name__} =====")

    results = []
    for left, right, expected in tests:
        ctx = TwoSeriesComparisonContextWithStrategyPars(
            row1=pd.Series({col1: left}),
            row2=pd.Series({col2: right}),
            stra_pars={
                "split_segment": split_segment,
                "strategy_mode": strategy_mode,
                "extra_debug_print": extra_debug_print,
            },
        )

        result = strategy.evaluate(ctx)
        success = result.success
        correctness = (success == expected)
        results.append(correctness)

        show = print_mode == "show_all" or (print_mode == "wrong_answer" and not correctness)
        if show:
            mark = f"{GREEN}✓{RESET}" if correctness else f"{RED}✗{RESET}"

            print(
                f"{mark} {BOLD}{left!r}{RESET} {PURPLE}vs{RESET} {BOLD}{right!r}{RESET} | "
                f"got: {YELLOW}{success}{RESET} | expected: {CYAN}{expected}{RESET}"
            )

    # summary
    total = len(results)
    passed = sum(results)
    failed = total - passed
    if failed == 0:
        print(f"{GREEN}ALL PASS! ({passed}/{total}){RESET}")
    else:
        print(f"{RED}Some tests failed ({failed}/{total}){RESET}")

    return results
