from typing import Literal

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
PURPLE = "\033[95m"

def run_str_processor_test(
    processor_class,
    tests,
    print_mode: Literal["show_all", "wrong_answer", "none"] = "show_all",
):
    """
    單一字串處理器 unit test runner

    tests: List[Tuple[input_str, expected_str]]
    """

    print(f"\n===== Testing {processor_class.__name__} =====")

    results = []

    for input_str, expected in tests:
        output = processor_class(input_str)._handle()
        correct = (output == expected)
        results.append(correct)

        show = (
            print_mode == "show_all"
            or (print_mode == "wrong_answer" and not correct)
        )

        if show:
            mark = f"{GREEN}✓{RESET}" if correct else f"{RED}✗{RESET}"

            print(
                f"{mark} {BOLD}IN :{RESET} {input_str!r}\n"
                f"    {PURPLE}OUT:{RESET} {YELLOW}{output!r}{RESET}\n"
                f"    {PURPLE}EXP:{RESET} {CYAN}{expected!r}{RESET}\n"
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
