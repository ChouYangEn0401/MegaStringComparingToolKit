from isd_str_sdk.str_matching.adapters import *
from isd_str_sdk.TDD.run_strategy_tests import run_strategy_test, run_str_processor_test

# 比對兩欄位是否匹配的策略
run_strategy_test(FuzzyRatioStrategy, [
    ("ABC", "ABC Inc.", True),
    ("ABC", "XYZ", False),
], print_mode="wrong_answer")

# 單一字串處理器
run_str_processor_test(AbbrevExactMatchStrategy, [
    ("Hello  World", "Hello World"),
    ("  abc  ", "abc"),
], print_mode="show_all")
