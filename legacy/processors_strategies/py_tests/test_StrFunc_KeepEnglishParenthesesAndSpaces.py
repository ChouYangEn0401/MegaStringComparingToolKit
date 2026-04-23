from src.lib.processors_strategies.cleaning_module.str_processors import StrFunc_KeepEnglishParenthesesAndSpaces
from src.lib.processors_strategies.py_tests.run_strategy_tests import run_str_processor_test

TESTS = [
    ("N><_=ational %@#@Taiwan U@$nive^@rsity (NTU)", "National Taiwan University (NTU)",),
    ("<N>ati_on=al Ta%@iw#an@ U@$nive^@rsity (NTU)", "National Taiwan University (NTU)",),
]

run_str_processor_test(
    StrFunc_KeepEnglishParenthesesAndSpaces,
    TESTS,
    "show_all",
)
